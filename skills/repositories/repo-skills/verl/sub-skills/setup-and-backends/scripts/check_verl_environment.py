#!/usr/bin/env python3
"""Safe JSON diagnostics for a verl Python environment.

This helper performs local imports and package metadata checks only. It does
not access the network, download models, launch Ray jobs, run Docker, or print
local module file paths.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import platform
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

CORE_PACKAGES = [
    "verl",
    "torch",
    "tensordict",
    "ray",
    "transformers",
    "hydra-core",
    "omegaconf",
]

DEFAULT_OPTIONAL_PACKAGES = [
    "vllm",
    "sglang",
    "mbridge",
    "flash-attn",
    "liger-kernel",
    "tensorrt-llm",
    "torch-npu",
]

IMPORT_CHECKS = [
    "verl",
    "verl.protocol",
    "verl.trainer.main_ppo",
    "verl.model_merger",
    "verl.tools.base_tool",
]

TENSOR_DICT_MIN = (0, 8, 0)
TENSOR_DICT_MAX = (0, 10, 0)


@dataclass
class ImportResult:
    ok: bool
    error_type: str | None = None
    error: str | None = None


def parse_version_tuple(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    current = ""
    for char in version:
        if char.isdigit():
            current += char
            continue
        if current:
            parts.append(int(current))
            current = ""
        if char in "+-":
            break
    if current:
        parts.append(int(current))
    return tuple(parts)


def distribution_version(name: str) -> dict[str, Any]:
    try:
        return {"installed": True, "version": metadata.version(name)}
    except metadata.PackageNotFoundError:
        return {"installed": False, "version": None}
    except Exception as exc:  # pragma: no cover - defensive metadata guard
        return {"installed": False, "version": None, "error": f"{type(exc).__name__}: {exc}"}


def import_module_safely(name: str) -> ImportResult:
    try:
        importlib.import_module(name)
        return ImportResult(ok=True)
    except Exception as exc:
        return ImportResult(ok=False, error_type=type(exc).__name__, error=str(exc))


def check_tensordict_constraint(version: str | None) -> dict[str, Any]:
    if not version:
        return {"ok": False, "message": "tensordict is not installed"}
    parsed = parse_version_tuple(version)
    if not parsed:
        return {"ok": None, "message": "could not parse tensordict version"}
    if parsed == (0, 9, 0):
        return {"ok": False, "message": "verl excludes tensordict 0.9.0"}
    if parsed < TENSOR_DICT_MIN or parsed > TENSOR_DICT_MAX:
        return {"ok": False, "message": "verl declares tensordict>=0.8.0,<=0.10.0,!=0.9.0"}
    return {"ok": True, "message": "within verl declared range"}


def collect_cuda_info() -> dict[str, Any]:
    result: dict[str, Any] = {"checked": True, "torch_imported": False}
    torch_result = import_module_safely("torch")
    if not torch_result.ok:
        result.update({"error_type": torch_result.error_type, "error": torch_result.error})
        return result

    import torch  # type: ignore

    result["torch_imported"] = True
    result["torch_version"] = getattr(torch, "__version__", None)
    version_obj = getattr(torch, "version", None)
    result["torch_cuda_version"] = getattr(version_obj, "cuda", None)
    result["torch_hip_version"] = getattr(version_obj, "hip", None)

    cuda_obj = getattr(torch, "cuda", None)
    if cuda_obj is None:
        result["cuda_available"] = False
        result["device_count"] = 0
        return result

    try:
        result["cuda_available"] = bool(cuda_obj.is_available())
        result["device_count"] = int(cuda_obj.device_count()) if result["cuda_available"] else 0
        if result["cuda_available"] and result["device_count"]:
            result["device_names"] = [str(cuda_obj.get_device_name(index)) for index in range(result["device_count"])]
    except Exception as exc:  # pragma: no cover - depends on accelerator runtime
        result["cuda_query_error"] = f"{type(exc).__name__}: {exc}"
    return result


def run_pip_check(timeout: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"ran": False, "ok": False, "error": "pip check timed out"}
    except Exception as exc:  # pragma: no cover - defensive subprocess guard
        return {"ran": False, "ok": False, "error": f"{type(exc).__name__}: {exc}"}

    output = "\n".join(part.strip() for part in [completed.stdout, completed.stderr] if part.strip())
    return {
        "ran": True,
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "output": output,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    optional_packages = args.optional or DEFAULT_OPTIONAL_PACKAGES
    packages = list(dict.fromkeys(CORE_PACKAGES + optional_packages))
    package_report = {name: distribution_version(name) for name in packages}

    import_report = {}
    for module_name in IMPORT_CHECKS:
        result = import_module_safely(module_name)
        import_report[module_name] = {
            "ok": result.ok,
            "error_type": result.error_type,
            "error": result.error,
        }

    report: dict[str, Any] = {
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable_basename": sys.executable.rsplit("/", 1)[-1].rsplit("\\", 1)[-1],
        },
        "packages": package_report,
        "imports": import_report,
        "constraints": {
            "python_requires": ">=3.10",
            "tensordict": check_tensordict_constraint(package_report.get("tensordict", {}).get("version")),
            "cuda_runtime_guidance": ">=12.8 for NVIDIA GPU runtime environments",
        },
        "notes": [
            "Core import success in a CPU environment does not validate optional GPU, vLLM, SGLang, Megatron, flash-attn, ROCm, or NPU runtime stacks.",
            "This helper performs no network checks, downloads, Docker actions, or Ray launches.",
        ],
    }

    if args.include_cuda:
        report["cuda"] = collect_cuda_info()

    if args.check_pip:
        report["pip_check"] = run_pip_check(timeout=args.pip_timeout)

    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely inspect a verl Python environment and emit JSON.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--include-cuda",
        action="store_true",
        help="Query torch CUDA/HIP availability without launching kernels or external commands.",
    )
    parser.add_argument(
        "--check-pip",
        action="store_true",
        help="Run `python -m pip check` locally and include its output.",
    )
    parser.add_argument("--pip-timeout", type=int, default=30, help="Timeout in seconds for pip check.")
    parser.add_argument(
        "--optional",
        nargs="*",
        default=None,
        help="Optional distribution names to check in addition to core packages.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args)
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
