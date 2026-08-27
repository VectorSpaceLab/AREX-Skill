#!/usr/bin/env python3
"""Read-only ESPnet environment checker."""
from __future__ import annotations
import argparse
import importlib.util
import json
import shutil
from typing import Any

MODULE_GROUPS = {
    "base": ["espnet2", "espnet3", "numpy", "torch", "torchaudio", "soundfile", "yaml", "omegaconf", "hydra", "lhotse"],
    "asr": ["editdistance", "espnet_model_zoo"],
    "tts": ["pyworld", "jaconv", "jamo", "pypinyin"],
    "enh": ["ci_sdr", "fast_bss_eval"],
    "speechlm": ["transformers", "huggingface_hub", "datasets"],
    "optional-specialized": ["flash_attn", "k2", "s3prl", "whisper", "kenlm", "fairseq", "phonemizer", "mir_eval"],
}
EXEC_GROUPS = {
    "host-audio": ["sox", "ffmpeg", "flac", "sph2pipe"],
    "tokenizer-cli": ["spm_train", "spm_encode", "spm_decode"],
    "scoring": ["sclite", "PESQ", "BeamformIt"],
    "build": ["cmake"],
}
ALL_GROUPS = sorted(set(MODULE_GROUPS) | set(EXEC_GROUPS) | {"torch"})


def module_status(name: str) -> dict[str, Any]:
    return {"name": name, "available": importlib.util.find_spec(name) is not None}


def executable_status(name: str) -> dict[str, Any]:
    return {"name": name, "available": shutil.which(name) is not None}


def torch_status(require_cuda: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {"name": "torch", "available": False}
    try:
        import torch
    except Exception as exc:  # noqa: BLE001 - diagnostic tool should report any torch import failure.
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result
    result.update(
        {
            "available": True,
            "version": getattr(torch, "__version__", None),
            "cuda_version": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            "cudnn_available": bool(torch.backends.cudnn.is_available()),
            "nccl_available": bool(torch.distributed.is_nccl_available()) if hasattr(torch, "distributed") else False,
        }
    )
    if require_cuda and not result["cuda_available"]:
        result["error"] = "CUDA was required but torch.cuda.is_available() is false."
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ESPnet modules, optional tools, and torch backend readiness.")
    parser.add_argument("--groups", nargs="+", default=["base", "torch"], choices=ALL_GROUPS)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--require-cuda", action="store_true")
    parser.add_argument("--list-groups", action="store_true")
    args = parser.parse_args()
    if args.list_groups:
        print(chr(10).join(ALL_GROUPS))
        return 0
    modules = []
    executables = []
    backend = None
    for group in args.groups:
        if group == "torch":
            backend = torch_status(args.require_cuda)
        modules.extend(module_status(name) for name in MODULE_GROUPS.get(group, []))
        executables.extend(executable_status(name) for name in EXEC_GROUPS.get(group, []))
    backend = backend or torch_status(args.require_cuda)
    ok = (
        all(item["available"] for item in modules)
        and all(item["available"] for item in executables)
        and backend.get("available", False)
        and (not args.require_cuda or backend.get("cuda_available", False))
    )
    payload = {"ok": ok, "modules": modules, "executables": executables, "torch": backend}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for item in modules:
            print(f"[{'x' if item['available'] else ' '}] module {item['name']}")
        for item in executables:
            print(f"[{'x' if item['available'] else ' '}] executable {item['name']}")
        print(f"[{'x' if backend.get('available') else ' '}] torch {backend.get('version', '')}")
        print(f"[{'x' if backend.get('cuda_available') else ' '}] torch cuda {backend.get('cuda_version', '')}")
    return 0 if (ok or not args.strict) else 1


if __name__ == "__main__":
    raise SystemExit(main())
