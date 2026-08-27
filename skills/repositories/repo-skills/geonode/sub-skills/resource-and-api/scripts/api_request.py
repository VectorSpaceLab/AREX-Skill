#!/usr/bin/env python3
"""Small, explicit-origin GeoNode API probe.

This is intentionally not a deployment client: it sends only GET or a JSON
request, requires an explicit base URL, and never prints bearer-token values.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Send one safe GeoNode GET or JSON request. The origin is required "
            "explicitly; a bearer token is read from an environment variable "
            "and is never printed. 4xx means the request was rejected by the "
            "client/auth/permission/route layer; 5xx means the server or a "
            "downstream service failed and needs server-side diagnosis."
        )
    )
    p.add_argument("--base-url", required=True, help="Explicit site origin, for example https://geonode.example")
    p.add_argument("--path", default="/api/v2/resources/", help="Absolute path or URL path below the base URL")
    p.add_argument("--method", choices=("GET", "POST", "PUT", "PATCH"), default="GET")
    p.add_argument("--json", dest="json_body", help="JSON object/array to send for POST/PUT/PATCH")
    p.add_argument("--bearer-env", metavar="ENV", help="Environment variable containing a bearer token")
    p.add_argument("--timeout", type=float, default=20.0, help="Socket timeout in seconds (default: 20)")
    return p


def explicit_url(base_url: str, path: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("--base-url must be an explicit http(s) origin")
    if path.startswith("http://") or path.startswith("https://"):
        target = path
    else:
        target = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    target_parsed = urlparse(target)
    if target_parsed.scheme not in {"http", "https"} or not target_parsed.netloc:
        raise ValueError("--path did not produce an absolute http(s) URL")
    if (target_parsed.scheme, target_parsed.netloc) != (parsed.scheme, parsed.netloc):
        raise ValueError("--path must stay on the explicit --base-url origin")
    return target


def redacted_json(value):
    """Redact common credential fields before displaying a JSON response."""
    sensitive = ("token", "password", "secret", "authorization", "api_key")
    if isinstance(value, dict):
        return {
            key: "<redacted>" if any(part in key.lower() for part in sensitive) else redacted_json(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redacted_json(item) for item in value]
    return value


def print_response_body(raw: bytes, *, stream) -> None:
    if not raw:
        return
    try:
        print(json.dumps(redacted_json(json.loads(raw)), indent=2, sort_keys=True), file=stream)
    except (UnicodeDecodeError, json.JSONDecodeError):
        print(f"Response body: {len(raw)} bytes (not JSON)", file=stream)


def run(args: argparse.Namespace) -> int:
    try:
        url = explicit_url(args.base_url, args.path)
        body = None
        headers = {"Accept": "application/json"}
        if args.bearer_env:
            token = os.environ.get(args.bearer_env)
            if not token:
                raise ValueError(f"bearer environment variable is unset or empty: {args.bearer_env}")
            headers["Authorization"] = f"Bearer {token}"
        if args.json_body is not None:
            if args.method == "GET":
                raise ValueError("--json is not valid with GET")
            parsed_body = json.loads(args.json_body)
            body = json.dumps(parsed_body, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif args.method != "GET":
            raise ValueError("POST/PUT/PATCH requires --json")

        request = Request(url, data=body, headers=headers, method=args.method)
        with urlopen(request, timeout=args.timeout) as response:
            raw = response.read()
            content_type = response.headers.get("Content-Type", "")
            print(f"HTTP {response.status} {response.reason}")
            print(f"Content-Type: {content_type or 'unknown'}")
            print_response_body(raw, stream=sys.stdout)
            return 0
    except HTTPError as exc:
        # Do not print request headers or the URL query, which may contain a
        # signed URL. The status/body are enough for route/auth diagnosis.
        raw = exc.read()
        print(f"HTTP {exc.code} {exc.reason}", file=sys.stderr)
        print(
            "4xx indicates a client, authentication, permission, route, or "
            "validation rejection; 5xx indicates server/downstream failure.",
            file=sys.stderr,
        )
        print_response_body(raw, stream=sys.stderr)
        return 1
    except (URLError, TimeoutError) as exc:
        print(f"Request failed before an HTTP response: {exc}", file=sys.stderr)
        print("Check the explicit origin, DNS/TLS, proxy, and service readiness.", file=sys.stderr)
        return 2
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Invalid request: {exc}", file=sys.stderr)
        return 2


def main() -> int:
    return run(parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
