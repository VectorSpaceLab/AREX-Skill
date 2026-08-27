#!/usr/bin/env python3
"""Safe Pytorch-UNet prediction/evaluation smoke check.

This script performs a no-download prediction path using the active Python
environment. It creates a tiny synthetic image and a temporary dummy UNet
checkpoint containing mask_values, loads that checkpoint, calls predict_img and
mask_to_image, validates output size/class IDs, optionally saves the converted
mask, and prints JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence


def _emit(payload: Dict[str, Any], exit_code: int = 0) -> None:
    print(json.dumps(payload, sort_keys=True))
    raise SystemExit(exit_code)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a safe Pytorch-UNet prediction smoke check")
    parser.add_argument("--classes", type=int, default=2, help="UNet n_classes; 1 uses binary threshold mode")
    parser.add_argument("--channels", type=int, choices=(1, 3), default=3, help="Synthetic input channels")
    parser.add_argument("--width", type=int, default=32, help="Synthetic image width")
    parser.add_argument("--height", type=int, default=32, help="Synthetic image height")
    parser.add_argument("--scale", type=float, default=1.0, help="Scale factor passed to predict_img")
    parser.add_argument("--threshold", type=float, default=0.5, help="Binary threshold passed to predict_img")
    parser.add_argument("--bilinear", action="store_true", help="Construct UNet with bilinear upsampling")
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "auto"),
        default="cpu",
        help="Execution device. Default is CPU for portable checks.",
    )
    parser.add_argument("--require-cuda", action="store_true", help="Fail if CUDA is unavailable")
    parser.add_argument(
        "--palette",
        choices=("default", "display", "rgb"),
        default="default",
        help="mask_values palette stored in the dummy checkpoint",
    )
    parser.add_argument("--save-mask", type=Path, help="Optional path where the converted predicted mask should be saved")
    parser.add_argument("--seed", type=int, default=0, help="Manual seed for deterministic dummy weights and image")
    parser.add_argument(
        "--repo-root",
        "--import-root",
        dest="import_root",
        type=Path,
        default=Path.cwd(),
        help="Directory to prepend to sys.path for source-checkout imports; defaults to current working directory",
    )
    return parser.parse_args()


def make_mask_values(classes: int, palette: str) -> List[Any]:
    # Binary n_classes==1 still produces mask IDs 0 and 1 after thresholding, so
    # it needs two output values. Multiclass needs at least one value per class.
    length = 2 if classes == 1 else classes
    if palette == "rgb":
        base = [
            [0, 0, 0],
            [255, 0, 0],
            [0, 255, 0],
            [0, 0, 255],
            [255, 255, 0],
            [255, 0, 255],
            [0, 255, 255],
        ]
        while len(base) < length:
            i = len(base)
            base.append([(37 * i) % 256, (67 * i) % 256, (97 * i) % 256])
        return base[:length]
    if palette == "display":
        if length == 1:
            return [0]
        return [round(i * 255 / (length - 1)) for i in range(length)]
    return list(range(length))


def make_image(width: int, height: int, channels: int, seed: int):
    import numpy as np
    from PIL import Image

    rng = np.random.default_rng(seed)
    if channels == 1:
        # Use a deterministic gradient plus light noise so preprocessing covers
        # non-constant grayscale images.
        yy, xx = np.mgrid[0:height, 0:width]
        arr = ((xx * 5 + yy * 3 + rng.integers(0, 8, size=(height, width))) % 256).astype("uint8")
        return Image.fromarray(arr, mode="L")

    yy, xx = np.mgrid[0:height, 0:width]
    arr = np.stack(
        [
            (xx * 5 + rng.integers(0, 8, size=(height, width))) % 256,
            (yy * 7 + rng.integers(0, 8, size=(height, width))) % 256,
            ((xx + yy) * 3 + rng.integers(0, 8, size=(height, width))) % 256,
        ],
        axis=-1,
    ).astype("uint8")
    return Image.fromarray(arr, mode="RGB")


def add_import_root(path: Path) -> None:
    root = str(path.resolve())
    if root not in sys.path:
        sys.path.insert(0, root)


def normalize_unique(values: Sequence[Any]) -> List[int]:
    return sorted(int(v) for v in values)


def main() -> None:
    args = parse_args()

    if args.classes <= 0:
        _emit({"ok": False, "error": "--classes must be a positive integer", "args": vars(args)}, 2)
    if args.width < 16 or args.height < 16:
        _emit({"ok": False, "error": "--width and --height must be at least 16", "args": vars(args)}, 2)
    if not (0 < args.scale <= 1):
        _emit({"ok": False, "error": "--scale must satisfy 0 < scale <= 1", "args": vars(args)}, 2)
    if int(args.scale * args.width) < 16 or int(args.scale * args.height) < 16:
        _emit(
            {
                "ok": False,
                "error": "scaled dimensions are too small for a safe UNet smoke check",
                "scaled_width": int(args.scale * args.width),
                "scaled_height": int(args.scale * args.height),
            },
            2,
        )

    add_import_root(args.import_root)

    try:
        import numpy as np
        import torch
        from predict import mask_to_image, predict_img
        from unet import UNet
    except Exception as exc:  # pragma: no cover - environment-dependent diagnostic
        _emit(
            {
                "ok": False,
                "stage": "import",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "hint": "Run from an environment where Pytorch-UNet modules and runtime dependencies are importable.",
            },
            1,
        )

    cuda_available = bool(torch.cuda.is_available())
    if args.require_cuda and not cuda_available:
        _emit(
            {
                "ok": False,
                "stage": "device",
                "error": "CUDA was required but torch.cuda.is_available() is false",
                "cuda_available": cuda_available,
                "torch_version": torch.__version__,
            },
            1,
        )

    if args.require_cuda:
        device_name = "cuda"
    elif args.device == "auto":
        device_name = "cuda" if cuda_available else "cpu"
    else:
        device_name = args.device

    if device_name == "cuda" and not cuda_available:
        _emit(
            {
                "ok": False,
                "stage": "device",
                "error": "CUDA device requested but torch.cuda.is_available() is false",
                "cuda_available": cuda_available,
                "torch_version": torch.__version__,
            },
            1,
        )

    mask_values = make_mask_values(args.classes, args.palette)
    img = make_image(args.width, args.height, args.channels, args.seed)
    device = torch.device(device_name)

    try:
        torch.manual_seed(args.seed)
        start = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="pytorch_unet_prediction_smoke_") as tmp:
            checkpoint_path = Path(tmp) / "dummy_unet_checkpoint.pth"

            source_net = UNet(n_channels=args.channels, n_classes=args.classes, bilinear=args.bilinear)
            state_dict = source_net.state_dict()
            state_dict["mask_values"] = mask_values
            torch.save(state_dict, checkpoint_path)

            net = UNet(n_channels=args.channels, n_classes=args.classes, bilinear=args.bilinear)
            net.to(device=device)
            try:
                loaded = torch.load(checkpoint_path, map_location=device, weights_only=True)
            except TypeError:
                # Older PyTorch releases do not accept weights_only. The file is
                # generated by this script in a temporary directory, so the
                # fallback does not load an untrusted external checkpoint.
                loaded = torch.load(checkpoint_path, map_location=device)
            loaded_mask_values = loaded.pop("mask_values", [0, 1])
            net.load_state_dict(loaded)

            mask = predict_img(
                net=net,
                full_img=img,
                device=device,
                scale_factor=args.scale,
                out_threshold=args.threshold,
            )
            if tuple(mask.shape) != (args.height, args.width):
                _emit(
                    {
                        "ok": False,
                        "stage": "predict_img",
                        "error": "unexpected mask shape",
                        "expected_shape": [args.height, args.width],
                        "actual_shape": list(mask.shape),
                    },
                    1,
                )

            unique_ids = normalize_unique(np.unique(mask).tolist())
            max_allowed = 1 if args.classes == 1 else args.classes - 1
            if unique_ids and (unique_ids[0] < 0 or unique_ids[-1] > max_allowed):
                _emit(
                    {
                        "ok": False,
                        "stage": "predict_img",
                        "error": "predicted class IDs outside expected range",
                        "unique_mask_ids": unique_ids,
                        "expected_min": 0,
                        "expected_max": max_allowed,
                    },
                    1,
                )

            pil_mask = mask_to_image(mask, loaded_mask_values)
            if tuple(pil_mask.size) != (args.width, args.height):
                _emit(
                    {
                        "ok": False,
                        "stage": "mask_to_image",
                        "error": "unexpected output image size",
                        "expected_size": [args.width, args.height],
                        "actual_size": list(pil_mask.size),
                    },
                    1,
                )

            saved_mask = None
            if args.save_mask is not None:
                args.save_mask.parent.mkdir(parents=True, exist_ok=True)
                pil_mask.save(args.save_mask)
                saved_mask = str(args.save_mask)

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        _emit(
            {
                "ok": True,
                "stages": ["synthetic_image", "dummy_checkpoint", "predict_img", "mask_to_image"],
                "n_channels": args.channels,
                "n_classes": args.classes,
                "bilinear": bool(args.bilinear),
                "scale": args.scale,
                "threshold": args.threshold,
                "image_size": [args.width, args.height],
                "mask_shape": [args.height, args.width],
                "output_size": [args.width, args.height],
                "unique_mask_ids": unique_ids,
                "mask_values": loaded_mask_values,
                "palette": args.palette,
                "saved_mask": saved_mask,
                "device": str(device),
                "cuda_available": cuda_available,
                "torch_version": torch.__version__,
                "elapsed_ms": round(elapsed_ms, 3),
            },
            0,
        )
    except Exception as exc:  # pragma: no cover - runtime diagnostic path
        _emit(
            {
                "ok": False,
                "stage": "runtime",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "device": str(device),
                "torch_version": getattr(torch, "__version__", "unknown"),
                "hint": "Check imports, checkpoint/class/bilinear choices, image dimensions, scale, and device availability.",
            },
            1,
        )


if __name__ == "__main__":
    main()
