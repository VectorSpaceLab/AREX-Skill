#!/usr/bin/env python3
"""Probe OpenMed CLI, service, MCP, and interop imports safely.

The script never starts a long-lived listener and never calls external
services. It is intended for local smoke checks and troubleshooting. It runs
help/version probes for the OpenMed console scripts, falling back to module
execution when a console script is unavailable, and it can optionally import
service and registry surfaces without making any network calls.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

DEFAULT_TIMEOUT_SECONDS = 20.0
_EXCERPT_CHARS = 3000


def _excerpt(text: str, *, limit: int = _EXCERPT_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n… <truncated {len(text) - limit} chars>"


def _probe_subprocess(
    *,
    label: str,
    console_command: str,
    module_name: str,
    args: list[str],
    timeout: float,
) -> dict[str, Any]:
    env_bin = Path(sys.executable).resolve().parent
    env_console = env_bin / console_command
    if shutil.which(console_command):
        command = [console_command, *args]
        invocation = "console"
    elif env_console.exists() and os.access(env_console, os.X_OK):
        command = [str(env_console), *args]
        invocation = "env"
    else:
        command = [
            sys.executable,
            "-W",
            "ignore::RuntimeWarning",
            "-m",
            module_name,
            *args,
        ]
        invocation = "module"

    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return {
            "label": label,
            "ok": False,
            "invocation": invocation,
            "command": command,
            "error": {
                "type": exc.__class__.__name__,
                "message": str(exc),
            },
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "label": label,
            "ok": False,
            "invocation": invocation,
            "command": command,
            "error": {
                "type": exc.__class__.__name__,
                "message": f"timed out after {timeout} seconds",
            },
            "stdout_excerpt": _excerpt(exc.stdout or ""),
            "stderr_excerpt": _excerpt(exc.stderr or ""),
        }

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    ok = completed.returncode == 0
    payload: dict[str, Any] = {
        "label": label,
        "ok": ok,
        "invocation": invocation,
        "command": command,
        "returncode": completed.returncode,
        "stdout_lines": len(stdout.splitlines()),
        "stderr_lines": len(stderr.splitlines()),
        "stdout_excerpt": _excerpt(stdout),
        "stderr_excerpt": _excerpt(stderr),
    }
    if not ok:
        payload["error"] = {
            "type": "CalledProcessError",
            "message": f"{console_command} {' '.join(args)} exited with {completed.returncode}",
        }
    return payload


def _probe_import(label: str, loader: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        details = loader()
        return {
            "label": label,
            "ok": True,
            **details,
        }
    except Exception as exc:  # noqa: BLE001 - diagnostic probe
        return {
            "label": label,
            "ok": False,
            "error": {
                "type": exc.__class__.__name__,
                "message": str(exc),
            },
        }


def _probe_service_app() -> dict[str, Any]:
    from openmed.service.app import create_app

    app = create_app()
    return {
        "module": "openmed.service.app",
        "factory": "create_app",
        "app_type": type(app).__name__,
        "title": getattr(app, "title", None),
        "route_count": len(getattr(app, "routes", ())),
    }


def _probe_service_client() -> dict[str, Any]:
    from openmed.service.client import OpenMedClient

    with OpenMedClient() as client:
        return {
            "module": "openmed.service.client",
            "class": type(client).__name__,
            "created": True,
        }


def _probe_tool_registry() -> dict[str, Any]:
    from openmed.mcp.tool_registry import TOOL_REGISTRY

    specs = TOOL_REGISTRY.latest_specs()
    return {
        "module": "openmed.mcp.tool_registry",
        "tool_count": len(specs),
        "tool_names": [spec.name for spec in specs[:10]],
    }


def _probe_interop_registry() -> dict[str, Any]:
    from openmed.interop import available_adapters

    adapters = available_adapters(include_plugins=False)
    return {
        "module": "openmed.interop",
        "adapter_count": len(adapters),
        "adapters": list(adapters[:10]),
    }


def _probe_grpc_module() -> dict[str, Any]:
    from openmed.service import grpc_server

    return {
        "module": "openmed.service.grpc_server",
        "default_address": getattr(grpc_server, "DEFAULT_GRPC_ADDRESS", None),
        "has_create_grpc_server": hasattr(grpc_server, "create_grpc_server"),
        "has_serve": hasattr(grpc_server, "serve"),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Timeout in seconds for each CLI probe.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the JSON summary to this file as well as stdout.",
    )
    parser.add_argument(
        "--no-cli",
        action="store_true",
        help="Skip the openmed and openmed-mcp help/version probes.",
    )
    parser.add_argument(
        "--no-imports",
        action="store_true",
        help="Skip the service, client, registry, and adapter imports.",
    )
    parser.add_argument(
        "--probe-grpc",
        action="store_true",
        help="Also import the gRPC service module without starting it.",
    )
    return parser


def run(args: argparse.Namespace) -> dict[str, Any]:
    cli_results: list[dict[str, Any]] = []
    import_results: dict[str, dict[str, Any]] = {}

    if not args.no_cli:
        cli_results.append(
            _probe_subprocess(
                label="openmed help",
                console_command="openmed",
                module_name="openmed.cli.main",
                args=["--help"],
                timeout=args.timeout,
            )
        )
        cli_results.append(
            _probe_subprocess(
                label="openmed version",
                console_command="openmed",
                module_name="openmed.cli.main",
                args=["--version"],
                timeout=args.timeout,
            )
        )
        cli_results.append(
            _probe_subprocess(
                label="openmed-mcp help",
                console_command="openmed-mcp",
                module_name="openmed.mcp.server",
                args=["--help"],
                timeout=args.timeout,
            )
        )
        cli_results.append(
            _probe_subprocess(
                label="openmed-mcp version",
                console_command="openmed-mcp",
                module_name="openmed.mcp.server",
                args=["--version"],
                timeout=args.timeout,
            )
        )

    if not args.no_imports:
        import_results["service_app"] = _probe_import(
            "service app",
            _probe_service_app,
        )
        import_results["service_client"] = _probe_import(
            "service client",
            _probe_service_client,
        )
        import_results["tool_registry"] = _probe_import(
            "tool registry",
            _probe_tool_registry,
        )
        import_results["interop_registry"] = _probe_import(
            "interop registry",
            _probe_interop_registry,
        )
        if args.probe_grpc:
            import_results["grpc_module"] = _probe_import(
                "grpc module",
                _probe_grpc_module,
            )

    cli_passed = sum(1 for item in cli_results if item.get("ok"))
    cli_failed = len(cli_results) - cli_passed
    import_passed = sum(1 for item in import_results.values() if item.get("ok"))
    import_failed = len(import_results) - import_passed

    summary = {
        "cli_passed": cli_passed,
        "cli_failed": cli_failed,
        "imports_passed": import_passed,
        "imports_failed": import_failed,
        "overall_ok": cli_failed == 0 and import_failed == 0,
    }

    return {
        "python": sys.version,
        "executable": sys.executable,
        "cli": cli_results,
        "imports": import_results,
        "summary": summary,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = run(args)
    rendered = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")

    print(rendered)
    return 0 if payload["summary"]["overall_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
