#!/usr/bin/env python3
"""Collect a safe vLLM deployment environment summary.

The script does not import private project paths, download models, start a
server, or require GPUs. It reports package, Python, platform, selected
accelerator, and CLI-help availability facts that are useful for deployment and
performance support.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from typing import Any

SAFE_ENV_KEYS = (
    "CUDA_VISIBLE_DEVICES",
    "HIP_VISIBLE_DEVICES",
    "ROCR_VISIBLE_DEVICES",
    "VLLM_TARGET_DEVICE",
    "VLLM_HOST_IP",
    "NCCL_SOCKET_IFNAME",
    "GLOO_SOCKET_IFNAME",
    "NCCL_DEBUG",
    "VLLM_LOGGING_LEVEL",
    "VLLM_LOG_STATS_INTERVAL",
    "VLLM_CPU_KVCACHE_SPACE",
    "PYTHONHASHSEED",
)

PACKAGES = (
    "vllm",
    "torch",
    "triton",
    "ray",
    "transformers",
    "tokenizers",
    "numpy",
    "prometheus_client",
    "opentelemetry-api",
    "opentelemetry-sdk",
)


def run_command(command: list[str], timeout: int) -> dict[str, Any]:
    executable = shutil.which(command[0])
    if executable is None:
        return {"available": False, "error": f"{command[0]} not found"}
    try:
        completed = subprocess.run(
            [executable, *command[1:]],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"available": True, "error": f"timed out after {timeout}s"}
    return {
        "available": True,
        "returncode": completed.returncode,
        "stdout_first_lines": completed.stdout.splitlines()[:20],
        "stderr_first_lines": completed.stderr.splitlines()[:20],
    }


def package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for package in PACKAGES:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return versions


def torch_summary() -> dict[str, Any]:
    try:
        import torch  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - depends on user env
        return {"import_ok": False, "error": repr(exc)}

    summary: dict[str, Any] = {
        "import_ok": True,
        "version": getattr(torch, "__version__", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": None,
        "cuda_version": getattr(torch.version, "cuda", None),
        "hip_version": getattr(torch.version, "hip", None),
    }
    try:
        summary["cuda_device_count"] = torch.cuda.device_count()
        if torch.cuda.is_available():
            summary["cuda_devices"] = [
                torch.cuda.get_device_name(index)
                for index in range(torch.cuda.device_count())
            ]
    except Exception as exc:  # pragma: no cover - depends on user env
        summary["cuda_query_error"] = repr(exc)
    return summary


def vllm_import_summary() -> dict[str, Any]:
    try:
        import vllm  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - depends on user env
        return {"import_ok": False, "error": repr(exc)}
    return {
        "import_ok": True,
        "version_attr": getattr(vllm, "__version__", None),
        "module_file_present": bool(getattr(vllm, "__file__", None)),
    }


def build_summary(args: argparse.Namespace) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "python": {
            "version": sys.version.split()[0],
            "implementation": platform.python_implementation(),
            "executable_basename": os.path.basename(sys.executable),
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "packages": package_versions(),
        "environment": {key: os.environ.get(key) for key in SAFE_ENV_KEYS},
        "vllm_import": vllm_import_summary(),
        "torch": torch_summary(),
    }
    if args.include_gpu_commands:
        summary["nvidia_smi"] = run_command(["nvidia-smi", "-L"], args.timeout)
        summary["rocm_smi"] = run_command(["rocm-smi", "--showproductname"], args.timeout)
    if args.check_vllm_help:
        summary["vllm_help"] = run_command(["vllm", "--help"], args.timeout)
        summary["vllm_serve_help"] = run_command(
            ["vllm", "serve", "--help"], args.timeout
        )
    return summary


def print_text(summary: dict[str, Any]) -> None:
    print("vLLM environment summary")
    print("========================")
    print(f"Python: {summary['python']['version']} ({summary['python']['implementation']})")
    print(
        "Platform: "
        f"{summary['platform']['system']} {summary['platform']['release']} "
        f"{summary['platform']['machine']}"
    )
    print("\nPackages:")
    for name, version in summary["packages"].items():
        print(f"  {name}: {version or 'not installed'}")
    print("\nSelected environment variables:")
    for key, value in summary["environment"].items():
        print(f"  {key}: {value if value is not None else '<unset>'}")
    print("\nvLLM import:")
    print(json.dumps(summary["vllm_import"], indent=2, sort_keys=True))
    print("\nTorch:")
    print(json.dumps(summary["torch"], indent=2, sort_keys=True))
    for optional_key in ("nvidia_smi", "rocm_smi", "vllm_help", "vllm_serve_help"):
        if optional_key in summary:
            print(f"\n{optional_key}:")
            print(json.dumps(summary[optional_key], indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect a safe vLLM deployment environment summary."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of text.",
    )
    parser.add_argument(
        "--check-vllm-help",
        action="store_true",
        help="Run 'vllm --help' and 'vllm serve --help' if the CLI is available.",
    )
    parser.add_argument(
        "--include-gpu-commands",
        action="store_true",
        help="Run lightweight GPU inventory commands if nvidia-smi or rocm-smi exists.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Timeout in seconds for each optional command. Default: 10.",
    )
    args = parser.parse_args()
    summary = build_summary(args)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_text(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
