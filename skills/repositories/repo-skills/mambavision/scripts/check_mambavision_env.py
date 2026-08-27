#!/usr/bin/env python3
"""Check MambaVision package and optional downstream runtime readiness.

Safe defaults:
- no network access
- no dataset access
- no checkpoint downloads
- no training or evaluation launch
- forward smoke is opt-in and always uses pretrained=False
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import platform
import sys
from importlib import metadata
from typing import Any

BASE_IMPORTS = {
    "mambavision": "mambavision",
    "torch": "torch",
    "torchvision": "torchvision",
    "timm": "timm",
    "transformers": "transformers",
    "mamba_ssm": "mamba_ssm",
    "einops": "einops",
    "requests": "requests",
    "PIL": "Pillow",
    "tensorboardX": "tensorboardX",
}

OPENMMLAB_IMPORTS = {
    "mmengine": "mmengine",
    "mmcv": "mmcv",
    "mmdet": "mmdet",
    "mmseg": "mmsegmentation",
    "mmpretrain": "mmpretrain",
}

MODEL_NAMES = [
    "mamba_vision_T",
    "mamba_vision_T2",
    "mamba_vision_S",
    "mamba_vision_B",
    "mamba_vision_B_21k",
    "mamba_vision_L",
    "mamba_vision_L_21k",
    "mamba_vision_L2",
    "mamba_vision_L2_512_21k",
    "mamba_vision_L3_256_21k",
    "mamba_vision_L3_512_21k",
]


class HelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter,
):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check MambaVision import readiness and optionally run a no-download forward smoke.",
        formatter_class=HelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/check_mambavision_env.py\n"
            "  python scripts/check_mambavision_env.py --smoke --device cuda\n"
            "  python scripts/check_mambavision_env.py --include-openmmlab\n"
        ),
    )
    parser.add_argument("--include-openmmlab", action="store_true", help="Also import mmengine, mmcv, mmdet, mmseg, and mmpretrain.")
    parser.add_argument("--smoke", action="store_true", help="Run a no-download forward pass with create_model(..., pretrained=False).")
    parser.add_argument("--model", choices=MODEL_NAMES, default="mamba_vision_T", help="Model factory used for the smoke pass.")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto", help="Device for the optional smoke pass.")
    parser.add_argument("--height", type=int, default=64, help="Smoke input height.")
    parser.add_argument("--width", type=int, default=64, help="Smoke input width.")
    parser.add_argument("--channels", type=int, default=3, help="Smoke input channels.")
    parser.add_argument("--batch-size", type=int, default=1, help="Smoke batch size.")
    parser.add_argument("--expect-classes", type=int, default=1000, help="Expected classifier logits dimension.")
    parser.add_argument("--channels-last", action="store_true", help="Use channels-last memory format during the optional smoke pass.")
    parser.add_argument("--seed", type=int, default=0, help="Random seed used for the optional smoke tensor.")
    return parser.parse_args()


def dist_version(dist_name: str) -> str:
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return "unknown"


def probe_import(import_name: str, dist_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(import_name)
    except Exception as exc:  # pragma: no cover - deliberately reports environment state
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(module, "__version__", None) or dist_version(dist_name)
    return {"ok": True, "version": version}


def resolve_device(choice: str, torch_module: Any) -> str:
    if choice == "auto":
        return "cuda" if torch_module.cuda.is_available() else "cpu"
    if choice == "cuda" and not torch_module.cuda.is_available():
        raise RuntimeError("--device cuda was requested, but torch.cuda.is_available() is false")
    return choice


def collect_registry_info() -> dict[str, Any]:
    from mambavision.models.registry import create_model, list_models

    models = list_models()
    return {
        "create_model_signature": str(inspect.signature(create_model)),
        "registered_model_count": len(models),
        "registered_models": models,
    }


def run_smoke(args: argparse.Namespace) -> dict[str, Any]:
    import torch
    from mambavision.models.registry import create_model, list_models

    registered = set(list_models())
    if args.model not in registered:
        raise RuntimeError(f"Unknown model {args.model!r}; available models: {sorted(registered)}")

    device = resolve_device(args.device, torch)
    torch.manual_seed(args.seed)

    model = create_model(args.model, pretrained=False)
    model.eval()
    model.to(device)
    if args.channels_last:
        model.to(memory_format=torch.channels_last)

    x = torch.randn(args.batch_size, args.channels, args.height, args.width, device=device)
    if args.channels_last:
        x = x.contiguous(memory_format=torch.channels_last)

    with torch.no_grad():
        output = model(x)

    if not torch.is_tensor(output):
        raise RuntimeError(f"Expected tensor output from {args.model}, got {type(output).__name__}")
    if output.ndim != 2:
        raise RuntimeError(f"Expected 2D logits from {args.model}, got shape {tuple(output.shape)}")
    if output.shape[0] != args.batch_size:
        raise RuntimeError(f"Expected batch dimension {args.batch_size}, got {output.shape[0]}")
    if output.shape[1] != args.expect_classes:
        raise RuntimeError(f"Expected {args.expect_classes} classes, got {output.shape[1]}")
    finite = bool(torch.isfinite(output).all().item())
    if not finite:
        raise RuntimeError("Smoke logits contain non-finite values")

    return {
        "model": args.model,
        "device": device,
        "cuda_device_name": torch.cuda.get_device_name(0) if device == "cuda" else None,
        "input_shape": [args.batch_size, args.channels, args.height, args.width],
        "logits_shape": list(output.shape),
        "logits_dtype": str(output.dtype),
        "logits_finite": finite,
        "pretrained": False,
    }


def main() -> int:
    args = parse_args()
    summary: dict[str, Any] = {
        "status": "ok",
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "imports": {},
    }

    errors: list[str] = []
    for import_name, dist_name in BASE_IMPORTS.items():
        result = probe_import(import_name, dist_name)
        summary["imports"][import_name] = result
        if not result["ok"]:
            errors.append(f"{import_name}: {result['error']}")

    if summary["imports"].get("torch", {}).get("ok"):
        import torch

        summary["torch_cuda"] = {
            "available": bool(torch.cuda.is_available()),
            "cuda_version": torch.version.cuda,
            "device_count": torch.cuda.device_count(),
            "device_name_0": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        }

    if not errors:
        try:
            summary["mambavision_registry"] = collect_registry_info()
        except Exception as exc:  # pragma: no cover - reports environment state
            errors.append(f"registry: {type(exc).__name__}: {exc}")

    if args.include_openmmlab:
        summary["openmmlab_imports"] = {}
        for import_name, dist_name in OPENMMLAB_IMPORTS.items():
            result = probe_import(import_name, dist_name)
            summary["openmmlab_imports"][import_name] = result
            if not result["ok"]:
                errors.append(f"{import_name}: {result['error']}")

    if args.smoke and not errors:
        try:
            summary["smoke"] = run_smoke(args)
        except Exception as exc:  # pragma: no cover - reports environment state
            errors.append(f"smoke: {type(exc).__name__}: {exc}")

    if errors:
        summary["status"] = "error"
        summary["errors"] = errors

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
