#!/usr/bin/env python3
"""Probe AutoTrain FastAPI app routes and training API route registration safely.

The main UI app can be checked with FastAPI TestClient. The training API has a
lifespan hook that starts training, so this helper inspects its registered
routes without issuing requests to that app.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any


def check_client(client: Any, method: str, path: str, expected_statuses: set[int]) -> dict[str, Any]:
    response = getattr(client, method.lower())(path)
    payload: dict[str, Any] = {
        "method": method,
        "path": path,
        "status_code": response.status_code,
        "expected_statuses": sorted(expected_statuses),
        "ok": response.status_code in expected_statuses,
    }
    try:
        payload["json"] = response.json()
    except Exception:
        payload["text"] = response.text[:200]
    location = response.headers.get("location")
    if location:
        payload["location"] = location
    return payload


def main() -> int:
    try:
        from fastapi.testclient import TestClient
        from autotrain.app.app import app
    except Exception as exc:  # pragma: no cover - environment triage
        print(f"ERROR: failed to import main FastAPI app: {exc!r}", file=sys.stderr)
        return 1

    main_client = TestClient(app, follow_redirects=False)
    checks = [
        check_client(main_client, "GET", "/", {307, 308}),
        check_client(main_client, "GET", "/api/version", {200}),
    ]

    training_route_check: dict[str, Any]
    try:
        # training_api imports TASK_ID as int at module import time. Provide a
        # harmless default for route inspection only. Do not request this app:
        # its lifespan hook starts training.
        os.environ.setdefault("TASK_ID", "0")
        from autotrain.app.training_api import api

        route_paths = sorted({getattr(route, "path", "") for route in api.routes})
        training_route_check = {
            "method": "ROUTE_INSPECTION",
            "path": "autotrain.app.training_api:api",
            "routes": route_paths,
            "ok": "/" in route_paths and "/health" in route_paths,
            "note": "Requests are intentionally not issued because the training API lifespan starts training.",
        }
    except Exception as exc:  # pragma: no cover - environment triage
        training_route_check = {
            "method": "ROUTE_INSPECTION",
            "path": "autotrain.app.training_api:api",
            "ok": False,
            "error": repr(exc),
        }

    checks.append(training_route_check)
    payload = {"ok": all(item["ok"] for item in checks), "checks": checks}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
