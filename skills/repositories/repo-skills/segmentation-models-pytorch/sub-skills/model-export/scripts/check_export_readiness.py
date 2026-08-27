#!/usr/bin/env python3
"""Report SMP model readiness signals for ONNX/TorchScript/torch.export/compile."""

from __future__ import annotations

import argparse
import importlib.util
import json
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Construct a small segmentation_models_pytorch model with "
            "encoder_weights=None and print JSON readiness information for "
            "deployment export paths."
        )
    )
    parser.add_argument("--arch", default="unet", help="SMP architecture name for smp.create_model.")
    parser.add_argument("--encoder", default="resnet18", help="Encoder name to use for the readiness model.")
    parser.add_argument("--in-channels", type=int, default=3, help="Input channel count.")
    parser.add_argument("--classes", type=int, default=1, help="Output class count.")
    parser.add_argument("--height", type=int, default=64, help="Dry-run input height.")
    parser.add_argument("--width", type=int, default=64, help="Dry-run input width.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run one eager forward pass and include the output shape or error.",
    )
    parser.add_argument(
        "--check-script",
        action="store_true",
        help="Attempt torch.jit.script when the model advertises scriptability.",
    )
    return parser


def package_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def shape_of(output: Any) -> list[int] | list[list[int]]:
    if isinstance(output, tuple):
        return [list(item.shape) for item in output]
    return list(output.shape)


def main() -> int:
    args = build_parser().parse_args()

    import torch
    import segmentation_models_pytorch as smp

    result: dict[str, Any] = {
        "ok": True,
        "torch_version": torch.__version__,
        "smp_version": getattr(smp, "__version__", None),
        "onnx_available": package_available("onnx"),
        "onnxruntime_available": package_available("onnxruntime"),
        "has_torch_export": hasattr(torch, "export") and hasattr(torch.export, "export"),
        "has_torch_compile": hasattr(torch, "compile"),
        "arch": args.arch,
        "encoder": args.encoder,
    }

    try:
        model = smp.create_model(
            args.arch,
            encoder_name=args.encoder,
            encoder_weights=None,
            in_channels=args.in_channels,
            classes=args.classes,
        ).eval()
    except Exception as exc:  # pragma: no cover - diagnostic script path
        result.update({"ok": False, "model_error": repr(exc)})
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    result["model_class"] = model.__class__.__name__
    result["requires_divisible_input_shape"] = bool(
        getattr(model, "requires_divisible_input_shape", False)
    )
    result["flags"] = {
        "torch_scriptable": bool(getattr(model, "_is_torch_scriptable", False)),
        "torch_exportable": bool(getattr(model, "_is_torch_exportable", False)),
        "torch_compilable": bool(getattr(model, "_is_torch_compilable", False)),
    }

    sample = torch.randn(1, args.in_channels, args.height, args.width)

    if args.dry_run:
        try:
            with torch.inference_mode():
                output = model(sample)
            result["dry_run"] = {"ok": True, "output_shape": shape_of(output)}
        except Exception as exc:  # pragma: no cover - diagnostic script path
            result["dry_run"] = {"ok": False, "error": repr(exc)}

    if args.check_script:
        if result["flags"]["torch_scriptable"]:
            try:
                scripted = torch.jit.script(model)
                with torch.inference_mode():
                    output = scripted(sample)
                result["torch_script"] = {"ok": True, "output_shape": shape_of(output)}
            except Exception as exc:  # pragma: no cover - diagnostic script path
                result["torch_script"] = {"ok": False, "error": repr(exc)}
        else:
            result["torch_script"] = {
                "ok": False,
                "skipped": "model advertises _is_torch_scriptable=False",
            }

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
