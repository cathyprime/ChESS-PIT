#!/usr/bin/env python3
"""Constant-memory UCI proxy for the permissioned sandbox runner socket."""
import json
import os
import selectors
import socket
import sys


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: sandbox-engine.py PURPOSE STORAGE_KEY SHA256", file=sys.stderr)
        return 64
    sock_path = os.environ.get("RUNNER_SOCKET", "/run/chesspit-runner/runner.sock")
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(sock_path)
        header = {"version": 1, "purpose": sys.argv[1], "key": sys.argv[2], "sha256": sys.argv[3]}
        sock.sendall(json.dumps(header, separators=(",", ":")).encode() + b"\n")
        response = bytearray()
        while not response.endswith(b"\n") and len(response) <= 4096:
            chunk = sock.recv(1)
            if not chunk:
                break
            response += chunk
        reply = json.loads(response or b"{}")
        if not reply.get("ok"):
            print(reply.get("error", "sandbox unavailable"), file=sys.stderr)
            return 69
        selector = selectors.DefaultSelector()
        selector.register(sock, selectors.EVENT_READ, "out")
        selector.register(sys.stdin.buffer, selectors.EVENT_READ, "in")
        while selector.get_map():
            for key, _ in selector.select():
                if key.data == "in":
                    data = os.read(sys.stdin.fileno(), 65536)
                    if data:
                        sock.sendall(data)
                    else:
                        selector.unregister(sys.stdin.buffer)
                        sock.shutdown(socket.SHUT_WR)
                else:
                    data = sock.recv(65536)
                    if not data:
                        return 0
                    os.write(sys.stdout.fileno(), data)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"sandbox unavailable: {exc}", file=sys.stderr)
        return 69
    finally:
        sock.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
