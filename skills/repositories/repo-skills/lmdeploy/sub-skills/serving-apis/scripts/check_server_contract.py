#!/usr/bin/env python3
"""Validate LMDeploy serving base URL contracts.

The default mode performs no network calls. It normalizes base URLs, prints the
expected endpoint map, and renders representative request payloads. Add
``--probe`` to run live HTTP checks against an already-running LMDeploy server.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse


@dataclass(frozen=True)
class Endpoint:
    name: str
    method: str
    path: str
    payload: dict[str, Any] | None = None
    headers: dict[str, str] | None = None


def normalize_root(base_url: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("--base-url must be an absolute http(s) URL such as http://127.0.0.1:23333")
    normalized = base_url.rstrip("/")
    if normalized.endswith("/v1"):
        normalized = normalized[:-3]
    if any(normalized.endswith(suffix) for suffix in ("/v1/chat/completions", "/v1/completions", "/v1/responses", "/v1/messages")):
        raise ValueError("--base-url must be the server root or /v1 root, not a concrete endpoint")
    return normalized


def endpoint_url(root: str, path: str) -> str:
    return urljoin(root + "/", path.lstrip("/"))


def auth_headers(api_key: str | None) -> dict[str, str]:
    if not api_key:
        return {}
    return {"Authorization": f"Bearer {api_key}"}


def build_endpoints(model: str, api_key: str | None) -> list[Endpoint]:
    authorization = auth_headers(api_key)
    json_headers = {"content-type": "application/json", **authorization}
    anthropic_headers = {"content-type": "application/json", "anthropic-version": "2023-06-01", **authorization}
    return [
        Endpoint("models", "GET", "/v1/models", headers=authorization),
        Endpoint(
            "chat_completions",
            "POST",
            "/v1/chat/completions",
            headers=json_headers,
            payload={
                "model": model,
                "messages": [{"role": "user", "content": "Reply exactly: pong"}],
                "max_tokens": 32,
                "temperature": 0,
            },
        ),
        Endpoint(
            "completions",
            "POST",
            "/v1/completions",
            headers=json_headers,
            payload={"model": model, "prompt": "Reply exactly: pong", "max_tokens": 32, "temperature": 0},
        ),
        Endpoint(
            "responses",
            "POST",
            "/v1/responses",
            headers=json_headers,
            payload={"model": model, "input": "Reply exactly: pong", "max_output_tokens": 32},
        ),
        Endpoint(
            "anthropic_messages",
            "POST",
            "/v1/messages",
            headers=anthropic_headers,
            payload={
                "model": model,
                "max_tokens": 32,
                "messages": [{"role": "user", "content": "Reply exactly: pong"}],
            },
        ),
        Endpoint(
            "anthropic_count_tokens",
            "POST",
            "/v1/messages/count_tokens",
            headers=anthropic_headers,
            payload={
                "model": model,
                "messages": [{"role": "user", "content": "Count these tokens"}],
            },
        ),
        Endpoint("anthropic_models", "GET", "/anthropic/v1/models", headers=authorization),
    ]


def emit_plan(root: str, endpoints: list[Endpoint]) -> None:
    print(json.dumps({"base_url_root": root, "v1_base_url": root + "/v1"}, indent=2))
    for item in endpoints:
        print(f"\n[{item.name}] {item.method} {endpoint_url(root, item.path)}")
        if item.headers:
            safe_headers = {key: ("<redacted>" if key.lower() == "authorization" else value) for key, value in item.headers.items()}
            print(json.dumps({"headers": safe_headers}, indent=2))
        if item.payload is not None:
            print(json.dumps(item.payload, indent=2))


def http_request(url: str, endpoint: Endpoint, timeout: float) -> tuple[int, str]:
    data = None
    if endpoint.payload is not None:
        data = json.dumps(endpoint.payload).encode("utf-8")
    request = urllib.request.Request(url=url, method=endpoint.method, data=data, headers=endpoint.headers or {})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read(4096).decode("utf-8", errors="replace")
        return response.status, body


def probe(root: str, endpoints: list[Endpoint], timeout: float, require_all: bool) -> int:
    failures: list[str] = []
    for item in endpoints:
        url = endpoint_url(root, item.path)
        try:
            status, body = http_request(url, item, timeout)
            ok = 200 <= status < 300
            print(json.dumps({"name": item.name, "url": url, "status": status, "ok": ok}, indent=2))
            if not ok:
                failures.append(f"{item.name}: HTTP {status}")
            elif item.name == "models":
                parsed = json.loads(body)
                if "data" not in parsed:
                    failures.append("models: response lacks data field")
        except urllib.error.HTTPError as exc:
            body = exc.read(1024).decode("utf-8", errors="replace")
            message = f"{item.name}: HTTP {exc.code} {body[:200]}"
            print(message, file=sys.stderr)
            failures.append(message)
        except Exception as exc:  # noqa: BLE001 - CLI diagnostic should report any probe failure.
            message = f"{item.name}: {exc}"
            print(message, file=sys.stderr)
            failures.append(message)
    if failures:
        print(json.dumps({"probe_failures": failures}, indent=2), file=sys.stderr)
        return 1 if require_all else 0
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check LMDeploy OpenAI/Responses/Anthropic serving URL contracts.")
    parser.add_argument("--base-url", default="http://127.0.0.1:23333", help="Server root or /v1 root URL.")
    parser.add_argument("--model", default="lmdeploy-model", help="Model id to place in example/probe payloads.")
    parser.add_argument("--api-key", default=None, help="Optional bearer token for servers launched with --api-keys.")
    parser.add_argument("--probe", action="store_true", help="Perform live HTTP requests; default only prints contracts.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds for --probe.")
    parser.add_argument(
        "--allow-probe-failures",
        action="store_true",
        help="Return success even if one or more live probes fail; useful for partial endpoint checks.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        root = normalize_root(args.base_url)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    endpoints = build_endpoints(args.model, args.api_key)
    emit_plan(root, endpoints)
    if args.probe:
        return probe(root, endpoints, args.timeout, require_all=not args.allow_probe_failures)
    print("\nOffline contract check complete. Re-run with --probe to contact a live server.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
