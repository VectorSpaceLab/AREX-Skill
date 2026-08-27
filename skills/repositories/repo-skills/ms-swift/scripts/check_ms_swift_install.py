#!/usr/bin/env python3
"""Check an ms-swift installation without launching models or services."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from typing import Any

OPTIONAL_MODULES = {
    "eval": ["evalscope"],
    "ray": ["ray"],
    "megatron": ["megatron", "megatron.core", "mcore_bridge"],
    "serve-vllm": ["vllm"],
    "serve-sglang": ["sglang"],
    "serve-lmdeploy": ["lmdeploy"],
    "quant-awq": ["awq"],
    "quant-gptq": ["auto_gptq", "optimum"],
    "quant-gptq-v2": ["gptqmodel", "optimum"],
    "quant-bnb": ["bitsandbytes"],
}


def check_import(module: str) -> dict[str, Any]:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - diagnostics only
        return {"module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"module": module, "ok": True, "file": getattr(imported, "__file__", None)}


def command_help(command: list[str], timeout: int) -> dict[str, Any]:
    executable = shutil.which(command[0])
    if executable is None:
        return {"command": command, "ok": False, "error": "command not found"}
    try:
        proc = subprocess.run(
            [executable, *command[1:], "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001 - diagnostics only
        return {"command": command, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "command": [executable, *command[1:], "--help"],
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout_lines": len(proc.stdout.splitlines()),
        "stderr_first_lines": proc.stderr.splitlines()[:5],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--optional", action="append", choices=sorted(OPTIONAL_MODULES), default=[], help="Optional dependency family to check; repeatable.")
    parser.add_argument("--check-cli", action="store_true", help="Run safe --help checks for selected swift routes.")
    parser.add_argument("--route", action="append", default=["sft", "infer", "export", "rlhf"], help="swift route to check when --check-cli is set.")
    parser.add_argument("--timeout", type=int, default=30, help="Seconds per CLI help command.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    result: dict[str, Any] = {
        "python": sys.version.split()[0],
        "distribution": {},
        "imports": {},
        "optional": {},
        "cli": [],
    }

    for dist_name in ["ms-swift", "ms_swift"]:
        try:
            result["distribution"][dist_name] = {"ok": True, "version": metadata.version(dist_name)}
        except Exception as exc:  # noqa: BLE001 - diagnostics only
            result["distribution"][dist_name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    result["imports"]["swift"] = check_import("swift")
    if result["imports"]["swift"]["ok"]:
        try:
            import swift  # type: ignore

            result["swift_version"] = getattr(swift, "__version__", None)
        except Exception:
            pass

    for family in args.optional:
        result["optional"][family] = [check_import(module) for module in OPTIONAL_MODULES[family]]

    if args.check_cli:
        for route in args.route:
            result["cli"].append(command_help(["swift", route], args.timeout))
        result["cli"].append(command_help(["megatron", "sft"], args.timeout))

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Python: {result['python']}")
        for name, info in result["distribution"].items():
            print(f"Distribution {name}: {'ok ' + info.get('version', '') if info['ok'] else info['error']}")
        for name, info in result["imports"].items():
            print(f"Import {name}: {'ok' if info['ok'] else info['error']}")
        if "swift_version" in result:
            print(f"swift.__version__: {result['swift_version']}")
        for family, checks in result["optional"].items():
            statuses = ", ".join(f"{item['module']}={'ok' if item['ok'] else 'missing'}" for item in checks)
            print(f"Optional {family}: {statuses}")
        for item in result["cli"]:
            print(f"CLI {' '.join(item['command'])}: {'ok' if item['ok'] else item.get('error', 'failed')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
