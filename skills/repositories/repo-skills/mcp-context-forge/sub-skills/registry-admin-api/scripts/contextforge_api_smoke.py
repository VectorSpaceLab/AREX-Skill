#!/usr/bin/env python3
"""Read-only ContextForge API smoke checks.

The helper intentionally uses only the Python standard library so it can run
from arbitrary current directories without a project checkout or installed test
dependencies. It performs GET requests only.
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
from typing import Any


@dataclass
class CheckResult:
    """Result for one HTTP smoke check."""

    name: str
    url: str
    status: int | None
    ok: bool
    detail: str
    json_type: str | None = None


def _normalize_base_url(value: str) -> str:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise argparse.ArgumentTypeError("--base-url must be an absolute http(s) URL")
    return value.rstrip("/")


def _normalize_path(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return path


def _build_url(base_url: str, path: str) -> str:
    return base_url + _normalize_path(path)


def _json_type(value: Any) -> str:
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if value is None:
        return "null"
    return type(value).__name__


def _decode_json(raw: bytes) -> tuple[Any | None, str | None]:
    if not raw:
        return None, "empty response body"
    try:
        return json.loads(raw.decode("utf-8")), None
    except UnicodeDecodeError as exc:
        return None, f"response is not UTF-8 JSON: {exc}"
    except json.JSONDecodeError as exc:
        snippet = raw[:200].decode("utf-8", errors="replace")
        return None, f"response is not JSON: {exc}; body starts with {snippet!r}"


def _get_json(base_url: str, path: str, token: str | None, timeout: float) -> tuple[int | None, Any | None, str | None, str]:
    url = _build_url(base_url, path)
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - explicit user-provided base URL smoke check
            raw = response.read()
            status = int(response.status)
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = int(exc.code)
    except urllib.error.URLError as exc:
        return None, None, f"request failed: {exc.reason}", url
    except TimeoutError:
        return None, None, "request timed out", url

    data, json_error = _decode_json(raw)
    return status, data, json_error, url


def _check_health(base_url: str, timeout: float) -> CheckResult:
    status, data, error, url = _get_json(base_url, "/health", token=None, timeout=timeout)
    if status is None:
        return CheckResult("health", url, status, False, error or "request failed")
    if not 200 <= status < 300:
        return CheckResult("health", url, status, False, f"unexpected HTTP {status}")
    if error:
        return CheckResult("health", url, status, False, error)
    detail = "health endpoint returned 2xx JSON"
    if isinstance(data, dict) and data.get("status"):
        detail = f"health status={data.get('status')!r}"
    return CheckResult("health", url, status, True, detail, _json_type(data))


def _check_generic(name: str, base_url: str, path: str, token: str, timeout: float) -> CheckResult:
    status, data, error, url = _get_json(base_url, path, token=token, timeout=timeout)
    if status is None:
        return CheckResult(name, url, status, False, error or "request failed")
    if not 200 <= status < 300:
        detail = f"unexpected HTTP {status}"
        if error is None and isinstance(data, dict) and "detail" in data:
            detail += f": {data['detail']!r}"
        return CheckResult(name, url, status, False, detail, _json_type(data) if error is None else None)
    if error:
        return CheckResult(name, url, status, False, error)
    return CheckResult(name, url, status, True, f"returned {_json_type(data)}", _json_type(data))


def _summarize_list_shape(result: CheckResult, data_path: str | None = None) -> str:
    if result.json_type == "array":
        return "plain array list response"
    if result.json_type == "object":
        if data_path:
            return f"object response; inspect key {data_path!r}"
        return "object response; likely cursor or Admin page shape"
    return result.detail


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run read-only ContextForge API smoke checks using stdlib urllib/json.",
    )
    parser.add_argument("--base-url", required=True, type=_normalize_base_url, help="Base URL, for example http://localhost:4444")
    parser.add_argument(
        "--token",
        default=os.environ.get("MCPGATEWAY_BEARER_TOKEN"),
        help="Bearer token. Defaults to MCPGATEWAY_BEARER_TOKEN. If omitted, only /health is checked.",
    )
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds. Default: 10")
    parser.add_argument("--check-version", action="store_true", help="With a token, also check /v1/version.")
    parser.add_argument("--version-path", default="/v1/version", help="Version endpoint path. Default: /v1/version")
    parser.add_argument(
        "--list-endpoint",
        default="/v1/tools?include_pagination=false",
        help="Read-only list endpoint to check when a token is present. Default: /v1/tools?include_pagination=false",
    )
    parser.add_argument("--no-list", action="store_true", help="Do not check the read-only list endpoint even when a token is present.")
    parser.add_argument("--json", action="store_true", help="Print only machine-readable JSON summary.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    results: list[CheckResult] = []

    results.append(_check_health(args.base_url, args.timeout))

    token = args.token
    if token:
        if args.check_version:
            results.append(_check_generic("version", args.base_url, args.version_path, token, args.timeout))
        if not args.no_list and args.list_endpoint:
            list_result = _check_generic("list", args.base_url, args.list_endpoint, token, args.timeout)
            list_result.detail = _summarize_list_shape(list_result)
            results.append(list_result)
    else:
        results.append(CheckResult("auth-dependent", args.base_url, None, True, "skipped: no token provided"))

    summary = {
        "ok": all(item.ok for item in results),
        "checks": [item.__dict__ for item in results],
    }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        for item in results:
            status = "PASS" if item.ok else "FAIL"
            code = "n/a" if item.status is None else str(item.status)
            print(f"[{status}] {item.name}: HTTP {code} {item.url} - {item.detail}")
        print(json.dumps(summary, indent=2, sort_keys=True))

    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
