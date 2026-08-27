#!/usr/bin/env python3
"""Connect to a live UnrealCV server and issue one or more requests.

This helper is for live-server workflows only. It is safe by default because it
only connects, requests the commands you ask for, prints the responses, and
exits.

Example:
    python connect_and_request.py --host 127.0.0.1 --port 9000 \
        --command "vget /unrealcv/status" --command "vget /unrealcv/version"
"""

from __future__ import annotations

import argparse
from pathlib import Path

from unrealcv import Client


def main() -> int:
    parser = argparse.ArgumentParser(description="Connect to a live UnrealCV server")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=9000, help="Server port")
    parser.add_argument(
        "--timeout", type=float, default=1.0, help="Connection and request timeout"
    )
    parser.add_argument(
        "--command",
        action="append",
        default=["vget /unrealcv/status"],
        help="UnrealCV command to send; may be repeated",
    )
    parser.add_argument(
        "--unix",
        action="store_true",
        help="Use a Unix-domain socket endpoint at /tmp/unrealcv_<port>.socket",
    )
    args = parser.parse_args()

    if args.unix:
        endpoint = f"/tmp/unrealcv_{args.port}.socket"
        client = Client(endpoint, "unix")
    else:
        client = Client((args.host, args.port), "inet")

    if not client.connect(timeout=args.timeout):
        print("UnrealCV server is not running or the endpoint is unreachable.")
        return 2

    try:
        for command in args.command:
            response = client.request(command, timeout=args.timeout)
            print(f"> {command}")
            print(response)
    finally:
        client.disconnect()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
