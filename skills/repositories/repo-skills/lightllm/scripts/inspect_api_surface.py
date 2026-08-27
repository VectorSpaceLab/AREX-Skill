#!/usr/bin/env python3
"""Inspect the LightLLM HTTP surface from the installed package."""

from __future__ import annotations

import argparse
import inspect
import json
from importlib.metadata import PackageNotFoundError, version


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args()

    try:
        import lightllm
        from lightllm.server import api_http, api_models
        from lightllm.server.api_cli import add_cli_args
        from lightllm.server.api_server import launch_server
        from lightllm.server.core.objs.start_args_type import StartArgs
    except Exception as exc:
        payload = {"ok": False, "error": str(exc)}
        print(json.dumps(payload, indent=2) if args.json else payload["error"])
        return 1

    try:
        pkg_version = version("lightllm")
    except PackageNotFoundError:
        pkg_version = getattr(lightllm, "__version__", None)

    routes = []
    for route in api_http.app.routes:
        path = getattr(route, "path", None)
        if not path:
            continue
        methods = sorted(m for m in getattr(route, "methods", []) or [] if m)
        routes.append({"path": path, "methods": methods, "name": getattr(route, "name", None)})

    request_signatures = {}
    for name in ["CompletionRequest", "ChatCompletionRequest", "ResponseFormat", "ToolChoice", "Tool", "Message"]:
        obj = getattr(api_models, name, None)
        if obj is not None:
            try:
                request_signatures[name] = str(inspect.signature(obj))
            except Exception:
                request_signatures[name] = "<no signature>"

    info = {
        "lightllm_version": pkg_version,
        "launch_server": str(inspect.signature(launch_server)),
        "add_cli_args": str(inspect.signature(add_cli_args)),
        "start_args": str(inspect.signature(StartArgs)),
        "routes": routes,
        "schema_signatures": request_signatures,
    }

    if args.json:
        print(json.dumps(info, indent=2, sort_keys=True, default=str))
    else:
        print(f"lightllm_version={pkg_version}")
        print(f"launch_server={info['launch_server']}")
        print(f"add_cli_args={info['add_cli_args']}")
        print(f"start_args={info['start_args']}")
        for route in routes:
            methods = ",".join(route["methods"])
            print(f"{methods:>12} {route['path']}")
        for name, sig in request_signatures.items():
            print(f"{name}={sig}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
