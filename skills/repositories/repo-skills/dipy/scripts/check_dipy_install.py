#!/usr/bin/env python3
"""Safe Dipy installation and CLI-flow probe.

The script performs import and metadata checks only. It does not download data,
run image workflows, open visualization windows, or require the original source
repository.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import sys


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Dipy import, version, CLI-flow, and optional dependency status.")
    parser.add_argument("--format", choices=("json", "text"), default="json", help="Output format.")
    parser.add_argument("--expect-min-flows", type=int, default=50, help="Minimum CLI flow count expected for a full Dipy install.")
    return parser.parse_args(argv)


def probe_optional(names: list[str]) -> dict[str, bool]:
    status: dict[str, bool] = {}
    for name in names:
        try:
            importlib.import_module(name)
        except Exception:
            status[name] = False
        else:
            status[name] = True
    return status


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result: dict[str, object] = {
        "ok": False,
        "import_ok": False,
        "metadata_ok": False,
        "cli_flows_ok": False,
        "optional_dependencies": {},
        "warnings": [],
    }

    try:
        dipy = importlib.import_module("dipy")
        result["import_ok"] = True
        result["dipy_version"] = getattr(dipy, "__version__", "unknown")
    except Exception as exc:
        result["error"] = f"Could not import dipy: {type(exc).__name__}: {exc}"
        result["warnings"].append("If this happens only inside a source checkout, run from outside the checkout or use a normal installed Dipy package.")
        print(json.dumps(result, indent=2, sort_keys=True) if args.format == "json" else result["error"])
        return 1

    try:
        result["distribution_version"] = metadata.version("dipy")
        result["metadata_ok"] = True
    except Exception as exc:
        result["warnings"].append(f"Could not read Dipy distribution metadata: {type(exc).__name__}: {exc}")

    try:
        from dipy.workflows.cli import cli_flows

        result["cli_flow_count"] = len(cli_flows)
        result["cli_flows_ok"] = len(cli_flows) >= args.expect_min_flows
        result["sample_cli_flows"] = sorted(cli_flows)[:12]
        if not result["cli_flows_ok"]:
            result["warnings"].append("CLI flow count is lower than expected; verify the installed package and entry points.")
    except Exception as exc:
        result["warnings"].append(f"Could not inspect Dipy CLI flows: {type(exc).__name__}: {exc}")

    result["optional_dependencies"] = probe_optional(["fury", "matplotlib", "sklearn", "torch", "tensorflow"])
    result["ok"] = bool(result["import_ok"] and result["metadata_ok"] and result["cli_flows_ok"])

    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Dipy install probe")
        print(f"ok: {result['ok']}")
        print(f"dipy version: {result.get('dipy_version', 'unknown')}")
        print(f"distribution version: {result.get('distribution_version', 'unknown')}")
        print(f"cli flow count: {result.get('cli_flow_count', 'unknown')}")
        print("optional dependencies:")
        for name, available in sorted(result["optional_dependencies"].items()):
            print(f"  {name}: {'available' if available else 'missing'}")
        for warning in result["warnings"]:
            print(f"warning: {warning}")

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
