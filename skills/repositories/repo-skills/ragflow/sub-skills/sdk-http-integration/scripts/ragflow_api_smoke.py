#!/usr/bin/env python3
"""Prepare or run a safe RAGFlow public API smoke request.

By default this script performs no network calls. It validates the supplied
base URL/API key shape and prints a redacted prepared request. Use --execute to
run a lightweight GET /api/v1/system/healthz check; that endpoint does not
require authentication and has no side effects.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class PreparedRequest:
    method: str
    url: str
    headers: dict[str, str]


def positive_timeout(value: str) -> float:
    try:
        timeout = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be a number") from exc
    if timeout <= 0:
        raise argparse.ArgumentTypeError("timeout must be greater than zero")
    return timeout


def normalize_base_url(raw_url: str) -> str:
    value = raw_url.strip().rstrip("/")
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("base URL must start with http:// or https://")
    if not parsed.netloc:
        raise ValueError("base URL must include a host")
    if parsed.path.endswith("/api/v1") or "/api/v1/" in parsed.path:
        raise ValueError(
            "base URL should be the server origin, not an /api/v1 endpoint; "
            "use a value like http://localhost:9380"
        )
    return value


def redacted_api_key(api_key: str | None) -> str:
    if not api_key:
        return "<not provided>"
    key = api_key.strip()
    if len(key) <= 8:
        return "<provided; redacted>"
    return f"{key[:4]}...{key[-4:]}"


def build_request(base_url: str, api_key: str | None, include_auth: bool) -> PreparedRequest:
    headers = {"Content-Type": "application/json"}
    if include_auth and api_key:
        headers["Authorization"] = f"Bearer {api_key.strip()}"
    return PreparedRequest(
        method="GET",
        url=f"{base_url}/api/v1/system/healthz",
        headers=headers,
    )


def printable_headers(headers: dict[str, str]) -> dict[str, str]:
    result = dict(headers)
    if "Authorization" in result:
        result["Authorization"] = "Bearer <redacted>"
    return result


def print_curl(request: PreparedRequest) -> None:
    print("Prepared request (no network call unless --execute is used):")
    parts = [
        "curl --request GET",
        f"  --url '{request.url}'",
    ]
    for name, value in printable_headers(request.headers).items():
        parts.append(f"  --header '{name}: {value}'")
    print(" \\\n".join(parts))


def execute_health_check(request: PreparedRequest, timeout: float) -> int:
    http_request = urllib.request.Request(
        request.url,
        method=request.method,
        headers=request.headers,
    )
    try:
        with urllib.request.urlopen(http_request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            status = response.status
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code} from RAGFlow health endpoint", file=sys.stderr)
        if body:
            print(body)
        return 1
    except urllib.error.URLError as exc:
        print(f"Could not reach RAGFlow health endpoint: {exc.reason}", file=sys.stderr)
        return 1
    except TimeoutError:
        print("Timed out reaching RAGFlow health endpoint", file=sys.stderr)
        return 1

    print(f"HTTP {status}")
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        print(body)
        return 0 if 200 <= status < 300 else 1

    print(json.dumps(parsed, indent=2, sort_keys=True))
    if parsed.get("status") == "ok":
        return 0
    return 0 if 200 <= status < 300 else 1


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare or optionally execute a safe RAGFlow GET /api/v1/system/healthz "
            "smoke check. Default mode performs no network call."
        )
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("RAGFLOW_BASE_URL", ""),
        help="RAGFlow server origin such as http://localhost:9380. May also be set with RAGFLOW_BASE_URL.",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("RAGFLOW_API_KEY", ""),
        help="Optional RAGFlow API key for validating presence/redaction. May also be set with RAGFLOW_API_KEY.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually run the non-destructive health check. Without this flag, only print the prepared request.",
    )
    parser.add_argument(
        "--include-auth",
        action="store_true",
        help="Include a redacted Authorization header in printed requests and a real header when --execute is used. Healthz does not require it.",
    )
    parser.add_argument(
        "--print-curl",
        action="store_true",
        help="Print the prepared curl command. This is always done in dry-run mode.",
    )
    parser.add_argument(
        "--timeout",
        type=positive_timeout,
        default=5.0,
        help="Network timeout in seconds when --execute is used. Default: 5.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if not args.base_url:
        print("Missing --base-url or RAGFLOW_BASE_URL", file=sys.stderr)
        return 2

    try:
        base_url = normalize_base_url(args.base_url)
    except ValueError as exc:
        print(f"Invalid --base-url: {exc}", file=sys.stderr)
        return 2

    api_key = args.api_key.strip() or None
    if args.include_auth and not api_key:
        print("--include-auth was requested but no API key was provided", file=sys.stderr)
        return 2

    request = build_request(base_url, api_key, args.include_auth)
    print(f"Base URL: {base_url}")
    print(f"API key: {redacted_api_key(api_key)}")
    print(f"Endpoint: {request.url}")

    if args.print_curl or not args.execute:
        print_curl(request)

    if not args.execute:
        print("Dry run only. Add --execute to perform the health check.")
        return 0

    return execute_health_check(request, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
