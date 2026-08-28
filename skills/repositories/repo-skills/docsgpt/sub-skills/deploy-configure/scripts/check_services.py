#!/usr/bin/env python3
"""Read-only reachability checks for DocsGPT API, Postgres, and Redis.

URI passwords are never printed. Postgres and Redis checks require the matching
client packages; the API check uses the standard library.
"""

from __future__ import annotations

import argparse
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request


def redact(uri: str) -> str:
    parsed = urllib.parse.urlsplit(uri)
    host = parsed.hostname or "?"
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://{host}{port}{parsed.path or ''}"


def check_api(url: str, timeout: float) -> tuple[bool, str]:
    target = url.rstrip("/") + "/api/health"
    try:
        with urllib.request.urlopen(target, timeout=timeout) as response:
            return 200 <= response.status < 300, f"HTTP {response.status}"
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return False, str(error)


def check_postgres(uri: str, timeout: float) -> tuple[bool, str]:
    try:
        import psycopg
    except ImportError:
        return False, "psycopg is not installed"
    # DocsGPT accepts the SQLAlchemy dialect form; psycopg itself expects the
    # ordinary postgresql scheme.
    direct_uri = uri.replace("postgresql+psycopg://", "postgresql://", 1)
    try:
        with psycopg.connect(direct_uri, connect_timeout=max(1, int(timeout))) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return cursor.fetchone() == (1,), "SELECT 1"
    except Exception as error:  # client error types differ by version
        return False, f"{type(error).__name__}: {error}"


def check_redis(uri: str, timeout: float) -> tuple[bool, str]:
    try:
        import redis
    except ImportError:
        return False, "redis package is not installed"
    try:
        client = redis.Redis.from_url(uri, socket_connect_timeout=timeout, socket_timeout=timeout)
        return bool(client.ping()), "PING"
    except Exception as error:
        return False, f"{type(error).__name__}: {error}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url")
    parser.add_argument("--postgres-uri")
    parser.add_argument("--redis-url")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()
    if not any((args.api_url, args.postgres_uri, args.redis_url)):
        parser.error("provide at least one service option")

    checks: list[tuple[str, tuple[bool, str]]] = []
    if args.api_url:
        checks.append((args.api_url.rstrip("/") + "/api/health", check_api(args.api_url, args.timeout)))
    if args.postgres_uri:
        checks.append((redact(args.postgres_uri), check_postgres(args.postgres_uri, args.timeout)))
    if args.redis_url:
        checks.append((redact(args.redis_url), check_redis(args.redis_url, args.timeout)))

    failed = 0
    for target, (ok, detail) in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {target}: {detail}")
        failed += not ok
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
