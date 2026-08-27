#!/usr/bin/env python3
"""Tiny roundtrip helper for a running Jina service."""

from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="grpc://localhost")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--protocol", default="grpc", choices=["grpc", "http", "websocket"])
    parser.add_argument("--text", default="hello")
    args = parser.parse_args()

    from jina import Client
    from docarray import BaseDoc

    class InputDoc(BaseDoc):
        text: str = args.text

    client = Client(host=args.host, port=args.port, protocol=args.protocol)
    response = client.post("/", InputDoc(), return_responses=True)
    print(json.dumps({"responses": len(response)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
