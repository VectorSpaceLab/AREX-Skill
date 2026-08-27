#!/usr/bin/env python3
"""Safe Mycodo REST API request helper.

Requires a host, endpoint, method, and API key supplied by --api-key or the
MYCODO_API_KEY environment variable. It defaults to the Mycodo v1 media type and
prints response status, a small response-header subset, and JSON/text body.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional
from urllib.parse import urlsplit

DEFAULT_ACCEPT = "application/vnd.mycodo.v1+json"
HEADER_SUBSET = [
    "content-type",
    "content-length",
    "date",
    "server",
    "location",
    "retry-after",
    "x-ratelimit-limit",
    "x-ratelimit-remaining",
    "x-ratelimit-reset",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Send one Mycodo REST API request using an API key from --api-key "
            "or MYCODO_API_KEY. No real keys are bundled or logged."
        )
    )
    parser.add_argument(
        "--host",
        required=True,
        help="Mycodo host/base URL, e.g. https://mycodo.local or https://192.0.2.10",
    )
    parser.add_argument(
        "--endpoint",
        required=True,
        help="Endpoint path, e.g. /api/daemon/ or settings/inputs",
    )
    parser.add_argument(
        "--method",
        required=True,
        choices=["GET", "POST", "PUT", "PATCH", "DELETE"],
        help="HTTP method to send.",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("MYCODO_API_KEY"),
        help="Base64 API key from Mycodo user settings. Defaults to MYCODO_API_KEY.",
    )
    parser.add_argument(
        "--auth-mode",
        choices=["x-api-key", "basic", "query"],
        default="x-api-key",
        help="Authentication placement. Default: x-api-key.",
    )
    parser.add_argument(
        "--json",
        dest="json_payload",
        help=(
            "JSON request body as a literal string, @path to read a file, or @- "
            "to read stdin. Required only for endpoints that need a body."
        ),
    )
    parser.add_argument(
        "--accept",
        default=DEFAULT_ACCEPT,
        help=f"Accept header. Default: {DEFAULT_ACCEPT}",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Request timeout in seconds. Default: 20.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification for trusted self-signed Mycodo hosts.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the prepared request with secrets redacted and do not send it.",
    )
    return parser


def normalize_url(host: str, endpoint: str) -> str:
    host = host.strip()
    endpoint = endpoint.strip()
    if not host:
        raise ValueError("--host cannot be empty")
    if not endpoint:
        raise ValueError("--endpoint cannot be empty")

    parsed_endpoint = urlsplit(endpoint)
    if parsed_endpoint.scheme or parsed_endpoint.netloc:
        raise ValueError("--endpoint must be a path, not a full URL")

    if not host.startswith(("https://", "http://")):
        host = "https://" + host
    host = host.rstrip("/")

    if endpoint.startswith("/api"):
        path = endpoint
    elif endpoint.startswith("api/"):
        path = "/" + endpoint
    else:
        path = "/api/" + endpoint.lstrip("/")

    if host.endswith("/api") and path.startswith("/api"):
        path = path[len("/api") :] or "/"

    return host + path


def load_json_payload(raw: Optional[str]) -> Optional[Any]:
    if raw is None:
        return None
    if raw.startswith("@"):
        source = raw[1:]
        if source == "-":
            text = sys.stdin.read()
        else:
            with open(source, "r", encoding="utf-8") as handle:
                text = handle.read()
    else:
        text = raw
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON payload: {exc}") from exc


def redacted_headers(headers: Dict[str, str]) -> Dict[str, str]:
    redacted = dict(headers)
    for key in list(redacted):
        if key.lower() in {"x-api-key", "authorization"}:
            redacted[key] = "<redacted>"
    return redacted


def print_response(response: Any) -> None:
    print(f"Status: {response.status_code} {response.reason}")
    subset = {}
    lower_to_key = {key.lower(): key for key in response.headers.keys()}
    for wanted in HEADER_SUBSET:
        actual = lower_to_key.get(wanted)
        if actual is not None:
            subset[actual] = response.headers[actual]
    print("Headers:")
    if subset:
        for key, value in subset.items():
            print(f"  {key}: {value}")
    else:
        print("  <none of selected headers present>")

    print("Body:")
    text = response.text or ""
    content_type = response.headers.get("Content-Type", "")
    if text and "json" in content_type.lower():
        try:
            parsed = response.json()
            print(json.dumps(parsed, indent=2, sort_keys=True, ensure_ascii=False))
            return
        except ValueError:
            pass
    if text:
        print(text)
    else:
        print("<empty>")


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.api_key:
        parser.error("provide --api-key or set MYCODO_API_KEY")

    try:
        url = normalize_url(args.host, args.endpoint)
        payload = load_json_payload(args.json_payload)
    except ValueError as exc:
        parser.error(str(exc))

    headers: Dict[str, str] = {"Accept": args.accept}
    params: Dict[str, str] = {}
    if payload is not None:
        headers["Content-Type"] = "application/json"

    if args.auth_mode == "x-api-key":
        headers["X-API-KEY"] = args.api_key
    elif args.auth_mode == "basic":
        headers["Authorization"] = f"Basic {args.api_key}"
    elif args.auth_mode == "query":
        params["api_key"] = args.api_key

    if args.dry_run:
        print("Dry run: request not sent")
        print(f"Method: {args.method}")
        print(f"URL: {url}")
        print("Headers:")
        for key, value in redacted_headers(headers).items():
            print(f"  {key}: {value}")
        if params:
            print("Query parameters:")
            for key in params:
                print(f"  {key}: <redacted>")
        if payload is not None:
            print("JSON body:")
            print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        else:
            print("JSON body: <none>")
        return 0

    try:
        import requests
    except ImportError as exc:
        print(
            "error: Python package 'requests' is required to use this helper",
            file=sys.stderr,
        )
        raise SystemExit(3) from exc

    if args.insecure:
        try:
            requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]
        except Exception:
            pass

    try:
        response = requests.request(
            args.method,
            url,
            headers=headers,
            params=params or None,
            json=payload,
            timeout=args.timeout,
            verify=not args.insecure,
        )
    except requests.RequestException as exc:
        print(f"request failed: {exc}", file=sys.stderr)
        return 4

    print_response(response)
    return 0 if response.status_code < 400 else 1


if __name__ == "__main__":
    raise SystemExit(main())
