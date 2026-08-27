#!/usr/bin/env python3
"""Safe R2R environment probe for the generated skill tree."""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

def _callable_signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "<unavailable>"

def _probe_imports() -> dict[str, Any]:
    from r2r import R2RAsyncClient, R2RClient, get_version
    from r2r.serve import create_app, run_server

    return {
        "version": get_version(),
        "python_client": _callable_signature(R2RClient),
        "python_async_client": _callable_signature(R2RAsyncClient),
        "create_app": _callable_signature(create_app),
        "run_server": _callable_signature(run_server),
    }

def _probe_health(base_url: str) -> dict[str, Any]:
    request = Request(base_url.rstrip("/") + "/v3/health")
    with urlopen(request, timeout=10) as response:
        payload = response.read().decode("utf-8", errors="replace")
        return {
            "status": getattr(response, "status", response.getcode()),
            "body": payload,
        }

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect the public R2R Python surface and optionally probe a live health endpoint.",
    )
    parser.add_argument(
        "--base-url",
        help="Optional server base URL such as http://localhost:7272.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a human summary.",
    )
    args = parser.parse_args()

    report: dict[str, Any] = {"imports": _probe_imports()}
    if args.base_url:
        try:
            report["health"] = _probe_health(args.base_url)
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            report["health_error"] = str(exc)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"r2r {report['imports']['version']}")
        print(f"R2RClient: {report['imports']['python_client']}")
        print(f"R2RAsyncClient: {report['imports']['python_async_client']}")
        print(f"create_app: {report['imports']['create_app']}")
        print(f"run_server: {report['imports']['run_server']}")
        if "health" in report:
            print(f"health status: {report['health']['status']}")
        elif "health_error" in report:
            print(f"health probe failed: {report['health_error']}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
