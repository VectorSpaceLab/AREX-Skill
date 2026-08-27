#!/usr/bin/env python3
"""Safe SamGeo API smoke check.

With no --base-url, uses FastAPI TestClient against the installed app and calls
/health and /models without loading model weights. With --base-url, probes a
running server using HTTP GET requests.
"""

from __future__ import annotations

import argparse
import json
import urllib.request


def probe_http(base_url: str) -> dict:
    base = base_url.rstrip("/")
    result = {}
    for path in ["/health", "/models"]:
        with urllib.request.urlopen(base + path, timeout=10) as response:  # noqa: S310 - user-supplied local/admin diagnostic URL
            body = response.read().decode("utf-8")
            result[path] = {"status": response.status, "json": json.loads(body)}
    return result


def probe_local() -> dict:
    from fastapi.testclient import TestClient
    from samgeo.api import app

    client = TestClient(app)
    result = {}
    for path in ["/health", "/models"]:
        response = client.get(path)
        result[path] = {"status": response.status_code, "json": response.json()}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", help="Probe a running server instead of local TestClient, e.g. http://localhost:8000")
    parser.add_argument("--local-testclient", action="store_true", help="Force local TestClient mode (default when --base-url is absent).")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    try:
        result = probe_http(args.base_url) if args.base_url else probe_local()
    except Exception as exc:  # noqa: BLE001
        result = {"error": f"{type(exc).__name__}: {exc}"}
        ok = False
    else:
        ok = all(item["status"] == 200 for item in result.values())

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("SamGeo API smoke result:")
        for key, value in result.items():
            print(f"  {key}: {value}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
