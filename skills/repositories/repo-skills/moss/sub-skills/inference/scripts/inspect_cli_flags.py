#!/usr/bin/env python3
"""Validate documented MOSS CLI flag combinations without importing torch or loading checkpoints."""

from __future__ import annotations

import argparse
import json
from typing import Dict, List

PYTORCH_MODELS = [
    "OpenMOSS-Team/moss-moon-003-sft",
    "OpenMOSS-Team/moss-moon-003-sft-int8",
    "OpenMOSS-Team/moss-moon-003-sft-int4",
]


def validate_pytorch(model_name: str, gpu: str) -> Dict[str, object]:
    devices = [part.strip() for part in gpu.split(",") if part.strip()]
    quantized = model_name.endswith("-int8") or model_name.endswith("-int4")
    ok = model_name in PYTORCH_MODELS and not (quantized and len(devices) > 1)
    return {
        "ok": ok,
        "runner": "bundled run_moss_generation.py template",
        "model_name": model_name,
        "gpu": gpu,
        "num_gpus": len(devices),
        "quantized": quantized,
        "command": f"python run_moss_generation.py --query '<your prompt>' --model-name {model_name} --gpu {gpu}",
        "flags": {"--model-name": PYTORCH_MODELS, "--gpu": "comma-separated CUDA device ids"},
        "warning": "Quantized checkpoints are single-GPU only in the MOSS runtime." if quantized and len(devices) > 1 else None,
    }


def jittor_summary(model_name: str, gpu: bool, method: str) -> Dict[str, object]:
    return {
        "runner": "optional Jittor source backend (no bundled executable)",
        "model_name": model_name,
        "gpu": gpu,
        "generate": method,
        "command": None,
        "bundled_alternative": f"python run_moss_generation.py --query '<your prompt>' --model-name {model_name} --gpu 0",
        "flags": {
            "model_name": PYTORCH_MODELS,
            "generate": ["sample", "greedy"],
            "temperature": "sampling temperature; sample mode only",
            "top_p": "nucleus sampling p; sample mode only",
            "top_k": "top-k sampling k; sample mode only",
            "max_len": "maximum generated sequence length",
            "gpu": "enable Jittor CUDA instead of CPU",
        },
        "warning": "The optional Jittor backend requires a separately installed jittor runtime and checkpoint conversion; this generated skill bundles PyTorch dry-run and execution templates only.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize and validate MOSS CLI flags safely.")
    parser.add_argument("--runner", choices=["pytorch", "jittor"], default="pytorch")
    parser.add_argument("--model-name", default="OpenMOSS-Team/moss-moon-003-sft-int4", choices=PYTORCH_MODELS)
    parser.add_argument("--gpu", default="0", help="For PyTorch: comma-separated CUDA devices; for Jittor use any value to document --gpu.")
    parser.add_argument("--jittor-gpu", action="store_true", help="Document a Jittor command with --gpu.")
    parser.add_argument("--generate", choices=["sample", "greedy"], default="sample", help="Jittor generation method.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.runner == "pytorch":
        report = validate_pytorch(args.model_name, args.gpu)
    else:
        report = jittor_summary(args.model_name, args.jittor_gpu, args.generate)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("ok", True) else 2


if __name__ == "__main__":
    raise SystemExit(main())
