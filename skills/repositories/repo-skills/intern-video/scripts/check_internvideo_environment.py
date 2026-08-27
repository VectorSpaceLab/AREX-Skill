#!/usr/bin/env python3
"""Conservative readiness checker for InternVideo workflows.

This script never installs packages, downloads checkpoints, or submits jobs. It
reports whether common Python packages, CUDA, launch commands, and user-provided
paths look ready for InternVideo tasks.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

OPTIONAL_MODULES = [
    "torch",
    "torchvision",
    "torchaudio",
    "decord",
    "av",
    "timm",
    "einops",
    "cv2",
    "transformers",
    "qwen_vl_utils",
    "deepspeed",
    "apex",
    "flash_attn",
    "fused_dense_lib",
    "dropout_layer_norm",
    "librosa",
    "soundfile",
    "wandb",
]
COMMANDS = ["srun", "torchrun", "nvcc", "nvidia-smi"]
ENV_VARS = [
    "INTERNVIDEO2_DATA_PATH",
    "INTERNVIDEO2_MODEL_PATH",
    "META_DATA_PATH",
    "WORK_DIR",
    "LOAD_FROM",
    "PROCESSOR_PATH",
    "GLOBAL_BATCH_SIZE",
    "CEPH_CONFIG",
]


def module_status(name: str) -> dict:
    spec = importlib.util.find_spec(name)
    return {"name": name, "available": spec is not None}


def torch_status() -> dict:
    if importlib.util.find_spec("torch") is None:
        return {"available": False, "cuda_available": False}
    try:
        import torch  # type: ignore

        status = {
            "available": True,
            "version": getattr(torch, "__version__", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_version": getattr(torch.version, "cuda", None),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            "devices": [],
        }
        if torch.cuda.is_available():
            for idx in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(idx)
                status["devices"].append(
                    {"index": idx, "name": torch.cuda.get_device_name(idx), "total_memory_gb": round(props.total_memory / 1024**3, 2)}
                )
        return status
    except Exception as exc:  # pragma: no cover - environment specific
        return {"available": True, "error": f"{type(exc).__name__}: {exc}", "cuda_available": False}


def path_status(value: str | None) -> dict | None:
    if not value:
        return None
    p = Path(value).expanduser()
    return {"path": value, "exists": p.exists(), "is_dir": p.is_dir(), "is_file": p.is_file()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check readiness for InternVideo workflows without side effects.")
    parser.add_argument("--data-root", help="Optional dataset root to check for existence.")
    parser.add_argument("--model-root", help="Optional model/checkpoint root to check for existence.")
    parser.add_argument("--require", action="append", default=[], help="Module or command name that must be available in --strict mode.")
    parser.add_argument("--strict", action="store_true", help="Return exit code 2 if required checks fail.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")
    args = parser.parse_args()

    report = {
        "python": {"executable": sys.executable, "version": sys.version.split()[0]},
        "modules": [module_status(m) for m in OPTIONAL_MODULES],
        "torch": torch_status(),
        "commands": [{"name": c, "path": shutil.which(c), "available": shutil.which(c) is not None} for c in COMMANDS],
        "env": {name: ("set" if os.environ.get(name) else "unset") for name in ENV_VARS},
        "paths": {"data_root": path_status(args.data_root), "model_root": path_status(args.model_root)},
        "warnings": [],
    }

    missing_required: list[str] = []
    available_modules = {item["name"] for item in report["modules"] if item["available"]}
    available_commands = {item["name"] for item in report["commands"] if item["available"]}
    for req in args.require:
        if req not in available_modules and req not in available_commands:
            missing_required.append(req)
    if args.data_root and not Path(args.data_root).expanduser().exists():
        missing_required.append("data-root")
    if args.model_root and not Path(args.model_root).expanduser().exists():
        missing_required.append("model-root")

    if not report["torch"].get("cuda_available"):
        report["warnings"].append("CUDA is not available to torch; do not run GPU-required InternVideo workflows.")
    if not shutil.which("srun"):
        report["warnings"].append("srun is unavailable; adapt SLURM launchers to local torchrun only if the user requests it.")
    if missing_required:
        report["warnings"].append("Missing required checks in strict mode: " + ", ".join(missing_required))

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']['version']}")
        print(f"Torch CUDA: {report['torch'].get('cuda_available')}")
        print("Available modules:", ", ".join(sorted(available_modules)) or "none")
        print("Available commands:", ", ".join(sorted(available_commands)) or "none")
        for warning in report["warnings"]:
            print("WARNING:", warning)
    return 2 if args.strict and missing_required else 0


if __name__ == "__main__":
    raise SystemExit(main())
