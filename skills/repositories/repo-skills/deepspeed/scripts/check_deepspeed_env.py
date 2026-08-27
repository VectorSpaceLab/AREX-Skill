#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# DeepSpeed Team
"""Read-only DeepSpeed environment checker.

This script imports package metadata, PyTorch, DeepSpeed, and selected CLI tools
without launching training, compiling ops, writing storage, or contacting online
services.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from typing import Any


def run_help(command: str, timeout: int) -> dict[str, Any]:
    executable = shutil.which(command)
    if not executable:
        return {"command": command, "found": False}
    try:
        proc = subprocess.run(
            [executable, "--help"],
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "found": True,
            "returncode": proc.returncode,
            "stdout_lines": len(proc.stdout.splitlines()),
            "stderr_lines": len(proc.stderr.splitlines()),
        }
    except Exception as exc:  # pragma: no cover - diagnostic path.
        return {"command": command, "found": True, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only DeepSpeed environment checker.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--help-timeout", type=int, default=20, help="Seconds for each CLI --help probe.")
    parser.add_argument(
        "--tools",
        nargs="*",
        default=["deepspeed", "ds", "ds_report"],
        help="CLI tools to locate and probe with --help.",
    )
    args = parser.parse_args()

    result: dict[str, Any] = {"python": sys.version.split()[0], "ok": True, "errors": []}

    try:
        dist = metadata.distribution("deepspeed")
        result["distribution"] = {"name": dist.metadata.get("Name"), "version": dist.version}
    except Exception as exc:
        result["ok"] = False
        result["errors"].append(f"deepspeed metadata: {type(exc).__name__}: {exc}")

    try:
        torch = importlib.import_module("torch")
        result["torch"] = {
            "version": getattr(torch, "__version__", None),
            "cuda_available": bool(torch.cuda.is_available()) if hasattr(torch, "cuda") else False,
            "cuda_version": getattr(getattr(torch, "version", None), "cuda", None),
        }
    except Exception as exc:
        result["ok"] = False
        result["errors"].append(f"torch import: {type(exc).__name__}: {exc}")

    try:
        deepspeed = importlib.import_module("deepspeed")
        result["deepspeed"] = {"version": getattr(deepspeed, "__version__", None)}
    except Exception as exc:
        result["ok"] = False
        result["errors"].append(f"deepspeed import: {type(exc).__name__}: {exc}")

    result["tools"] = [run_help(command, args.help_timeout) for command in args.tools]

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Python: {result['python']}")
        for key in ("distribution", "torch", "deepspeed"):
            if key in result:
                print(f"{key}: {result[key]}")
        for tool in result["tools"]:
            print(f"tool: {tool}")
        if result["errors"]:
            print("Errors:")
            for error in result["errors"]:
                print(f"- {error}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
