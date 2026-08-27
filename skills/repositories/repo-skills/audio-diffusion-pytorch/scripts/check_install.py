#!/usr/bin/env python3
"""Check an audio-diffusion-pytorch installation.

This helper is safe by default: it imports the installed package, reports key
versions and optional dependency availability, and can optionally show public
API signatures or allocate a tiny CUDA tensor when explicitly requested.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from importlib import metadata


PUBLIC_OBJECTS = [
    "DiffusionModel",
    "UNetV0",
    "VDiffusion",
    "VSampler",
    "VInpainter",
    "DiffusionUpsampler",
    "DiffusionVocoder",
    "DiffusionAE",
    "DiffusionAR",
]

OPTIONAL_MODULES = {
    "transformers": "text conditioning with the default T5 embedder",
    "audio_encoders_pytorch": "README-style DiffusionAE encoder examples",
    "auraloss": "README/test-style custom spectral loss examples",
}


def version_or_none(distribution: str):
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def import_optional(name: str) -> bool:
    try:
        importlib.import_module(name)
        return True
    except Exception:
        return False


def collect(show_signatures: bool, check_cuda: bool) -> dict:
    try:
        import torch
        import torchaudio
        import audio_diffusion_pytorch as adp
    except Exception as exc:  # pragma: no cover - diagnostic output path
        return {
            "status": "error",
            "error_type": exc.__class__.__name__,
            "error": str(exc),
            "hint": "Install with `pip install audio-diffusion-pytorch` before using this skill.",
        }

    result = {
        "status": "ok",
        "distributions": {
            "audio-diffusion-pytorch": version_or_none("audio-diffusion-pytorch"),
            "torch": version_or_none("torch"),
            "torchaudio": version_or_none("torchaudio"),
            "a-unet": version_or_none("a-unet"),
            "transformers": version_or_none("transformers"),
        },
        "imports": {
            "audio_diffusion_pytorch": True,
            "torch": True,
            "torchaudio": True,
        },
        "torch_backend": {
            "torch_version": getattr(torch, "__version__", None),
            "torchaudio_version": getattr(torchaudio, "__version__", None),
            "cuda_build": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()),
        },
        "optional_modules": {
            module: {
                "available": import_optional(module),
                "used_for": purpose,
            }
            for module, purpose in OPTIONAL_MODULES.items()
        },
    }

    if check_cuda:
        if torch.cuda.is_available():
            tensor = torch.empty((1,), device="cuda")
            result["cuda_allocation"] = {"status": "ok", "device": str(tensor.device)}
        else:
            result["cuda_allocation"] = {"status": "unavailable"}

    if show_signatures:
        signatures = {}
        for name in PUBLIC_OBJECTS:
            obj = getattr(adp, name, None)
            if obj is None:
                signatures[name] = None
                continue
            try:
                signatures[name] = str(inspect.signature(obj))
            except (TypeError, ValueError):
                signatures[name] = "<signature unavailable>"
        result["public_signatures"] = signatures

    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check audio-diffusion-pytorch imports and optional dependencies.")
    parser.add_argument("--show-signatures", action="store_true", help="Include public constructor signatures.")
    parser.add_argument("--check-cuda", action="store_true", help="If CUDA is available, allocate one tiny tensor on cuda:0.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    result = collect(show_signatures=args.show_signatures, check_cuda=args.check_cuda)
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
