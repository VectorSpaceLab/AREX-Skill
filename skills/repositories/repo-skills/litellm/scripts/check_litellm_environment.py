#!/usr/bin/env python3
"""Check LiteLLM import, version, core API signatures, and optional proxy CLI availability."""

from __future__ import annotations

import argparse
import importlib.metadata
import inspect
import json
import sys
from typing import Any


def _signature(target: Any) -> str:
    try:
        return str(inspect.signature(target))
    except Exception as exc:
        return f"unavailable: {type(exc).__name__}: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a LiteLLM Python environment without making provider calls.")
    parser.add_argument("--check-proxy-cli", action="store_true", help="Also import the proxy CLI and verify help text is available.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    result: dict[str, Any] = {"ok": False, "checks": {}}
    try:
        import litellm
        from litellm import Router
    except Exception as exc:
        result["error"] = f"LiteLLM import failed: {type(exc).__name__}: {exc}"
        print(json.dumps(result, indent=2) if args.json else result["error"])
        return 1

    result["checks"]["distribution_version"] = importlib.metadata.version("litellm")
    result["checks"]["module_version"] = getattr(litellm, "__version__", None)
    result["checks"]["completion_signature"] = _signature(litellm.completion)
    result["checks"]["acompletion_signature"] = _signature(litellm.acompletion)
    result["checks"]["embedding_signature"] = _signature(litellm.embedding)
    result["checks"]["router_init_signature"] = _signature(Router.__init__)

    if args.check_proxy_cli:
        try:
            from click.testing import CliRunner
            from litellm.proxy.proxy_cli import run_server

            cli_result = CliRunner().invoke(run_server, ["--help"])
            result["checks"]["proxy_cli_help_exit_code"] = cli_result.exit_code
            result["checks"]["proxy_cli_has_model_flag"] = "--model" in cli_result.output
            result["checks"]["proxy_cli_has_config_flag"] = "--config" in cli_result.output
        except Exception as exc:
            result["checks"]["proxy_cli_error"] = f"{type(exc).__name__}: {exc}"
            print(json.dumps(result, indent=2) if args.json else result["checks"]["proxy_cli_error"])
            return 1

    result["ok"] = True
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"LiteLLM distribution: {result['checks']['distribution_version']}")
        print("Core imports and signatures are available.")
        if args.check_proxy_cli:
            print("Proxy CLI help is available.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
