#!/usr/bin/env python3
"""Preflight a Nerfstudio viewer config and optional port choice without starting the viewer.

Examples:
    python check_viewer_config.py --config outputs/scene/nerfacto/run/config.yml
    python check_viewer_config.py --config config.yml --port 7007
"""

from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path


def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Check viewer config paths and port availability without opening a viewer.")
    parser.add_argument("--config", type=Path, required=True, help="Path to a saved Nerfstudio config.yml.")
    parser.add_argument("--port", type=int, default=7007, help="Viewer websocket port to test for local availability.")
    args = parser.parse_args()

    failures: list[str] = []
    if not args.config.exists():
        failures.append(f"config not found: {args.config}")
    elif not args.config.name.startswith("config."):
        print("Warning: expected a saved run config named config.yml/config.yaml")

    if not port_free(args.port):
        failures.append(f"port {args.port} is already in use")
    else:
        print(f"port {args.port} appears free")

    if failures:
        print("Failures:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("Viewer preflight passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
