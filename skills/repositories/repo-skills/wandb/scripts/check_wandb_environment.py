#!/usr/bin/env python3
"""Inspect a W&B Python/CLI environment without printing secrets."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
from importlib import metadata

SECRET_ENV_NAMES = {"WANDB_API_KEY", "WANDB_IDENTITY_TOKEN_FILE"}
VISIBLE_ENV_NAMES = [
    "WANDB_MODE",
    "WANDB_BASE_URL",
    "WANDB_ENTITY",
    "WANDB_PROJECT",
    "WANDB_DIR",
    "WANDB_CACHE_DIR",
    "WANDB_CONFIG_DIR",
    "WANDB_ARTIFACT_DIR",
    "WANDB_CONSOLE",
    "WANDB_SILENT",
    "WANDB_QUIET",
]
OPTIONAL_MODULES = {
    "aws": ["boto3", "botocore"],
    "gcp": ["google.cloud.storage"],
    "azure": ["azure.identity", "azure.storage.blob"],
    "media": ["PIL", "numpy", "plotly"],
    "launch": ["kubernetes", "yaml"],
    "sweeps": ["yaml"],
}


def module_available(name: str) -> bool:
    try:
        importlib.import_module(name)
        return True
    except Exception:
        return False


def run_command(command: list[str], timeout: int = 10) -> dict[str, object]:
    try:
        proc = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
        return {"returncode": proc.returncode, "stdout": proc.stdout[:4000], "stderr": proc.stderr[:4000]}
    except Exception as exc:
        return {"error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Report W&B import, package, CLI, optional dependency, and env facts without secrets.")
    parser.add_argument("--check-cli", action="store_true", help="Run safe CLI help/version checks.")
    parser.add_argument("--optional", action="append", choices=sorted(OPTIONAL_MODULES), default=[], help="Optional dependency group to probe. Repeatable.")
    args = parser.parse_args()

    report: dict[str, object] = {
        "python": sys.version.split()[0],
        "executable_basename": os.path.basename(sys.executable),
        "wandb": {},
        "cli": {},
        "environment": {},
        "optional_dependencies": {},
    }

    try:
        import wandb
        report["wandb"] = {
            "import_ok": True,
            "version": getattr(wandb, "__version__", None),
            "distribution_version": metadata.version("wandb"),
        }
    except Exception as exc:
        report["wandb"] = {"import_ok": False, "error": str(exc)}

    for name in VISIBLE_ENV_NAMES:
        if name in os.environ:
            report["environment"][name] = os.environ[name]
    for name in SECRET_ENV_NAMES:
        report["environment"][name] = "set" if os.environ.get(name) else "unset"

    if args.check_cli:
        executable = shutil.which("wandb") or shutil.which("wb")
        report["cli"]["executable_found"] = bool(executable)
        report["cli"]["executable_name"] = os.path.basename(executable) if executable else None
        if executable:
            report["cli"]["version"] = run_command([executable, "--version"])
            report["cli"]["help"] = run_command([executable, "--help"])

    for group in args.optional:
        report["optional_dependencies"][group] = {module: module_available(module) for module in OPTIONAL_MODULES[group]}

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["wandb"].get("import_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
