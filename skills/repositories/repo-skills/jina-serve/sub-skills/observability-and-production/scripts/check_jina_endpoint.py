#!/usr/bin/env python3
"""Check a Jina endpoint using the installed package or plain HTTP/WebSocket clients."""

from __future__ import annotations

import argparse
import asyncio
import sys


def check_grpc(host: str, port: int) -> int:
    from jina import Client

    client = Client(host=host, port=port, protocol="grpc")
    client.post("/", None, return_responses=True)
    return 0


def check_http(host: str, port: int) -> int:
    import requests

    resp = requests.get(f"http://{host}:{port}/")
    return 0 if resp.status_code == 200 else 1


async def check_websocket(host: str, port: int) -> int:
    import websockets

    async with websockets.connect(f"ws://{host}:{port}"):
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("protocol", choices=["grpc", "http", "websocket"])
    parser.add_argument("host")
    parser.add_argument("port", type=int)
    args = parser.parse_args()

    if args.protocol == "grpc":
        return check_grpc(args.host, args.port)
    if args.protocol == "http":
        return check_http(args.host, args.port)
    return asyncio.run(check_websocket(args.host, args.port))


if __name__ == "__main__":
    raise SystemExit(main())
