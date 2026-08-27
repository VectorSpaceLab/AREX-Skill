#!/usr/bin/env python3
"""Safe docTR CLI environment diagnostic.

By default this script performs Python imports only. Optional GPU command probes
are bounded and must be requested explicitly.
"""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def module_version(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - diagnostic should report import failures
        return {"available": False, "version": None, "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(module, "__version__", None)
    return {"available": True, "version": version, "error": None}


def torch_backend_info() -> dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    info: dict[str, Any] = {
        "available": True,
        "version": getattr(torch, "__version__", None),
        "cuda_available": None,
        "cuda_device_count": None,
        "mps_available": None,
    }
    try:
        info["cuda_available"] = bool(torch.cuda.is_available())
        info["cuda_device_count"] = int(torch.cuda.device_count())
    except Exception as exc:  # noqa: BLE001
        info["cuda_error"] = f"{type(exc).__name__}: {exc}"
    try:
        info["mps_available"] = bool(getattr(torch.backends, "mps").is_available())
    except Exception:
        info["mps_available"] = False
    return info


def run_probe(command: list[str], timeout: float) -> dict[str, Any]:
    executable = shutil.which(command[0])
    if executable is None:
        return {"available": False, "command": command, "returncode": None, "stdout": "", "stderr": "not found"}
    try:
        proc = subprocess.run(
            [executable, *command[1:]],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"available": True, "command": command, "returncode": None, "stdout": "", "stderr": "timed out"}
    return {
        "available": True,
        "command": command,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def _doctr_cli_path() -> str | None:
    cli = shutil.which("doctr-cli")
    if cli:
        return cli
    sibling = Path(sys.executable).resolve().parent / "doctr-cli"
    return str(sibling) if sibling.exists() else None


def collect(args: argparse.Namespace) -> dict[str, Any]:
    report: dict[str, Any] = {
        "python": {
            "executable": sys.executable,
            "version": platform.python_version(),
            "platform": platform.platform(),
        },
        "entry_points": {"doctr_cli": _doctr_cli_path()},
        "modules": {
            "doctr": module_version("doctr"),
            "torchvision": module_version("torchvision"),
            "cv2": module_version("cv2"),
            "pypdfium2": module_version("pypdfium2"),
            "PIL": module_version("PIL"),
        },
        "torch": torch_backend_info(),
        "gpu_command_probes": {},
    }
    if args.probe_gpu_commands:
        report["gpu_command_probes"] = {
            "nvidia_smi": run_probe(["nvidia-smi", "-L"], args.timeout),
            "nvcc": run_probe(["nvcc", "--version"], args.timeout),
        }
    return report


def print_text(report: dict[str, Any]) -> None:
    print("docTR CLI environment report")
    print(f"Python: {report['python']['version']} ({report['python']['platform']})")
    print(f"doctr-cli: {report['entry_points']['doctr_cli'] or 'not found'}")
    for name, item in report["modules"].items():
        if item["available"]:
            print(f"{name}: {item['version'] or 'available'}")
        else:
            print(f"{name}: unavailable ({item['error']})")
    torch_info = report["torch"]
    if torch_info.get("available"):
        print(
            "torch: {version}, cuda_available={cuda}, cuda_device_count={count}, mps_available={mps}".format(
                version=torch_info.get("version"),
                cuda=torch_info.get("cuda_available"),
                count=torch_info.get("cuda_device_count"),
                mps=torch_info.get("mps_available"),
            )
        )
    else:
        print(f"torch: unavailable ({torch_info.get('error')})")
    probes = report.get("gpu_command_probes") or {}
    for name, probe in probes.items():
        print(f"{name}: returncode={probe.get('returncode')} stderr={probe.get('stderr')!r}")
        if probe.get("stdout"):
            print(probe["stdout"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print safe docTR CLI/import/backend diagnostics.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument(
        "--probe-gpu-commands",
        action="store_true",
        help="Also run bounded local nvidia-smi/nvcc probes when available",
    )
    parser.add_argument("--timeout", type=float, default=3.0, help="Timeout in seconds for each optional command probe")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    report = collect(args)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
