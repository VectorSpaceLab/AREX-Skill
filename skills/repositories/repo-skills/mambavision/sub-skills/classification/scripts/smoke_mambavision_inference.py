#!/usr/bin/env python3
"""Safe MambaVision classification inference smoke.

Defaults avoid network downloads and use a tiny random RGB tensor. Use
--pretrained only when you intentionally want to load/download pretrained
weights to --model-path.
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib import metadata
from pathlib import Path
from typing import Any


MODEL_NAMES = (
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
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a no-download-by-default MambaVision random-input inference smoke.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model", default="mamba_vision_T", choices=MODEL_NAMES, help="MambaVision factory name.")
    parser.add_argument(
        "--device",
        default="auto",
        choices=("auto", "cpu", "cuda"),
        help="Device for model and random input. 'auto' selects CUDA when available.",
    )
    parser.add_argument("--height", type=int, default=64, help="Input tensor height.")
    parser.add_argument("--width", type=int, default=64, help="Input tensor width.")
    parser.add_argument("--channels", type=int, default=3, help="Input tensor channels; released checkpoints expect 3.")
    parser.add_argument("--batch-size", type=int, default=1, help="Random input batch size.")
    parser.add_argument("--seed", type=int, default=0, help="Torch random seed for the dummy tensor.")
    parser.add_argument(
        "--pretrained",
        action="store_true",
        help="Opt in to pretrained weight loading. May download to --model-path if the file is absent.",
    )
    parser.add_argument(
        "--model-path",
        default="",
        help="Destination/source file used by the factory when --pretrained is set. Required with --pretrained for explicit cache behavior.",
    )
    parser.add_argument(
        "--checkpoint-path",
        default="",
        help="Optional local checkpoint loaded after model construction via create_model(..., checkpoint_path=...).",
    )
    parser.add_argument(
        "--expect-classes",
        type=int,
        default=1000,
        help="Expected logits dimension for the classifier head.",
    )
    parser.add_argument(
        "--channels-last",
        action="store_true",
        help="Use channels-last memory format for the model and input tensor.",
    )
    return parser.parse_args()


def die(message: str, code: int = 2) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def pick_device(requested: str, torch_module: Any):
    if requested == "cuda":
        if not torch_module.cuda.is_available():
            die("CUDA was requested but torch.cuda.is_available() is False.")
        return torch_module.device("cuda")
    if requested == "auto":
        return torch_module.device("cuda" if torch_module.cuda.is_available() else "cpu")
    return torch_module.device("cpu")


def main() -> int:
    args = parse_args()

    if args.height <= 0 or args.width <= 0 or args.channels <= 0 or args.batch_size <= 0:
        die("--height, --width, --channels, and --batch-size must be positive integers.")
    if args.pretrained and not args.model_path:
        die("--pretrained can download weights; pass an explicit --model-path to make cache behavior intentional.")
    if args.checkpoint_path and not Path(args.checkpoint_path).is_file():
        die(f"--checkpoint-path does not exist or is not a file: {args.checkpoint_path}")

    try:
        import torch
        from mambavision import create_model
    except Exception as exc:  # pragma: no cover - user environment dependent
        die(f"Failed to import torch/mambavision: {exc}")

    device = pick_device(args.device, torch)
    if device.type == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.benchmark = True

    torch.manual_seed(args.seed)

    model_kwargs: dict[str, Any] = {}
    if args.channels != 3:
        model_kwargs["in_chans"] = args.channels
    if args.model_path:
        model_kwargs["model_path"] = args.model_path
    if args.checkpoint_path:
        model_kwargs["checkpoint_path"] = args.checkpoint_path

    model = create_model(args.model, pretrained=args.pretrained, **model_kwargs)
    model.eval().to(device)

    x = torch.rand(args.batch_size, args.channels, args.height, args.width, device=device)
    if args.channels_last:
        model = model.to(memory_format=torch.channels_last)
        x = x.contiguous(memory_format=torch.channels_last)

    with torch.inference_mode():
        logits = model(x)

    expected_shape = (args.batch_size, args.expect_classes)
    got_shape = tuple(logits.shape)
    if got_shape != expected_shape:
        die(f"Expected logits shape {expected_shape}, got {got_shape}.")
    finite = bool(torch.isfinite(logits).all().item())
    if not finite:
        die("Logits contain NaN or Inf values.")

    try:
        package_version = metadata.version("mambavision")
    except metadata.PackageNotFoundError:
        package_version = "unknown"

    result = {
        "status": "ok",
        "package": "mambavision",
        "package_version": package_version,
        "model": args.model,
        "pretrained": args.pretrained,
        "checkpoint_path_used": bool(args.checkpoint_path),
        "device": str(device),
        "cuda_name": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
        "input_shape": list(x.shape),
        "logits_shape": list(logits.shape),
        "logits_finite": finite,
        "logits_dtype": str(logits.dtype),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
