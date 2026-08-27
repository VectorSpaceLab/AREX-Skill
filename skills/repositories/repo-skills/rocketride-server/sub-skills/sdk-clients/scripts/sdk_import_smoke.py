#!/usr/bin/env python3
"""Safe RocketRide Python SDK import/signature smoke check.

This script performs local imports and method-signature inspection only. It does
not instantiate network transports, open WebSockets, start an engine, call Cloud,
or read any RocketRide repository checkout.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from importlib import import_module, metadata
from typing import Any

REQUIRED_CLIENT_METHODS = [
    "connect",
    "disconnect",
    "use",
    "send",
    "send_files",
    "pipe",
    "chat",
    "validate",
    "terminate",
    "get_task_status",
    "get_services",
    "get_service",
    "set_events",
    "fs_open",
    "fs_read",
    "fs_write",
    "fs_close",
    "fs_delete",
    "fs_list_dir",
    "fs_mkdir",
    "fs_rmdir",
    "fs_stat",
    "fs_rename",
    "fs_get_url",
    "fs_read_many",
    "fs_read_string",
    "fs_write_string",
    "fs_read_json",
    "fs_write_json",
]

OPTIONAL_CLIENT_METHODS = [
    "attach",
    "detach",
    "login",
    "logout",
    "is_attached",
    "is_authenticated",
    "is_connected",
    "get_connection_info",
    "get_apikey",
    "set_env",
    "ping",
    "call",
    "tool",
    "build_request",
    "request",
    "dap_request",
    "did_fail",
    "get_task_token",
    "get_task_pipeline",
]

REQUIRED_PUBLIC_SYMBOLS = [
    "RocketRideClient",
    "Question",
    "Answer",
    "AuthenticationException",
]


def _signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:  # pragma: no cover - diagnostic path
        return f"<signature unavailable: {exc}>"


def run_smoke() -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": False,
        "package": "rocketride",
        "version": None,
        "public_symbols": {},
        "client_signatures": {},
        "datapipe_signatures": {},
        "missing_required": [],
        "warnings": [],
    }

    try:
        rocketride = import_module("rocketride")
    except Exception as exc:
        result["error"] = f"failed to import rocketride: {exc}"
        return result

    try:
        result["version"] = metadata.version("rocketride")
    except Exception:
        result["version"] = getattr(rocketride, "__version__", "") or None
        result["warnings"].append("package metadata version unavailable")

    for name in REQUIRED_PUBLIC_SYMBOLS:
        obj = getattr(rocketride, name, None)
        result["public_symbols"][name] = bool(obj)
        if obj is None:
            result["missing_required"].append(f"rocketride.{name}")

    client_cls = getattr(rocketride, "RocketRideClient", None)
    if client_cls is None:
        return result

    result["client_signatures"]["__init__"] = _signature(client_cls.__init__)
    for name in REQUIRED_CLIENT_METHODS + OPTIONAL_CLIENT_METHODS:
        method = getattr(client_cls, name, None)
        if method is None:
            if name in REQUIRED_CLIENT_METHODS:
                result["missing_required"].append(f"RocketRideClient.{name}")
            else:
                result["warnings"].append(f"optional method missing: RocketRideClient.{name}")
            continue
        result["client_signatures"][name] = _signature(method)

    try:
        data_module = import_module("rocketride.mixins.data")
        data_pipe = data_module.DataMixin.DataPipe
        for name in ["open", "write", "close", "tool", "__aenter__", "__aexit__"]:
            method = getattr(data_pipe, name, None)
            if method is None:
                result["warnings"].append(f"DataPipe.{name} missing")
            else:
                result["datapipe_signatures"][name] = _signature(method)
    except Exception as exc:
        result["warnings"].append(f"DataPipe inspection skipped: {exc}")

    result["ok"] = not result["missing_required"]
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import and inspect RocketRide Python SDK signatures without connecting.")
    parser.add_argument("--json", action="store_true", help="emit structured JSON output")
    args = parser.parse_args(argv)

    result = run_smoke()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"RocketRide SDK import smoke: {'OK' if result['ok'] else 'FAILED'}")
        print(f"package: {result['package']} version={result.get('version') or '<unknown>'}")
        if result.get("error"):
            print(f"error: {result['error']}")
        if result["missing_required"]:
            print("missing required:")
            for item in result["missing_required"]:
                print(f"  - {item}")
        print("client signatures:")
        for name in sorted(result["client_signatures"]):
            print(f"  RocketRideClient.{name}{result['client_signatures'][name]}")
        if result["datapipe_signatures"]:
            print("DataPipe signatures:")
            for name in sorted(result["datapipe_signatures"]):
                print(f"  DataPipe.{name}{result['datapipe_signatures'][name]}")
        if result["warnings"]:
            print("warnings:")
            for item in result["warnings"]:
                print(f"  - {item}")

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
