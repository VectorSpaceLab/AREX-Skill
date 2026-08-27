#!/usr/bin/env python3
"""Probe qdrant-client remote transport configuration without requiring a server.

The script constructs QdrantClient with check_compatibility=False, prints the
resolved REST URI and selected transport settings, then closes the client. It is
for address/auth/transport shape validation only; it does not prove network
reachability, credentials, server compatibility, or API behavior.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    endpoint = parser.add_mutually_exclusive_group()
    endpoint.add_argument("--url", help="Complete Qdrant endpoint, e.g. https://host:6333")
    endpoint.add_argument("--host", help="Host without http:// or https://")
    parser.add_argument("--port", type=int, default=6333, help="REST port when --host is used")
    parser.add_argument("--no-port", action="store_true", help="Do not append a REST port")
    parser.add_argument("--grpc-port", type=int, default=6334, help="gRPC port")
    parser.add_argument("--prefix", help="Reverse-proxy path prefix, e.g. api/v1")
    parser.add_argument("--https", action="store_true", help="Force HTTPS when --host is used")
    parser.add_argument("--api-key", help="API key placeholder or real key for header-shape validation")
    parser.add_argument(
        "--header",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="Additional header; repeat for multiple headers",
    )
    parser.add_argument("--prefer-grpc", action="store_true", help="Prefer gRPC for supported methods")
    parser.add_argument("--pool-size", type=int, help="Remote connection pool size")
    parser.add_argument("--timeout", type=float, help="Timeout value passed to QdrantClient")
    parser.add_argument("--http2", action="store_true", help="Enable HTTP/2 for the REST client")
    return parser


def parse_headers(items: list[str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Header must be NAME=VALUE, got: {item!r}")
        name, value = item.split("=", 1)
        name = name.strip()
        if not name:
            raise ValueError(f"Header name cannot be empty: {item!r}")
        headers[name] = value
    return headers


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        headers = parse_headers(args.header)
    except ValueError as exc:
        parser.error(str(exc))

    try:
        from qdrant_client import QdrantClient
    except Exception as exc:  # pragma: no cover - environment guard
        print(f"Unable to import qdrant_client: {exc}", file=sys.stderr)
        return 2

    kwargs: dict[str, Any] = {
        "grpc_port": args.grpc_port,
        "prefer_grpc": args.prefer_grpc,
        "check_compatibility": False,
    }
    if args.url:
        kwargs["url"] = args.url
    if args.host:
        kwargs["host"] = args.host
    if args.no_port:
        kwargs["port"] = None
    elif args.port is not None:
        kwargs["port"] = args.port
    if args.prefix:
        kwargs["prefix"] = args.prefix
    if args.https:
        kwargs["https"] = True
    if args.api_key:
        kwargs["api_key"] = args.api_key
    if headers:
        kwargs["headers"] = headers
    if args.pool_size is not None:
        kwargs["pool_size"] = args.pool_size
    if args.timeout is not None:
        kwargs["timeout"] = args.timeout
    if args.http2:
        kwargs["http2"] = True

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            client = QdrantClient(**kwargs)
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True))
            return 1

    remote = client._client
    result = {
        "ok": True,
        "rest_uri": getattr(remote, "rest_uri", None),
        "prefer_grpc": getattr(remote, "_prefer_grpc", None),
        "grpc_port": getattr(remote, "_grpc_port", None),
        "https": getattr(remote, "_https", None),
        "prefix": getattr(remote, "_prefix", None),
        "pool_size": getattr(remote, "_pool_size", None),
        "timeout": getattr(remote, "_timeout", None),
        "rest_header_names": sorted(getattr(remote, "_rest_headers", {}).keys()),
        "grpc_header_names": sorted(name for name, _ in getattr(remote, "_grpc_headers", [])),
        "warnings": [str(item.message) for item in caught],
    }

    try:
        client.close()
    finally:
        print(json.dumps(result, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
