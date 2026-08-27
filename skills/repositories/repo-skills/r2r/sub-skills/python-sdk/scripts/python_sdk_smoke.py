#!/usr/bin/env python3
"""Safe Python SDK smoke helper for the R2R skill tree."""

from __future__ import annotations

import argparse
import inspect
import json
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

def _sig(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "<unavailable>"

def _import_report() -> dict[str, Any]:
    from r2r import R2RAsyncClient, R2RClient, get_version

    client = R2RClient()
    async_client = R2RAsyncClient()
    return {
        "version": get_version(),
        "client": _sig(R2RClient),
        "async_client": _sig(R2RAsyncClient),
        "groups": sorted(
            [name for name in ("system", "users", "documents", "chunks", "collections", "retrieval", "graphs", "prompts", "indices", "conversations")]
        ),
        "default_base_url": client.base_url,
        "async_default_base_url": async_client.base_url,
    }

def _health(base_url: str) -> dict[str, Any]:
    request = Request(base_url.rstrip("/") + "/v3/health")
    with urlopen(request, timeout=10) as response:
        return {
            "status": getattr(response, "status", response.getcode()),
            "body": response.read().decode("utf-8", errors="replace"),
        }

def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect the public R2R Python SDK surface and optionally probe a health endpoint.")
    parser.add_argument("--base-url", help="Optional R2R base URL, such as http://localhost:7272.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a human summary.")
    args = parser.parse_args()

    report = {"imports": _import_report()}
    if args.base_url:
        try:
            report["health"] = _health(args.base_url)
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            report["health_error"] = str(exc)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"r2r {report['imports']['version']}")
        print(f"R2RClient: {report['imports']['client']}")
        print(f"R2RAsyncClient: {report['imports']['async_client']}")
        print(f"default base URL: {report['imports']['default_base_url']}")
        if "health" in report:
            print(f"health status: {report['health']['status']}")
        elif "health_error" in report:
            print(f"health probe failed: {report['health_error']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
