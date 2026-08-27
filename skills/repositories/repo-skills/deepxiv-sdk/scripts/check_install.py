#!/usr/bin/env python3
"""No-network DeepXiv installation and optional-feature check.

The helper imports the installed package, inspects the public CLI registry, and
reports whether the optional local-agent modules are available. It deliberately
disables python-dotenv loading and never makes service or credential calls.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from importlib.metadata import PackageNotFoundError, version


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check DeepXiv installation without network access.")
    parser.add_argument("--require-agent", action="store_true", help="fail when optional Agent imports are unavailable")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    os.environ["PYTHON_DOTENV_DISABLED"] = "1"

    report: dict[str, object] = {"network_requests": 0}
    try:
        report["distribution_version"] = version("deepxiv-sdk")
    except PackageNotFoundError:
        report["status"] = "distribution_missing"
        report["message"] = "Install deepxiv-sdk in the interpreter running this helper."
        print(json.dumps(report, sort_keys=True))
        return 1

    try:
        package = importlib.import_module("deepxiv_sdk")
        cli = importlib.import_module("deepxiv_sdk.cli")
        report["package_version"] = getattr(package, "__version__", None)
        report["reader_import"] = hasattr(package, "Reader")
        report["cli_commands"] = sorted(getattr(cli.main, "commands", {}).keys())
        report["cli_version"] = str(cli.main)
    except Exception as exc:
        report["status"] = "import_error"
        report["error"] = f"{type(exc).__name__}: {exc}"
        print(json.dumps(report, sort_keys=True))
        return 1

    optional_modules = ("openai", "langgraph", "langchain_core", "tiktoken")
    missing: list[str] = []
    for module_name in optional_modules:
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append(module_name)
    agent_exported = hasattr(package, "Agent") and "Agent" in getattr(package, "__all__", [])
    report["optional_agent_modules"] = {name: name not in missing for name in optional_modules}
    report["agent_exported"] = agent_exported
    agent_ready = not missing and agent_exported
    report["status"] = "ok" if agent_ready or not args.require_agent else "optional_agent_missing"
    if missing or (args.require_agent and not agent_exported):
        report["missing_agent_modules"] = missing
        report["next_step"] = 'Install "deepxiv-sdk[agent]" (or [all]) and install tiktoken separately when needed.'

    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
