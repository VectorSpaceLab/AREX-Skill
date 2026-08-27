#!/usr/bin/env python3
"""In-process smoke test for Opyrator FastAPI services.

This helper builds a tiny wrapped function, creates the FastAPI app in-process,
inspects the route set and OpenAPI metadata, and reports relative-doc behavior.
It never launches uvicorn or touches the network.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List


def _dependency_hint(exc: Exception) -> str:
    message = f"{exc.__class__.__name__}: {exc}"
    if "graphql" in message or "starlette.graphql" in message:
        return (
            message
            + " | This stack expects the repo-pinned FastAPI/Starlette pair; "
            "newer Starlette releases remove starlette.graphql."
        )
    if isinstance(exc, ModuleNotFoundError):
        return (
            message
            + " | Install the package and its FastAPI testing dependencies before "
            "running this smoke helper."
        )
    return message


def _schema_ref(schema: Dict[str, Any]) -> str:
    ref = schema.get("$ref")
    if ref:
        return ref
    if schema.get("type") == "array" and isinstance(schema.get("items"), dict):
        return f"array({_schema_ref(schema['items'])})"
    if "type" in schema:
        return str(schema["type"])
    return json.dumps(schema, sort_keys=True)


def build_report() -> Dict[str, Any]:
    try:
        from pydantic import create_model
        from opyrator import Opyrator
        from opyrator.api import create_api
    except Exception as exc:  # pragma: no cover - exercised only when deps are missing
        raise RuntimeError(
            "Unable to import the Opyrator FastAPI surface. " + _dependency_hint(exc)
        ) from exc

    smoke_input = create_model("SmokeInput", message=(str, ...))
    smoke_output = create_model("SmokeOutput", message=(str, ...))
    globals()["SmokeInput"] = smoke_input
    globals()["SmokeOutput"] = smoke_output

    def echo(input: SmokeInput) -> SmokeOutput:
        return SmokeOutput(message=input.message)

    try:
        app = create_api(Opyrator(echo))
    except Exception as exc:  # pragma: no cover - exercised only on incompatible installs
        raise RuntimeError(
            "Failed to build the FastAPI app from a tiny compatible callable. "
            "The callable must accept `input` and return a Pydantic-compatible output. "
            + _dependency_hint(exc)
        ) from exc

    schema = app.openapi()
    call_operation = schema["paths"]["/call"]["post"]

    report: Dict[str, Any] = {
        "title": app.title,
        "description": app.description,
        "route_map": [],
        "openapi_title": schema.get("info", {}).get("title"),
        "openapi_version": schema.get("info", {}).get("version"),
        "openapi_paths": sorted(schema.get("paths", {}).keys()),
        "call_request_ref": _schema_ref(
            call_operation["requestBody"]["content"]["application/json"]["schema"]
        ),
        "call_response_ref": _schema_ref(
            call_operation["responses"]["200"]["content"]["application/json"]["schema"]
        ),
        "component_schemas": sorted(schema.get("components", {}).get("schemas", {}).keys()),
        "client_checks": {"available": False},
    }

    for route in app.routes:
        path = getattr(route, "path", None)
        if not path:
            continue
        methods = sorted(getattr(route, "methods", []) or [])
        report["route_map"].append({"path": path, "methods": methods})
    report["route_map"].sort(key=lambda item: (item["path"], item["methods"]))

    try:
        from fastapi.testclient import TestClient
    except Exception as exc:
        report["client_checks"] = {
            "available": False,
            "error": "TestClient unavailable: " + _dependency_hint(exc),
        }
        return report

    try:
        client = TestClient(app)
        root = client.get("/", allow_redirects=False)
        docs = client.get("/docs")
        redoc = client.get("/redoc")
        call = client.post("/call", json={"message": "smoke"})
    except Exception as exc:
        report["client_checks"] = {
            "available": False,
            "error": "Client check failed: " + _dependency_hint(exc),
        }
        return report

    report["client_checks"] = {
        "available": True,
        "root_status": root.status_code,
        "root_location": root.headers.get("location"),
        "docs_status": docs.status_code,
        "docs_relative_openapi_url": "./openapi.json" in docs.text,
        "redoc_status": redoc.status_code,
        "redoc_relative_openapi_url": "./openapi.json" in redoc.text,
        "call_status": call.status_code,
        "call_json": call.json(),
    }
    return report


def emit(report: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    print("Opyrator FastAPI smoke report")
    print(f"title: {report['title']}")
    print(f"openapi: {report['openapi_title']} ({report['openapi_version']})")
    print("routes: " + ", ".join(item["path"] for item in report["route_map"]))
    print(f"/call request: {report['call_request_ref']}")
    print(f"/call response: {report['call_response_ref']}")

    client = report.get("client_checks", {})
    if client.get("available"):
        print(f"root redirect: {client['root_status']} -> {client['root_location']}")
        print(f"docs relative openapi: {client['docs_relative_openapi_url']}")
        print(f"redoc relative openapi: {client['redoc_relative_openapi_url']}")
        print(f"call response: {client['call_status']} {client['call_json']}")
    else:
        print(f"client checks skipped: {client.get('error', 'unavailable')}")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Smoke-test Opyrator FastAPI service creation in-process."
    )
    parser.add_argument("--json", action="store_true", help="Print a machine-readable report.")
    args = parser.parse_args(argv)

    try:
        report = build_report()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    emit(report, args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
