#!/usr/bin/env python3
"""Inspect a running BentoML HTTP service without starting a server."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


def _get_json(url: str, timeout: float, token: str | None) -> Any:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - explicit user URL inspection helper
        charset = response.headers.get_content_charset() or "utf-8"
        return json.loads(response.read().decode(charset))


def _check_ready(url: str, timeout: float, token: str | None) -> tuple[bool, str]:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(urljoin(url.rstrip("/") + "/", "readyz"), headers=headers)
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - explicit user URL inspection helper
            return response.status == 200, f"HTTP {response.status}"
    except HTTPError as exc:
        return False, f"HTTP {exc.code}"
    except URLError as exc:
        return False, str(exc.reason)
    except TimeoutError:
        return False, "timeout"


def _summarize_schema(schema: dict[str, Any]) -> list[dict[str, Any]]:
    routes = schema.get("routes")
    if not isinstance(routes, list):
        raise ValueError("schema JSON does not contain a routes list")
    summaries: list[dict[str, Any]] = []
    for route in routes:
        if not isinstance(route, dict):
            continue
        output = route.get("output") if isinstance(route.get("output"), dict) else {}
        summaries.append(
            {
                "name": route.get("name"),
                "route": route.get("route"),
                "doc": route.get("doc"),
                "is_stream": bool(output.get("is_stream", False)),
                "is_task": bool(route.get("is_task", False)),
                "input": route.get("input"),
                "output": route.get("output"),
            }
        )
    return summaries


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect /readyz and /schema.json for an already running BentoML HTTP service."
    )
    parser.add_argument("--url", required=True, help="Base URL, for example http://localhost:3000")
    parser.add_argument("--timeout", type=float, default=5.0, help="Request timeout in seconds")
    parser.add_argument("--token", default=None, help="Optional bearer token")
    parser.add_argument("--json", action="store_true", help="Print full summarized JSON")
    args = parser.parse_args()

    base_url = args.url.rstrip("/") + "/"
    ready, ready_detail = _check_ready(base_url, args.timeout, args.token)
    print(f"ready: {ready} ({ready_detail})")

    try:
        schema = _get_json(urljoin(base_url, "schema.json"), args.timeout, args.token)
        endpoints = _summarize_schema(schema)
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        print(f"failed to fetch schema: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"ready": ready, "endpoints": endpoints}, indent=2, sort_keys=True))
        return 0

    print(f"endpoints: {len(endpoints)}")
    for endpoint in endpoints:
        input_schema = endpoint.get("input") if isinstance(endpoint.get("input"), dict) else {}
        required = input_schema.get("required", []) if isinstance(input_schema, dict) else []
        properties = input_schema.get("properties", {}) if isinstance(input_schema, dict) else {}
        property_names = list(properties.keys()) if isinstance(properties, dict) else []
        flags = []
        if endpoint["is_stream"]:
            flags.append("stream")
        if endpoint["is_task"]:
            flags.append("task")
        flag_text = f" [{' '.join(flags)}]" if flags else ""
        print(f"- {endpoint['name']} -> {endpoint['route']}{flag_text}")
        if required:
            print(f"  required: {', '.join(map(str, required))}")
        if property_names:
            print(f"  properties: {', '.join(map(str, property_names))}")
        elif input_schema.get("root_input"):
            print("  input: root positional value")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
