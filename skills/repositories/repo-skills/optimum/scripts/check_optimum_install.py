#!/usr/bin/env python3
"""Check an installed Optimum environment without downloads or training.

Examples:
  python scripts/check_optimum_install.py
  python scripts/check_optimum_install.py --json
  python scripts/check_optimum_install.py --run-cli-env --strict
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
from typing import Any, Dict, List


def dist_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def module_status(module: str) -> Dict[str, Any]:
    try:
        imported = importlib.import_module(module)
        return {"module": module, "ok": True, "file": bool(getattr(imported, "__file__", None))}
    except Exception as exc:  # keep diagnostics user-facing
        return {"module": module, "ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def run_command(argv: List[str], timeout: int) -> Dict[str, Any]:
    try:
        proc = subprocess.run(argv, text=True, capture_output=True, timeout=timeout, check=False)
        return {
            "argv": argv,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip().splitlines()[:20],
            "stderr": proc.stderr.strip().splitlines()[:20],
        }
    except FileNotFoundError:
        return {"argv": argv, "returncode": None, "error": "executable-not-found"}
    except subprocess.TimeoutExpired:
        return {"argv": argv, "returncode": None, "error": f"timeout-after-{timeout}s"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely inspect Optimum package, CLI, and optional dependency state.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--run-cli-env", action="store_true", help="Also run `optimum-cli env`.")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout for CLI subprocesses in seconds.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if base Optimum imports or CLI help fail.")
    args = parser.parse_args()

    modules = [
        "optimum.version",
        "optimum.commands.optimum_cli",
        "optimum.exporters.tasks",
        "optimum.fx.optimization",
        "optimum.pipelines",
        "optimum.gptq",
        "optimum.utils.input_generators",
        "optimum.utils.normalized_config",
    ]
    optional_modules = [
        "requests",
        "torchvision",
        "datasets",
        "gptqmodel",
        "accelerate",
        "optimum.onnxruntime",
        "optimum.exporters.onnx",
        "optimum.intel",
        "onnxruntime",
    ]

    result: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "distributions": {
            name: dist_version(name)
            for name in [
                "optimum",
                "transformers",
                "torch",
                "huggingface_hub",
                "numpy",
                "requests",
                "torchvision",
                "datasets",
                "gptqmodel",
                "accelerate",
                "optimum-onnx",
                "optimum-intel",
                "onnxruntime",
            ]
        },
        "required_modules": [module_status(m) for m in modules],
        "optional_modules": [module_status(m) for m in optional_modules],
        "cli": {"path_found": bool(shutil.which("optimum-cli"))},
    }

    result["cli"]["help"] = run_command(["optimum-cli", "--help"], args.timeout)
    if args.run_cli_env:
        result["cli"]["env"] = run_command(["optimum-cli", "env"], args.timeout)

    torch_info: Dict[str, Any] = {"imported": False}
    try:
        import torch

        torch_info.update(
            {
                "imported": True,
                "version": getattr(torch, "__version__", None),
                "cuda_version": getattr(torch.version, "cuda", None),
                "cuda_available": bool(torch.cuda.is_available()),
                "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            }
        )
        if torch.cuda.is_available():
            torch_info["cuda_device_0"] = torch.cuda.get_device_name(0)
            torch_info["cuda_capability_0"] = torch.cuda.get_device_capability(0)
    except Exception as exc:
        torch_info.update({"error_type": type(exc).__name__, "error": str(exc)})
    result["torch"] = torch_info

    base_ok = all(item["ok"] for item in result["required_modules"])
    cli_help_ok = result["cli"]["help"].get("returncode") == 0
    result["ok"] = bool(base_ok and cli_help_ok)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Optimum distribution: {result['distributions']['optimum']}")
        print(f"Base imports: {'ok' if base_ok else 'failed'}")
        for item in result["required_modules"]:
            if not item["ok"]:
                print(f"  - {item['module']}: {item['error_type']}: {item['error']}")
        print(f"optimum-cli --help: {'ok' if cli_help_ok else 'failed'}")
        print(
            "Optional modules present: "
            + ", ".join(item["module"] for item in result["optional_modules"] if item["ok"])
        )
        missing = [item["module"] for item in result["optional_modules"] if not item["ok"]]
        if missing:
            print("Optional modules missing: " + ", ".join(missing))
        if torch_info.get("imported"):
            print(
                f"Torch: {torch_info.get('version')} cuda_available={torch_info.get('cuda_available')} "
                f"devices={torch_info.get('cuda_device_count')}"
            )

    return 1 if args.strict and not result["ok"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
