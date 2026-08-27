#!/usr/bin/env python3
"""Run CLIP image-text similarity for one image and comma-separated labels."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _split_labels(labels: str) -> List[str]:
    return [label.strip() for label in labels.split(",") if label.strip()]


def _default_device() -> str:
    import torch

    return "cuda" if torch.cuda.is_available() else "cpu"


def _resolve_device(requested_device: str) -> str:
    if requested_device != "auto":
        return requested_device
    return _default_device()


def _validate_model_arg(clip_module: Any, model: str) -> Tuple[bool, Optional[str]]:
    if model in clip_module.available_models():
        return True, None
    if os.path.isfile(model):
        return True, None
    valid_models = ", ".join(clip_module.available_models())
    return (
        False,
        f"Model '{model}' is neither a valid CLIP model name nor an existing checkpoint file. "
        f"Valid named models: {valid_models}",
    )


def run_similarity(args: argparse.Namespace) -> Dict[str, Any]:
    try:
        import torch
        from PIL import Image
        import clip
    except Exception as exc:  # pragma: no cover - environment-specific error path
        raise RuntimeError(f"failed to import dependencies: {type(exc).__name__}: {exc}") from exc

    labels = _split_labels(args.labels)
    if not labels:
        raise ValueError("provide at least one non-empty label via --labels")

    image_path = Path(args.image)
    if not image_path.is_file():
        raise FileNotFoundError(f"image file does not exist: {image_path}")

    valid_model, model_error = _validate_model_arg(clip, args.model)
    if not valid_model:
        raise ValueError(model_error)

    if args.offline and args.model in clip.available_models() and not args.download_root:
        raise ValueError(
            "--offline with a named model requires --download-root pointing at a pre-populated cache, "
            "or use --model with a local checkpoint path"
        )

    device = _resolve_device(args.device)
    model, preprocess = clip.load(
        args.model,
        device=device,
        jit=args.jit,
        download_root=args.download_root,
    )
    model.eval()

    image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
    text = clip.tokenize(labels, truncate=args.truncate).to(device)

    with torch.no_grad():
        logits_per_image, _ = model(image, text)
        probabilities = logits_per_image.softmax(dim=-1)[0]
        values, indices = probabilities.topk(min(args.top_k, len(labels)))

    predictions = [
        {
            "rank": rank,
            "label": labels[index.item()],
            "probability": float(value.item()),
        }
        for rank, (value, index) in enumerate(zip(values.cpu(), indices.cpu()), start=1)
    ]

    return {
        "model": args.model,
        "device": device,
        "jit": bool(args.jit),
        "image": str(image_path),
        "labels": labels,
        "top_k": predictions,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Score one image against comma-separated text labels with CLIP. Loading a named model may "
            "download a checkpoint if it is not already cached; pass a local checkpoint path to --model "
            "for offline use."
        )
    )
    parser.add_argument(
        "--image",
        required=True,
        help="Path to an input image readable by Pillow.",
    )
    parser.add_argument(
        "--labels",
        required=True,
        help="Comma-separated labels/classes, such as 'a dog,a cat,a diagram'.",
    )
    parser.add_argument(
        "--model",
        default="ViT-B/32",
        help="CLIP model name from clip.available_models() or a local checkpoint path. Default: %(default)s",
    )
    parser.add_argument(
        "--device",
        default="auto",
        help="Device for model and tensors: auto, cpu, cuda, cuda:0, etc. Default: %(default)s",
    )
    parser.add_argument(
        "--download-root",
        default=None,
        help="Optional CLIP cache/download directory for named models.",
    )
    parser.add_argument(
        "--jit",
        action="store_true",
        help="Load a JIT/TorchScript model when available. Defaults to eager loading.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of predictions to print. Capped by the number of labels. Default: %(default)s",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Allow clip.tokenize to truncate labels longer than the CLIP context length.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help=(
            "Fail early for named models unless --download-root is supplied. For strict offline use, "
            "prefer a local checkpoint path in --model."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of a text table.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.top_k < 1:
        print("--top-k must be at least 1", file=sys.stderr)
        return 2

    try:
        result = run_similarity(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Model: {result['model']}  Device: {result['device']}  JIT: {result['jit']}")
        print("Top predictions:")
        for item in result["top_k"]:
            print(f"{item['rank']:>2}. {item['label']}: {item['probability']:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
