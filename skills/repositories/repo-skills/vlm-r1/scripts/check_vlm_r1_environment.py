#!/usr/bin/env python3
"""Safe VLM-R1 environment probes.

This script performs import and backend checks without downloading models,
loading datasets, starting servers, or launching training.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version


def dist_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def import_check(module: str) -> dict:
    try:
        mod = importlib.import_module(module)
        return {"module": module, "ok": True, "file": getattr(mod, "__file__", None)}
    except Exception as exc:  # noqa: BLE001 - report exact user environment failure
        return {"module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def torch_probe() -> dict:
    result = {"available": False, "cuda_available": False, "cuda_device_count": 0, "tensor_smoke": None}
    try:
        import torch

        result["available"] = True
        result["torch_version"] = getattr(torch, "__version__", None)
        result["cuda_available"] = bool(torch.cuda.is_available())
        result["cuda_device_count"] = int(torch.cuda.device_count()) if result["cuda_available"] else 0
        if result["cuda_available"]:
            x = torch.tensor([1.0], device="cuda")
            result["tensor_smoke"] = float(x.item())
            result["first_device"] = torch.cuda.get_device_name(0)
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def command_exists(name: str) -> str | None:
    return shutil.which(name)


def nvidia_smi_probe() -> dict:
    exe = command_exists("nvidia-smi")
    if not exe:
        return {"available": False}
    try:
        proc = subprocess.run(
            [exe, "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )
        return {"available": True, "returncode": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}
    except Exception as exc:  # noqa: BLE001
        return {"available": True, "error": f"{type(exc).__name__}: {exc}"}


def ascend_probe() -> dict:
    nodes = [p for p in ["/dev/davinci0", "/dev/davinci_manager", "/dev/devmm_svm", "/dev/hisi_hdc"] if os.path.exists(p)]
    return {"npu_smi": command_exists("npu-smi"), "device_nodes_present": nodes}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe VLM-R1 package and backend probes.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    parser.add_argument("--check-modules", default="open_r1,open_r1.configs", help="Comma-separated modules to import.")
    args = parser.parse_args()

    modules = [m.strip() for m in args.check_modules.split(",") if m.strip()]
    report = {
        "python": sys.version,
        "distributions": {name: dist_version(name) for name in ["open-r1", "torch", "transformers", "trl", "deepspeed", "datasets"]},
        "imports": [import_check(m) for m in modules],
        "torch": torch_probe(),
        "nvidia_smi": nvidia_smi_probe(),
        "ascend": ascend_probe(),
        "tools": {name: command_exists(name) for name in ["torchrun", "python", "pip", "npu-smi", "docker"]},
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(json.dumps(report, indent=2))
        failures = [item for item in report["imports"] if not item["ok"]]
        if failures:
            print("\nImport warnings:", file=sys.stderr)
            for item in failures:
                print(f"- {item['module']}: {item['error']}", file=sys.stderr)
    return 1 if any(not item["ok"] for item in report["imports"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
