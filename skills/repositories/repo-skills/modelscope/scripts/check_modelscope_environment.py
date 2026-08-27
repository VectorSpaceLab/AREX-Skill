#!/usr/bin/env python3
"""Check a ModelScope installation without downloads or side effects.

The check imports public modules, reports package versions, optionally runs CLI
help, and optionally probes torch/CUDA. It does not contact ModelScope Hub,
download models/datasets, start a server, train, export, upload, clear caches,
or modify files.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from importlib import metadata
from typing import Any, Dict, List

MODULES = [
    "modelscope",
    "modelscope.hub",
    "modelscope.fileio",
    "modelscope.utils.config",
    "modelscope.msdatasets",
    "modelscope.pipelines",
    "modelscope.trainers",
    "modelscope.outputs",
]
DISTRIBUTIONS = [
    "modelscope",
    "modelscope-hub",
    "torch",
    "datasets",
    "transformers",
    "fastapi",
    "uvicorn",
]
OPTIONAL_MODULES = [
    "torch",
    "transformers",
    "datasets",
    "fastapi",
    "uvicorn",
    "cv2",
    "PIL",
    "tensorflow",
    "vllm",
]


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def import_status(name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(name)
        return {"module": name, "ok": True, "version": getattr(module, "__version__", None)}
    except Exception as exc:
        return {"module": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def run_cli_help(command: str, timeout: int) -> Dict[str, Any]:
    exe = shutil.which(command)
    if not exe:
        return {"command": command, "ok": False, "error": "not found on PATH"}
    try:
        proc = subprocess.run(
            [exe, "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"command": command, "ok": False, "error": f"timed out after {timeout}s"}
    return {
        "command": command,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout_first_line": proc.stdout.splitlines()[0] if proc.stdout.splitlines() else "",
        "stderr_first_line": proc.stderr.splitlines()[0] if proc.stderr.splitlines() else "",
    }


def torch_backend_status() -> Dict[str, Any]:
    try:
        import torch  # type: ignore
    except Exception as exc:
        return {"torch_import": False, "error": f"{type(exc).__name__}: {exc}"}
    info: Dict[str, Any] = {
        "torch_import": True,
        "torch_version": getattr(torch, "__version__", None),
        "torch_cuda_version": getattr(torch.version, "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()),
    }
    if info["cuda_available"]:
        try:
            info["cuda_device_name_0"] = torch.cuda.get_device_name(0)
            info["cuda_device_capability_0"] = list(torch.cuda.get_device_capability(0))
            torch.empty((1,), device="cuda")
            info["cuda_tensor_smoke"] = True
        except Exception as exc:
            info["cuda_tensor_smoke"] = False
            info["cuda_error"] = f"{type(exc).__name__}: {exc}"
    return info


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "executable": sys.executable if args.show_private_paths else "omitted-use --show-private-paths",
        "distributions": {name: dist_version(name) for name in DISTRIBUTIONS},
        "required_imports": [import_status(name) for name in MODULES],
        "optional_imports": [import_status(name) for name in OPTIONAL_MODULES],
        "cli_help": [],
        "backend": {},
        "warnings": [
            "This check is non-network and does not prove model downloads, GPU domain pipelines, training, serving, or export workflows."
        ],
    }
    if args.cli:
        report["cli_help"] = [run_cli_help(cmd, args.timeout) for cmd in ("modelscope", "ms")]
    if args.torch_backend:
        report["backend"]["torch"] = torch_backend_status()
    report["ok"] = all(item["ok"] for item in report["required_imports"])
    if args.cli and report["cli_help"]:
        report["ok"] = report["ok"] and all(item["ok"] for item in report["cli_help"])
    return report


def print_summary(report: Dict[str, Any]) -> None:
    print("ModelScope environment check")
    print(f"Python: {report['python']}")
    print("Distributions:")
    for name, version in report["distributions"].items():
        print(f"  - {name}: {version or 'not installed'}")
    print("Required imports:")
    for item in report["required_imports"]:
        status = "OK" if item["ok"] else f"FAIL ({item['error']})"
        print(f"  - {item['module']}: {status}")
    if report["cli_help"]:
        print("CLI help:")
        for item in report["cli_help"]:
            status = "OK" if item["ok"] else f"FAIL ({item.get('error') or item.get('stderr_first_line')})"
            print(f"  - {item['command']}: {status}")
    if report["backend"]:
        print("Backend:")
        torch = report["backend"].get("torch", {})
        for key, value in torch.items():
            print(f"  - {key}: {value}")
    for warning in report["warnings"]:
        print(f"warning: {warning}")
    print(f"overall: {'PASS' if report['ok'] else 'FAIL'}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Non-side-effecting ModelScope environment checker.")
    parser.add_argument("--summary", action="store_true", help="Print a human-readable summary instead of JSON.")
    parser.add_argument("--cli", action="store_true", help="Also run `modelscope --help` and `ms --help` if scripts are on PATH.")
    parser.add_argument("--torch-backend", action="store_true", help="Probe torch import and CUDA availability without running model code.")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout seconds for CLI help checks.")
    parser.add_argument("--show-private-paths", action="store_true", help="Include the Python executable path in JSON output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args)
    if args.summary:
        print_summary(report)
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
