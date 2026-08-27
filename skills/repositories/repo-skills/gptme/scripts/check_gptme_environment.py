#!/usr/bin/env python3
"""Check an installed gptme runtime without making network, model, or browser calls.

Examples:
  python check_gptme_environment.py
  python check_gptme_environment.py --json --check-server-app
  python check_gptme_environment.py --require gptme --require gptme.server.app
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata
from typing import Any

EXPECTED_CONSOLE_SCRIPTS = {
    "gptme",
    "gptme-util",
    "gptme-server",
    "gptme-acp",
    "gptme-agent",
    "gptme-eval",
    "gptme-eval-swebench",
    "gptme-eval-tbench",
    "gptme-auth",
    "gptme-doctor",
    "gptme-mcp-server",
    "gptme-tui",
}

DEFAULT_IMPORTS = [
    "gptme",
    "gptme.cli.main",
    "gptme.config",
    "gptme.llm",
    "gptme.tools",
    "gptme.plugins.registry",
    "gptme.hooks.registry",
    "gptme.mcp.client",
]

OPTIONAL_IMPORTS = {
    "server": "gptme.server.app",
    "acp": "gptme.acp.agent",
    "tui": "gptme.tui.main",
    "eval": "gptme.eval.main",
    "agent": "gptme.agent.cli",
}


def import_status(module: str) -> dict[str, str]:
    try:
        importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        return {"module": module, "status": "fail", "error": f"{type(exc).__name__}: {exc}"}
    return {"module": module, "status": "ok"}


def distribution_status() -> dict[str, Any]:
    try:
        dist = metadata.distribution("gptme")
    except metadata.PackageNotFoundError:
        return {
            "status": "fail",
            "error": "The gptme distribution is not installed in this Python environment.",
            "version": None,
            "console_scripts": [],
            "missing_expected_console_scripts": sorted(EXPECTED_CONSOLE_SCRIPTS),
        }

    scripts = sorted(
        ep.name for ep in dist.entry_points if ep.group == "console_scripts"
    )
    missing = sorted(EXPECTED_CONSOLE_SCRIPTS.difference(scripts))
    return {
        "status": "ok",
        "version": dist.version,
        "console_scripts": scripts,
        "missing_expected_console_scripts": missing,
    }


def server_app_status() -> dict[str, Any]:
    try:
        from gptme.server.app import create_app

        app = create_app(host="127.0.0.1", cors_origin=None, default_profile=None)
        rules = sorted(str(rule) for rule in app.url_map.iter_rules())
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        return {"status": "fail", "error": f"{type(exc).__name__}: {exc}"}
    return {
        "status": "ok",
        "route_count": len(rules),
        "has_api_v2": any(rule.startswith("/api/v2") for rule in rules),
        "has_static_root": "/" in rules,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    modules = list(dict.fromkeys(DEFAULT_IMPORTS + list(args.require)))
    optional = {name: import_status(module) for name, module in OPTIONAL_IMPORTS.items()}
    report: dict[str, Any] = {
        "distribution": distribution_status(),
        "imports": [import_status(module) for module in modules],
        "optional_imports": optional,
    }
    if args.check_server_app:
        report["server_app"] = server_app_status()
    failures = []
    dist = report["distribution"]
    if dist.get("status") != "ok" or dist.get("missing_expected_console_scripts"):
        failures.append("distribution-or-entrypoints")
    failures.extend(item["module"] for item in report["imports"] if item["status"] != "ok")
    if args.check_server_app and report.get("server_app", {}).get("status") != "ok":
        failures.append("server-app")
    report["status"] = "ok" if not failures else "fail"
    report["failures"] = failures
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require",
        action="append",
        default=[],
        help="Additional import module to require; may be repeated.",
    )
    parser.add_argument(
        "--check-server-app",
        action="store_true",
        help="Construct the Flask app and verify route registration. Does not start a server.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        dist = report["distribution"]
        print(f"gptme distribution: {dist.get('status')} version={dist.get('version')}")
        missing = dist.get("missing_expected_console_scripts") or []
        print(f"console scripts: {len(dist.get('console_scripts') or [])}; missing expected: {', '.join(missing) if missing else 'none'}")
        for item in report["imports"]:
            line = f"import {item['module']}: {item['status']}"
            if item["status"] != "ok":
                line += f" ({item['error']})"
            print(line)
        for name, item in report["optional_imports"].items():
            suffix = f" ({item.get('error')})" if item["status"] != "ok" else ""
            print(f"optional {name}: {item['status']}{suffix}")
        if "server_app" in report:
            print(f"server app: {report['server_app']}")
        print(f"overall: {report['status']}")
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
