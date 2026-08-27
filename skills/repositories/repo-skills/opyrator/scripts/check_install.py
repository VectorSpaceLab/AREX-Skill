#!/usr/bin/env python3
"""Safe install-and-smoke helper for the Opyrator snapshot.

This helper does not launch a long-running service. It verifies that the package,
CLI entry point, core wrapper, FastAPI app creation, schema utilities, and
FileContent round-tripping all work in the active Python environment.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any, Dict, List


def _tiny_report() -> Dict[str, Any]:
    from pydantic import BaseModel, Field

    from opyrator import Opyrator
    from opyrator.api.fastapi_app import create_api
    from opyrator.components.types import FileContent
    from opyrator.ui import schema_utils

    class Input(BaseModel):
        message: str = Field(..., max_length=20)

    class Output(BaseModel):
        message: str

    globals()["Input"] = Input
    globals()["Output"] = Output

    def hello_world(input: Input) -> Output:
        """Echo the message back to the caller."""
        return Output(message=input.message)

    wrapped = Opyrator(hello_world)
    app = create_api(wrapped)
    routes = sorted({getattr(route, "path", "") for route in app.routes if getattr(route, "path", None)})
    payload = FileContent.validate(b"opyrator-smoke")

    try:
        from fastapi.testclient import TestClient

        client = TestClient(app)
        root = client.get("/", allow_redirects=False)
        docs = client.get("/docs")
        call = client.post("/call", json={"message": "smoke"})
        client_result = {
            "available": True,
            "root_status": root.status_code,
            "root_location": root.headers.get("location"),
            "docs_relative_openapi": "./openapi.json" in docs.text,
            "call_status": call.status_code,
            "call_json": call.json(),
        }
    except Exception as exc:  # pragma: no cover - environment-specific fallback
        client_result = {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    return {
        "package_version": __import__("opyrator").__version__,
        "wrapped_name": wrapped.name,
        "wrapped_description": wrapped.description,
        "wrapped_call": wrapped({"message": "smoke"}).message,
        "routes": routes,
        "filecontent_round_trip": payload.as_bytes() == b"opyrator-smoke",
        "schema_string": schema_utils.is_single_string_property(Input.schema()["properties"]["message"]),
        "client_result": client_result,
    }


def _check_cli() -> Dict[str, Any]:
    command = "opyrator"
    if not command:
        return {"available": False, "error": "console script not configured"}

    try:
        proc = subprocess.run(
            [command, "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return {
            "available": False,
            "error": "console script `opyrator` not found on PATH; reinstall the package or use `python -m pip install -e .`",
        }

    return {
        "available": True,
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "help_ok": proc.returncode == 0 and "Usage: opyrator" in proc.stdout,
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the installed Opyrator package and CLI entry point.")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    args = parser.parse_args(argv)

    try:
        import opyrator  # noqa: F401
    except Exception as exc:
        payload = {
            "status": "error",
            "error_type": type(exc).__name__,
            "error": f"Unable to import opyrator: {exc}",
        }
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else json.dumps(payload, indent=2, sort_keys=True))
        return 2

    try:
        report = _tiny_report()
    except Exception as exc:
        payload = {
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else json.dumps(payload, indent=2, sort_keys=True))
        return 2

    report["cli_help"] = _check_cli()
    report["status"] = (
        "ok"
        if report["filecontent_round_trip"]
        and report["schema_string"]
        and report["wrapped_call"] == "smoke"
        and report["client_result"].get("available")
        and report["client_result"].get("call_status") == 200
        and report["cli_help"].get("help_ok")
        else "failed"
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Opyrator install check:", report["status"])
        print("Version:", report["package_version"])
        print("Routes:", ", ".join(report["routes"]))
        print("CLI help ok:", report["cli_help"].get("help_ok"))

    return 0 if report["status"] == "ok" and report["cli_help"].get("help_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
