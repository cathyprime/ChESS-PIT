#!/usr/bin/env python3
"""Container healthcheck for the runner daemon.

Kept as a file (instead of an inline `python -c` one-liner) because Podman's
Docker-compatible healthcheck path re-splits the test argv on whitespace.
"""
import os
import socket
import sys

SOCKET_PATH = os.environ.get("RUNNER_SOCKET", "/run/chesspit-runner/runner.sock")


def main() -> int:
    with socket.socket(socket.AF_UNIX) as sock:
        sock.settimeout(1)
        sock.connect(SOCKET_PATH)
        sock.sendall(b'{"version":1,"op":"health"}\n')
        if b'"ok":true' not in sock.recv(256):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
