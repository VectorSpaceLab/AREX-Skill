#!/usr/bin/env python3
"""Run a deterministic LightGlue package smoke check without pretrained weights.

The check imports the public package, probes optional torch backends, and runs a
tiny synthetic `LightGlue(features=None, ...)` matcher forward pass. It avoids
model downloads and does not require the original repository checkout.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check LightGlue imports and a synthetic matcher forward pass."
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda", "mps"),
        default="auto",
        help="Device for the synthetic matcher. Auto prefers CUDA, then MPS, then CPU.",
    )
    parser.add_argument(
        "--num-keypoints0", type=int, default=5, help="Synthetic keypoints in image0."
    )
    parser.add_argument(
        "--num-keypoints1", type=int, default=6, help="Synthetic keypoints in image1."
    )
    parser.add_argument(
        "--descriptor-dim", type=int, default=8, help="Synthetic descriptor dimension."
    )
    return parser


def resolve_device(torch, choice: str):
    if choice == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    if choice == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false.")
    if choice == "mps" and not (
        hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    ):
        raise RuntimeError("MPS was requested but torch.backends.mps is unavailable.")
    return torch.device(choice)


def tensor_shape(value: Any):
    return list(value.shape) if hasattr(value, "shape") else None


def run(args: argparse.Namespace) -> Dict[str, Any]:
    if args.num_keypoints0 <= 0 or args.num_keypoints1 <= 0:
        raise ValueError("Synthetic keypoint counts must be positive.")
    if args.descriptor_dim <= 0 or args.descriptor_dim % 2:
        raise ValueError("Descriptor dim must be a positive even integer.")

    import torch
    import lightglue
    from lightglue import LightGlue

    device = resolve_device(torch, args.device)
    torch.manual_seed(7)

    matcher = LightGlue(
        features=None,
        input_dim=args.descriptor_dim,
        descriptor_dim=args.descriptor_dim,
        n_layers=1,
        num_heads=2,
        flash=False,
        depth_confidence=-1,
        width_confidence=-1,
        filter_threshold=0.0,
    ).eval().to(device)

    data = {
        "image0": {
            "keypoints": torch.rand(1, args.num_keypoints0, 2, device=device),
            "descriptors": torch.rand(
                1, args.num_keypoints0, args.descriptor_dim, device=device
            ),
            "image_size": torch.tensor([[64.0, 64.0]], device=device),
        },
        "image1": {
            "keypoints": torch.rand(1, args.num_keypoints1, 2, device=device),
            "descriptors": torch.rand(
                1, args.num_keypoints1, args.descriptor_dim, device=device
            ),
            "image_size": torch.tensor([[64.0, 64.0]], device=device),
        },
    }

    with torch.inference_mode():
        out = matcher(data)

    required = {
        "matches0",
        "matches1",
        "matching_scores0",
        "matching_scores1",
        "matches",
        "scores",
        "stop",
        "prune0",
        "prune1",
    }
    missing = sorted(required - set(out))
    if missing:
        raise RuntimeError(f"Synthetic matcher output is missing keys: {missing}")

    return {
        "ok": True,
        "module": getattr(lightglue, "__name__", "lightglue"),
        "device": str(device),
        "torch": {
            "version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "cuda_available": torch.cuda.is_available(),
            "mps_available": bool(
                hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
            ),
        },
        "output_shapes": {key: tensor_shape(out[key]) for key in sorted(required)},
        "stop": int(out["stop"]),
        "note": "features=None uses random untrained weights here; this smoke validates API shape, not match quality.",
    }


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        print(json.dumps(run(args), indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                    "hint": "Install LightGlue runtime dependencies, or rerun with --device cpu for a download-free API smoke check.",
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
