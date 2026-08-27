#!/usr/bin/env python3
"""Safe Argilla import/version checker.

Default behavior performs local imports and metadata checks only. Add
--check-server only when you intentionally want a live API call to client.me.
"""

from __future__ import annotations

import argparse
import os
import sys
from importlib import metadata


def version_or_missing(dist: str) -> str:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return "not-installed"


def check_imports(include_server: bool) -> int:
    status = 0
    try:
        import argilla as rg

        print("argilla import: ok")
        print(f"argilla module version: {getattr(rg, '__version__', 'unknown')}")
        print(f"argilla distribution: {version_or_missing('argilla')}")
        print("Argilla client class:", rg.Argilla)
    except Exception as exc:  # pragma: no cover - diagnostic output path
        print(f"argilla import: failed: {exc}", file=sys.stderr)
        status = 1

    if include_server:
        try:
            import argilla_server

            print("argilla_server import: ok")
            print(f"argilla-server distribution: {version_or_missing('argilla-server')}")
            print("argilla_server exposes app:", hasattr(argilla_server, "app"))
        except Exception as exc:  # pragma: no cover
            print(f"argilla_server import: failed: {exc}", file=sys.stderr)
            status = 1

    print(f"httpx distribution: {version_or_missing('httpx')}")
    print(f"pydantic distribution: {version_or_missing('pydantic')}")
    return status


def check_live_server(args: argparse.Namespace) -> int:
    import argilla as rg

    if not args.api_key:
        print("--check-server requires --api-key or ARGILLA_API_KEY", file=sys.stderr)
        return 2

    http_client_args = {}
    if args.hf_token:
        http_client_args["headers"] = {"Authorization": f"Bearer {args.hf_token}"}

    client = rg.Argilla(
        api_url=args.api_url,
        api_key=args.api_key,
        timeout=args.timeout,
        retries=args.retries,
        **http_client_args,
    )
    me = client.me
    print("live server check: ok")
    print(f"authenticated user: {getattr(me, 'username', '<unknown>')} role={getattr(me, 'role', '<unknown>')}")
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Argilla SDK/server imports and optionally perform a live client.me check.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--include-server", action="store_true", help="Also import argilla_server locally")
    parser.add_argument("--check-server", action="store_true", help="Perform a live Argilla API call to client.me")
    parser.add_argument("--api-url", default=os.getenv("ARGILLA_API_URL", "http://localhost:6900"))
    parser.add_argument("--api-key", default=os.getenv("ARGILLA_API_KEY"))
    parser.add_argument("--hf-token", default=os.getenv("HF_TOKEN"), help="Optional Hugging Face token for private Spaces")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--retries", type=int, default=5)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    status = check_imports(include_server=args.include_server)
    if args.check_server:
        live_status = check_live_server(args)
        status = live_status if status == 0 else status
    else:
        print("live server check: skipped (pass --check-server to contact an Argilla API)")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
