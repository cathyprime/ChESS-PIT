#!/usr/bin/env python3
"""Container healthcheck for the API service.

Kept as a file (instead of an inline `python -c` one-liner) because Podman's
Docker-compatible healthcheck path re-splits the test argv on whitespace.

Pass --require-tools to additionally assert that the bundled chess engines are
available.
"""
import json
import sys
import urllib.request

HEALTH_URL = "http://127.0.0.1:8000/api/health"


def main(argv: list[str]) -> int:
    with urllib.request.urlopen(HEALTH_URL, timeout=5) as response:
        data = json.load(response)
    if data.get("sandbox") != "ready":
        return 1
    if "--require-tools" in argv:
        if not (data.get("ok") and data.get("stockfish") and data.get("fastchess")):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
