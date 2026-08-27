#!/usr/bin/env python3
"""Diagnose H2O LLM Studio training environment readiness without training.

Checks are read-only except for optional imports performed in the current Python
process. No model downloads, network calls, or training commands are executed.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def status(ok: bool, message: str, **extra: Any) -> dict[str, Any]:
    item = {"ok": ok, "message": message}
    item.update(extra)
    return item


def check_distribution() -> dict[str, Any]:
    names = ["h2o-llmstudio", "llm-studio"]
    for name in names:
        try:
            version = importlib.metadata.version(name)
            return status(True, f"distribution {name} is installed", distribution=name, version=version)
        except importlib.metadata.PackageNotFoundError:
            continue
    return status(False, "h2o-llmstudio distribution metadata was not found")


def check_import(module: str) -> dict[str, Any]:
    try:
        imported = importlib.import_module(module)
        origin = getattr(imported, "__file__", None)
        return status(
            True,
            f"import {module} succeeded",
            origin_available=bool(origin),
            origin_file=Path(origin).name if origin else None,
        )
    except Exception as exc:  # noqa: BLE001 - user-facing diagnostic
        return status(False, f"import {module} failed: {type(exc).__name__}: {exc}")


def check_torch(require_cuda: bool = False) -> dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        return status(False, f"import torch failed: {type(exc).__name__}: {exc}")

    info: dict[str, Any] = {
        "torch_version": getattr(torch, "__version__", None),
        "torch_cuda_version": getattr(torch.version, "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
    }
    if torch.cuda.is_available():
        try:
            info["first_cuda_device"] = torch.cuda.get_device_name(0)
        except Exception as exc:  # noqa: BLE001
            info["first_cuda_device_error"] = f"{type(exc).__name__}: {exc}"
    ok = info["cuda_available"] or not require_cuda
    message = "torch import succeeded"
    if require_cuda and not info["cuda_available"]:
        message = "torch import succeeded but CUDA is not available"
    return status(ok, message, **info)


def find_nvcc(cuda_home: str | None) -> tuple[bool, str | None]:
    candidates = []
    if cuda_home:
        candidates.append(str(Path(cuda_home) / "bin" / "nvcc"))
    path_nvcc = shutil.which("nvcc")
    if path_nvcc:
        candidates.append(path_nvcc)
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            try:
                proc = subprocess.run([candidate, "--version"], text=True, capture_output=True, timeout=10, check=False)
                output = (proc.stdout or proc.stderr).strip().splitlines()[-1] if (proc.stdout or proc.stderr).strip() else "nvcc found"
                return True, output
            except Exception as exc:  # noqa: BLE001
                return True, f"nvcc probe failed: {type(exc).__name__}: {exc}"
    return False, None


def check_cuda_home() -> dict[str, Any]:
    cuda_home = os.environ.get("CUDA_HOME") or os.environ.get("CUDA_PATH")
    nvcc_found, nvcc_version = find_nvcc(cuda_home)
    message = "nvcc found" if nvcc_found else "nvcc not found; set CUDA_HOME/CUDA_PATH to a CUDA toolkit root or add nvcc to PATH"
    return status(
        nvcc_found,
        message,
        cuda_home_set=bool(cuda_home),
        nvcc_found=nvcc_found,
        nvcc_version=nvcc_version,
    )


def check_deepspeed() -> dict[str, Any]:
    try:
        import deepspeed  # noqa: F401
        version = getattr(deepspeed, "__version__", None)
        exe = shutil.which("deepspeed")
        return status(True, "deepspeed import succeeded", version=version, executable_available=bool(exe))
    except Exception as exc:  # noqa: BLE001
        return status(False, f"deepspeed import failed: {type(exc).__name__}: {exc}", diagnosis=diagnose_error_text(str(exc)))


def inspect_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return status(False, f"config file not found: {path}")
    try:
        import yaml
    except Exception as exc:  # noqa: BLE001
        return status(False, f"PyYAML import failed: {type(exc).__name__}: {exc}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            cfg = yaml.safe_load(handle)
    except Exception as exc:  # noqa: BLE001
        return status(False, f"could not parse YAML: {type(exc).__name__}: {exc}")
    if not isinstance(cfg, dict):
        return status(False, "YAML root is not a mapping")
    required = ["problem_type", "dataset", "environment", "training", "output_directory", "llm_backbone"]
    missing = [key for key in required if key not in cfg]
    env = cfg.get("environment") if isinstance(cfg.get("environment"), dict) else {}
    training = cfg.get("training") if isinstance(cfg.get("training"), dict) else {}
    arch = cfg.get("architecture") if isinstance(cfg.get("architecture"), dict) else {}
    warnings = []
    if env.get("use_deepspeed") and arch.get("backbone_dtype") in {"int4", "int8"}:
        warnings.append("DeepSpeed is incompatible with int4/int8 backbone_dtype in H2O LLM Studio")
    gpus = env.get("gpus")
    if env.get("use_deepspeed") and isinstance(gpus, list) and len(gpus) < 2:
        warnings.append("DeepSpeed requires at least two selected GPUs")
    if training.get("save_checkpoint") == "disable":
        warnings.append("checkpoint saving is disabled; prompt/export workflows will not have checkpoint.pth")
    return status(
        not missing,
        "config shape looks usable" if not missing else "config is missing required top-level keys",
        missing=missing,
        problem_type=cfg.get("problem_type"),
        output_directory=cfg.get("output_directory"),
        gpus=gpus,
        use_deepspeed=env.get("use_deepspeed"),
        backbone_dtype=arch.get("backbone_dtype"),
        epochs=training.get("epochs"),
        save_checkpoint=training.get("save_checkpoint"),
        warnings=warnings,
    )


def diagnose_error_text(text: str) -> list[str]:
    lower = text.lower()
    advice: list[str] = []
    if "missingcudaexception" in lower or "cuda_home" in lower or "cuda_home does not exist" in lower:
        advice.append("DeepSpeed CUDA extension checks need a CUDA toolkit with nvcc, not only an NVIDIA driver.")
        advice.append("Set CUDA_HOME or CUDA_PATH to the toolkit root and confirm $CUDA_HOME/bin/nvcc --version works.")
    if "no gpu selected" in lower:
        advice.append("Select at least one GPU in environment.gpus before running the trainer.")
    if "more gpus selected than available" in lower:
        advice.append("The config GPU list does not match the visible CUDA devices; reset environment.gpus or CUDA_VISIBLE_DEVICES.")
    if "deepspeed" in lower and "single gpu" in lower:
        advice.append("Disable DeepSpeed or run with at least two selected GPUs.")
    if "int4" in lower or "int8" in lower:
        advice.append("DeepSpeed is incompatible with int4/int8 backbone dtype; use float16 or bfloat16.")
    if "out-of-memory" in lower or "oom" in lower:
        advice.append("Reduce batch size, max length, model size, or enable LoRA/gradient checkpointing/DeepSpeed where compatible.")
    if "nan caught" in lower:
        advice.append("Reduce learning rate, change dtype, disable mixed precision, or add gradient clipping.")
    return advice


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="Optional YAML config to inspect statically.")
    parser.add_argument("--check-torch", action="store_true", help="Import torch and report CUDA availability.")
    parser.add_argument("--require-cuda", action="store_true", help="Return non-zero if torch CUDA is unavailable.")
    parser.add_argument("--check-cuda-home", action="store_true", help="Check CUDA_HOME/CUDA_PATH and nvcc.")
    parser.add_argument("--check-deepspeed", action="store_true", help="Import deepspeed and report common CUDA_HOME/nvcc failures.")
    parser.add_argument("--check-train-import", action="store_true", help="Import llm_studio.train; may trigger DeepSpeed import checks.")
    parser.add_argument("--diagnose-error", default="", help="Error text to classify into H2O LLM Studio recovery hints.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checks: dict[str, Any] = {
        "python": status(True, "python running", executable_name=Path(sys.executable).name, version=sys.version.split()[0], platform=platform.platform()),
        "distribution": check_distribution(),
        "import_llm_studio": check_import("llm_studio"),
    }
    if args.config:
        checks["config"] = inspect_config(args.config)
    if args.check_torch or args.require_cuda:
        checks["torch"] = check_torch(require_cuda=args.require_cuda)
    if args.check_cuda_home:
        checks["cuda_home"] = check_cuda_home()
    if args.check_deepspeed:
        checks["deepspeed"] = check_deepspeed()
    if args.check_train_import:
        checks["import_train"] = check_import("llm_studio.train")
    if args.diagnose_error:
        checks["diagnosis"] = status(True, "diagnosed supplied error text", advice=diagnose_error_text(args.diagnose_error))

    ok = all(item.get("ok", False) for item in checks.values() if isinstance(item, dict))
    if args.json:
        print(json.dumps({"ok": ok, "checks": checks}, indent=2, sort_keys=True))
    else:
        for name, item in checks.items():
            mark = "OK" if item.get("ok") else "FAIL"
            print(f"[{mark}] {name}: {item.get('message')}")
            for key, value in item.items():
                if key in {"ok", "message"} or value in (None, [], ""):
                    continue
                print(f"  {key}: {value}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
