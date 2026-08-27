#!/usr/bin/env python3
"""Check a local mcp-agent environment without network or credential use.

The checker verifies the base import, selected optional extras/imports, CLI
executables, and bundled helper paths. It never calls providers, starts servers,
deploys to Cloud, or reads secret values.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
from pathlib import Path

OPTIONAL_IMPORTS = {
    "openai": ["openai"],
    "anthropic": ["anthropic"],
    "google": ["google.genai"],
    "azure": ["azure.ai.inference"],
    "bedrock": ["boto3"],
    "cohere": ["cohere"],
    "temporal": ["temporalio"],
    "langchain": ["langchain_core"],
    "crewai": ["crewai"],
    "redis": ["redis"],
}

HELPERS = [
    "sub-skills/core-sdk/scripts/check_core_sdk.py",
    "sub-skills/workflow-patterns/scripts/check_workflow_imports.py",
    "sub-skills/mcp-server-integration/scripts/validate_server_config.py",
    "sub-skills/cli-cloud-operations/scripts/collect_cli_help.py",
    "sub-skills/durable-execution/scripts/check_temporal_config.py",
    "sub-skills/observability-integrations/scripts/check_observability_config.py",
]


def import_status(module_name: str) -> dict[str, object]:
    try:
        module = importlib.import_module(module_name)
        return {"module": module_name, "ok": True, "file": getattr(module, "__file__", None)}
    except Exception as exc:  # noqa: BLE001 - diagnostic helper should summarize failures.
        return {"module": module_name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def help_status(executable: str, timeout: float) -> dict[str, object]:
    resolved = shutil.which(executable)
    if not resolved:
        return {"executable": executable, "found": False, "ok": False}
    try:
        completed = subprocess.run(
            [resolved, "--help"],
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env={"MCP_AGENT_DISABLE_VERSION_CHECK": "1", "NO_COLOR": "1"},
        )
        return {
            "executable": executable,
            "found": True,
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "first_line": next((line.strip() for line in completed.stdout.splitlines() if line.strip()), ""),
        }
    except Exception as exc:  # noqa: BLE001
        return {"executable": executable, "found": True, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--extra",
        action="append",
        choices=sorted(OPTIONAL_IMPORTS),
        default=[],
        help="Optional mcp-agent extra/import family to check. May be repeated.",
    )
    parser.add_argument("--skip-cli", action="store_true", help="Do not run CLI --help checks.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-CLI help timeout in seconds.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parents[1]
    base_import = import_status("mcp_agent")
    try:
        version = importlib.metadata.version("mcp-agent")
    except importlib.metadata.PackageNotFoundError:
        version = None

    extras = {
        extra: [import_status(module) for module in OPTIONAL_IMPORTS[extra]]
        for extra in args.extra
    }
    helper_status = [
        {"path": helper, "exists": (skill_root / helper).is_file()}
        for helper in HELPERS
    ]
    cli_status = [] if args.skip_cli else [help_status(name, args.timeout) for name in ["mcp-agent", "mcp-cloud", "mcpc"]]

    ok = bool(base_import["ok"]) and all(item["exists"] for item in helper_status)
    if extras:
        ok = ok and all(result["ok"] for results in extras.values() for result in results)
    if cli_status:
        ok = ok and any(item["ok"] for item in cli_status if item["executable"] == "mcp-agent")

    payload = {
        "ok": ok,
        "distribution_version": version,
        "base_import": base_import,
        "optional_imports": extras,
        "cli": cli_status,
        "bundled_helpers": helper_status,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"mcp-agent import: {'ok' if base_import['ok'] else 'failed'}")
        print(f"distribution version: {version or 'not found'}")
        for extra, results in extras.items():
            print(f"extra {extra}: " + ", ".join(f"{r['module']}={'ok' if r['ok'] else 'missing'}" for r in results))
        for item in cli_status:
            print(f"cli {item['executable']}: {'ok' if item['ok'] else 'missing/failed'}")
        missing = [item["path"] for item in helper_status if not item["exists"]]
        if missing:
            print("missing bundled helpers: " + ", ".join(missing))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
