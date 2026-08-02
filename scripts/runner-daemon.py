#!/usr/bin/env python3
"""Narrow host service that runs uploaded UCI engines inside rootless gVisor."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import selectors
import shutil
import signal
import socket
import socketserver
import stat
import subprocess
import threading
import time
from pathlib import Path

SOCKET_PATH = Path(os.getenv("RUNNER_SOCKET", "/run/chesspit-runner/runner.sock"))
BOT_DIR = Path(os.getenv("BOT_STORAGE_DIR", "/var/lib/chesspit/bots")).resolve()
CACHE_DIR = Path(os.getenv("RUNNER_CACHE_DIR", "/var/lib/chesspit-runner/cache"))
IMAGE = os.getenv("ENGINE_IMAGE", "localhost/chesspit-engine-runtime:latest")
RUN_IMAGE = IMAGE
RUNTIME = os.getenv("ENGINE_RUNTIME", "runsc")
MAX_ENGINES = int(os.getenv("MAX_CONCURRENT_ENGINES", "4"))
MAX_LINE = 64 * 1024
OUTPUT_WINDOW = 10.0
OUTPUT_WINDOW_BYTES = 4 * 1024 * 1024
PURPOSE_TIMEOUT = {"validate": 15, "live": 1800, "rated": 14400}
KEY_RE = re.compile(r"[A-Za-z0-9_-]{20,128}\Z")
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")
capacity = threading.BoundedSemaphore(MAX_ENGINES)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("chesspit.runner")


def send_json(sock: socket.socket, value: dict) -> None:
    sock.sendall(json.dumps(value, separators=(",", ":")).encode() + b"\n")


def read_header(sock: socket.socket) -> dict:
    value = bytearray()
    while not value.endswith(b"\n") and len(value) <= 4096:
        chunk = sock.recv(1)
        if not chunk:
            break
        value += chunk
    if not value.endswith(b"\n"):
        raise ValueError("invalid request")
    return json.loads(value)


def cached_engine(key: str, expected: str) -> Path:
    if not KEY_RE.fullmatch(key) or not SHA_RE.fullmatch(expected):
        raise ValueError("invalid engine identity")
    source = BOT_DIR / key
    try:
        descriptor = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        raise ValueError("invalid engine file") from exc
    CACHE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = CACHE_DIR / expected
    temporary = CACHE_DIR / f".{expected}-{os.getpid()}-{threading.get_ident()}"
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > 50 * 1024 * 1024:
            raise ValueError("invalid engine file")
        digest = hashlib.sha256()
        with os.fdopen(descriptor, "rb", closefd=False) as src, temporary.open("xb") as dst:
            while chunk := src.read(1024 * 1024):
                digest.update(chunk)
                dst.write(chunk)
            if digest.hexdigest() != expected:
                raise ValueError("engine digest mismatch")
            dst.flush()
            os.fsync(dst.fileno())
        if not target.exists():
            temporary.chmod(0o500)
            temporary.replace(target)
    finally:
        os.close(descriptor)
        temporary.unlink(missing_ok=True)
    return target


def command(engine: Path, purpose: str) -> list[str]:
    timeout = PURPOSE_TIMEOUT[purpose]
    args = ["podman", "run", "--rm", "-i", "--pull=never", "--runtime", RUNTIME,
            "--network=none", "--ipc=none", "--read-only", "--read-only-tmpfs=false",
            "--userns=keep-id:uid=65534,gid=65534", "--user=65534:65534",
            "--cap-drop=all", "--security-opt=no-new-privileges", "--pids-limit=64",
            "--memory=512m", "--memory-swap=512m", "--cpus=1", "--timeout", str(timeout),
            "--ulimit", "nofile=64:64", "--ulimit", "core=0:0", "--ulimit", "fsize=20971520:20971520",
            "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=16m", "-v", f"{engine}:/engine:ro,z",
            RUN_IMAGE]
    return args


def relay(client: socket.socket, proc: subprocess.Popen, deadline: float) -> None:
    selector = selectors.DefaultSelector()
    selector.register(client, selectors.EVENT_READ, "input")
    selector.register(proc.stdout, selectors.EVENT_READ, "output")
    window_start, window_bytes = time.monotonic(), 0
    current_line = 0
    while proc.poll() is None and time.monotonic() < deadline:
        for selected, _ in selector.select(timeout=.25):
            if selected.data == "input":
                data = client.recv(65536)
                if not data:
                    proc.stdin.close()
                    selector.unregister(client)
                else:
                    proc.stdin.write(data)
                    proc.stdin.flush()
            else:
                chunk = os.read(proc.stdout.fileno(), 65536)
                if not chunk:
                    selector.unregister(proc.stdout)
                    continue
                pieces = chunk.split(b"\n")
                if len(pieces) == 1:
                    current_line += len(chunk)
                else:
                    if current_line + len(pieces[0]) > MAX_LINE or any(len(piece) > MAX_LINE for piece in pieces[1:]):
                        raise RuntimeError("engine output line limit exceeded")
                    current_line = len(pieces[-1])
                if current_line > MAX_LINE:
                    raise RuntimeError("engine output line limit exceeded")
                now = time.monotonic()
                if now - window_start >= OUTPUT_WINDOW:
                    window_start, window_bytes = now, 0
                window_bytes += len(chunk)
                if window_bytes > OUTPUT_WINDOW_BYTES:
                    raise RuntimeError("engine output rate limit exceeded")
                client.sendall(chunk)
    if time.monotonic() >= deadline:
        raise RuntimeError("engine wall-clock limit exceeded")


class Handler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        proc = None
        acquired = False
        acknowledged = False
        try:
            request = read_header(self.request)
            if request.get("version") != 1:
                raise ValueError("unsupported runner protocol")
            if request.get("op") == "health":
                send_json(self.request, {"ok": True})
                return
            purpose = request.get("purpose")
            if purpose not in PURPOSE_TIMEOUT:
                raise ValueError("invalid engine purpose")
            acquired = capacity.acquire(blocking=False)
            if not acquired:
                send_json(self.request, {"ok": False, "error": "sandbox capacity exhausted"})
                return
            engine = cached_engine(str(request.get("key", "")), str(request.get("sha256", "")))
            proc = subprocess.Popen(command(engine, purpose), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL, bufsize=0, start_new_session=True)
            send_json(self.request, {"ok": True})
            acknowledged = True
            relay(self.request, proc, time.monotonic() + PURPOSE_TIMEOUT[purpose])
        except Exception:
            logger.exception("Sandbox request failed")
            if not acknowledged:
                try:
                    send_json(self.request, {"ok": False, "error": "sandbox request failed"})
                except OSError:
                    pass
        finally:
            if proc and proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait(timeout=5)
            if acquired:
                capacity.release()


class Server(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True


def preflight() -> None:
    global RUN_IMAGE
    BOT_DIR.mkdir(parents=True, exist_ok=True)
    SOCKET_PATH.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["podman", "info"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    result = subprocess.run(["podman", "image", "inspect", IMAGE, "--format", "{{.Id}}"], check=True,
                            capture_output=True, text=True, timeout=10)
    RUN_IMAGE = result.stdout.strip()
    if re.fullmatch(r"[0-9a-f]{64}", RUN_IMAGE):
        RUN_IMAGE = f"sha256:{RUN_IMAGE}"
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", RUN_IMAGE):
        raise RuntimeError("Could not pin the engine image by immutable ID")
    if RUNTIME != "runsc" and os.getenv("ALLOW_NON_GVISOR", "false").lower() != "true":
        raise RuntimeError("gVisor/runsc is required")
    CACHE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    selftest = CACHE_DIR / ".selftest"
    selftest.unlink(missing_ok=True)
    shutil.copyfile("/bin/true", selftest)
    selftest.chmod(0o500)
    subprocess.run(command(selftest, "validate"), check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)


def main() -> None:
    preflight()
    SOCKET_PATH.unlink(missing_ok=True)
    with Server(str(SOCKET_PATH), Handler) as server:
        SOCKET_PATH.chmod(0o660)
        server.serve_forever()


if __name__ == "__main__":
    main()
