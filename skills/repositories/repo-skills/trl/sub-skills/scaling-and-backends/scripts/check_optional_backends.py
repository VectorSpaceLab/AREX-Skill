#!/usr/bin/env python3
"""Safe optional-backend diagnostic for TRL scaling and serving decisions."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any


PACKAGES = {
    "trl": ["trl"],
    "accelerate": ["accelerate"],
    "torch": ["torch"],
    "transformers": ["transformers"],
    "vllm": ["vllm"],
    "fastapi": ["fastapi"],
    "pydantic": ["pydantic"],
    "uvicorn": ["uvicorn"],
    "deepspeed": ["deepspeed"],
    "peft": ["peft"],
    "bitsandbytes": ["bitsandbytes"],
    "liger-kernel": ["liger_kernel", "liger"],
    "kernels": ["kernels"],
    "unsloth": ["unsloth"],
    "rapidfireai": ["rapidfireai"],
}


def module_available(module_names: list[str]) -> bool:
    return any(importlib.util.find_spec(module_name) is not None for module_name in module_names)


def package_status(package_name: str, module_names: list[str]) -> dict[str, Any]:
    available = module_available(module_names)
    version = None
    try:
        version = metadata.version(package_name)
    except metadata.PackageNotFoundError:
        for module_name in module_names:
            try:
                version = metadata.version(module_name)
                break
            except metadata.PackageNotFoundError:
                pass
    return {"available": available, "version": version}


def torch_status() -> dict[str, Any]:
    status: dict[str, Any] = {"importable": False}
    if not module_available(["torch"]):
        return status

    import torch

    status["importable"] = True
    status["version"] = getattr(torch, "__version__", None)
    status["cuda_available"] = torch.cuda.is_available()
    status["cuda_device_count"] = torch.cuda.device_count() if torch.cuda.is_available() else 0
    status["cuda_devices"] = []
    if torch.cuda.is_available():
        for index in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(index)
            status["cuda_devices"].append(
                {
                    "index": index,
                    "name": props.name,
                    "total_memory_gb": round(props.total_memory / 1024**3, 2),
                    "capability": list(torch.cuda.get_device_capability(index)),
                }
            )
    status["mps_available"] = bool(getattr(getattr(torch, "backends", None), "mps", None)) and torch.backends.mps.is_available()
    status["xpu_available"] = hasattr(torch, "xpu") and torch.xpu.is_available()
    return status


def trl_vllm_help_status(timeout: float) -> dict[str, Any]:
    executable = shutil.which("trl")
    status: dict[str, Any] = {"trl_executable": executable, "vllm_serve_help": False}
    if executable is None:
        return status

    try:
        completed = subprocess.run(
            [executable, "vllm-serve", "--help"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception as exc:  # noqa: BLE001 - diagnostics should report failures, not crash.
        status["error"] = f"{type(exc).__name__}: {exc}"
        return status

    status["returncode"] = completed.returncode
    status["vllm_serve_help"] = completed.returncode == 0 and "vllm-serve" in completed.stdout
    if completed.stderr.strip():
        status["stderr_tail"] = completed.stderr.strip().splitlines()[-3:]
    return status


def recommendations(results: dict[str, Any]) -> list[str]:
    notes = []
    packages = results["packages"]
    torch_info = results["torch"]

    if not torch_info.get("cuda_available"):
        notes.append("CUDA is not visible; treat vLLM, bitsandbytes, and optimized-kernel checks as inspection only.")
    if not packages["vllm"]["available"]:
        notes.append("vLLM is not importable; install the vLLM extra before using TRL vLLM server or colocate mode.")
    if packages["vllm"]["available"]:
        missing_server = [name for name in ["fastapi", "pydantic", "uvicorn"] if not packages[name]["available"]]
        if missing_server:
            notes.append("vLLM is importable, but serving dependencies are missing: " + ", ".join(missing_server) + ".")
    if not packages["peft"]["available"]:
        notes.append("PEFT is not importable; LoRA/adapter configs require peft.")
    if not packages["bitsandbytes"]["available"]:
        notes.append("bitsandbytes is not importable; common QLoRA 4-bit/8-bit paths are unavailable.")
    if not packages["deepspeed"]["available"]:
        notes.append("DeepSpeed is not importable; do not choose ZeRO configs unless it is installed.")
    if results["trl_cli"].get("vllm_serve_help") and not packages["vllm"]["available"]:
        notes.append("The TRL CLI exposes vllm-serve help, but actual server startup still requires vLLM and hardware.")
    return notes


def build_results(args: argparse.Namespace) -> dict[str, Any]:
    results: dict[str, Any] = {
        "script": Path(__file__).name,
        "safe": True,
        "packages": {name: package_status(name, modules) for name, modules in PACKAGES.items()},
        "torch": torch_status(),
        "trl_cli": trl_vllm_help_status(args.cli_timeout),
    }
    results["recommendations"] = recommendations(results)
    return results


def print_text(results: dict[str, Any]) -> None:
    print("TRL optional backend diagnostic (safe: no training, serving, downloads, or large allocations)\n")
    print("Packages:")
    for name, status in results["packages"].items():
        marker = "yes" if status["available"] else "no"
        version = status["version"] or "unknown"
        print(f"  {name:15} available={marker:3} version={version}")

    torch_info = results["torch"]
    print("\nTorch/accelerator:")
    if not torch_info.get("importable"):
        print("  torch importable: no")
    else:
        print(f"  torch version: {torch_info.get('version')}")
        print(f"  cuda available: {torch_info.get('cuda_available')}")
        print(f"  cuda devices: {torch_info.get('cuda_device_count')}")
        for device in torch_info.get("cuda_devices", []):
            print(
                "  - cuda:{index} {name}, {total_memory_gb} GiB, capability {capability}".format(**device)
            )
        print(f"  mps available: {torch_info.get('mps_available')}")
        print(f"  xpu available: {torch_info.get('xpu_available')}")

    print("\nTRL CLI:")
    cli = results["trl_cli"]
    print(f"  trl executable: {cli.get('trl_executable') or 'not found'}")
    print(f"  vllm-serve --help works: {cli.get('vllm_serve_help')}")
    if cli.get("error"):
        print(f"  help error: {cli['error']}")

    if results["recommendations"]:
        print("\nRecommendations:")
        for note in results["recommendations"]:
            print(f"  - {note}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--cli-timeout",
        type=float,
        default=10.0,
        help="Seconds to wait for `trl vllm-serve --help` before reporting a timeout.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = build_results(args)
    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        print_text(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
