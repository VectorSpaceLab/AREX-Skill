#!/usr/bin/env python3
"""Inspect the installed palm_rlhf_pytorch package safely.

This helper is safe to run from any working directory. It imports the installed
package, prints verified package metadata, and optionally performs a tiny CUDA
availability check.

Example:
    python scripts/inspect_palm_rlhf.py --device auto --check-cuda
"""
from __future__ import annotations

import argparse
import inspect
import json
import sys
from importlib.metadata import version


def choose_device(requested: str) -> str:
    if requested != "auto":
        return requested
    try:
        import torch
    except Exception:
        return "cpu"
    return "cuda" if torch.cuda.is_available() else "cpu"


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect the installed palm_rlhf_pytorch package.")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto", help="Device to report for the tiny smoke check.")
    parser.add_argument("--check-cuda", action="store_true", help="If set, print torch CUDA availability and allocate a tiny tensor when possible.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of a human summary.")
    args = parser.parse_args()

    import palm_rlhf_pytorch as pkg
    from palm_rlhf_pytorch import PaLM, RewardModel, RLHFTrainer, ActorCritic, ImplicitPRM

    info = {
        "distribution": version("PaLM-rlhf-pytorch"),
        "module": pkg.__name__,
        "module_file": pkg.__file__,
        "public_names": ["PaLM", "RewardModel", "RLHFTrainer", "ActorCritic", "ImplicitPRM"],
        "signatures": {
            "PaLM": str(inspect.signature(PaLM.__init__)),
            "RewardModel": str(inspect.signature(RewardModel.__init__)),
            "RLHFTrainer": str(inspect.signature(RLHFTrainer.__init__)),
            "ActorCritic": str(inspect.signature(ActorCritic.__init__)),
            "ImplicitPRM": str(inspect.signature(ImplicitPRM.__init__)),
        },
        "device": choose_device(args.device),
    }

    if args.check_cuda:
        import torch
        info["torch_version"] = torch.__version__
        info["torch_cuda"] = torch.version.cuda
        info["cuda_available"] = torch.cuda.is_available()
        info["cuda_device_count"] = torch.cuda.device_count()
        if torch.cuda.is_available():
            info["cuda_device_name"] = torch.cuda.get_device_name(0)
            info["cuda_device_capability"] = torch.cuda.get_device_capability(0)
            torch.empty((1,), device="cuda")

    if args.json:
        print(json.dumps(info, indent=2, sort_keys=True))
    else:
        print(f"distribution: {info['distribution']}")
        print(f"module: {info['module']} ({info['module_file']})")
        print(f"device: {info['device']}")
        for name, sig in info["signatures"].items():
            print(f"{name}: {sig}")
        if args.check_cuda:
            print(f"torch: {info['torch_version']} | cuda: {info['torch_cuda']} | available: {info['cuda_available']} | count: {info['cuda_device_count']}")
            if info["cuda_available"]:
                print(f"cuda device 0: {info['cuda_device_name']} {info['cuda_device_capability']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
