#!/usr/bin/env python3
"""Smoke-check SMP save_pretrained/from_pretrained behavior with a tiny local model."""

from __future__ import annotations

import argparse
import json
import tempfile
import warnings
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create a small segmentation_models_pytorch model, save it to a "
            "temporary local directory, reload it with smp.from_pretrained, "
            "and print a JSON summary."
        )
    )
    parser.add_argument("--arch", default="unet", help="SMP architecture name for smp.create_model.")
    parser.add_argument("--encoder", default="resnet18", help="Encoder name to use for the smoke model.")
    parser.add_argument("--in-channels", type=int, default=3, help="Input channel count.")
    parser.add_argument("--classes", type=int, default=1, help="Saved model class count.")
    parser.add_argument(
        "--mismatch-classes",
        type=int,
        default=2,
        help="Class count to request when --class-mismatch is enabled.",
    )
    parser.add_argument(
        "--class-mismatch",
        action="store_true",
        help="Also reload with classes changed and strict=False.",
    )
    parser.add_argument(
        "--keep-dir",
        type=Path,
        default=None,
        help="Optional directory to keep the saved model instead of using a temporary directory.",
    )
    return parser


def tensor_shape(value: Any) -> list[int] | list[list[int]]:
    if isinstance(value, tuple):
        return [list(item.shape) for item in value]
    return list(value.shape)


def main() -> int:
    args = build_parser().parse_args()

    import torch
    import segmentation_models_pytorch as smp

    save_dir_context = None
    if args.keep_dir is None:
        save_dir_context = tempfile.TemporaryDirectory()
        save_dir = Path(save_dir_context.name)
    else:
        save_dir = args.keep_dir
        save_dir.mkdir(parents=True, exist_ok=True)

    try:
        model = smp.create_model(
            args.arch,
            encoder_name=args.encoder,
            encoder_weights=None,
            in_channels=args.in_channels,
            classes=args.classes,
        ).eval()
        model.save_pretrained(save_dir, dataset="smoke-test", metrics={"status": "ok"})
        restored = smp.from_pretrained(str(save_dir)).eval()

        sample = torch.randn(1, args.in_channels, 64, 64)
        with torch.inference_mode():
            restored_output = restored(sample)

        result: dict[str, Any] = {
            "ok": True,
            "arch": args.arch,
            "encoder": args.encoder,
            "save_dir_kept": args.keep_dir is not None,
            "files": sorted(path.name for path in save_dir.iterdir()),
            "restored_class": restored.__class__.__name__,
            "restored_output_shape": tensor_shape(restored_output),
        }

        if args.class_mismatch:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                changed = smp.from_pretrained(
                    str(save_dir), classes=args.mismatch_classes, strict=False
                ).eval()
            result["class_mismatch"] = {
                "requested_classes": args.mismatch_classes,
                "head_out_channels": int(changed.segmentation_head[0].out_channels),
                "warnings": [str(item.message) for item in caught],
            }

        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    finally:
        if save_dir_context is not None:
            save_dir_context.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
