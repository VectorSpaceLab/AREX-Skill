#!/usr/bin/env python3
"""Template for exporting a SAM image embedding to `.npy` for ONNX/browser use."""

from __future__ import annotations

import argparse
from pathlib import Path

VALID_MODEL_TYPES = ("default", "vit_h", "vit_l", "vit_b")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare a Segment Anything image embedding for ONNX/browser inference."
    )
    parser.add_argument("--checkpoint", required=True, help="Path to the SAM model checkpoint.")
    parser.add_argument("--model-type", required=True, choices=VALID_MODEL_TYPES)
    parser.add_argument("--image", required=True, help="Image file used by the browser/runtime.")
    parser.add_argument("--output", required=True, help="Path to write the embedding .npy file.")
    parser.add_argument(
        "--device",
        default="auto",
        help="Torch device for embedding export, for example cuda or cpu. Use auto to prefer cuda when available.",
    )
    return parser


def load_rgb_image(path: str):
    try:
        import numpy as np
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Embedding export requires numpy and pillow installed in this environment.") from exc
    image = Image.open(path).convert("RGB")
    return np.asarray(image)


def resolve_device(requested_device: str) -> str:
    if requested_device != "auto":
        return requested_device
    try:
        import torch
    except ImportError as exc:
        raise SystemExit("Embedding export requires torch installed in this environment.") from exc
    return "cuda" if torch.cuda.is_available() else "cpu"


def require_segment_anything():
    try:
        from segment_anything import SamPredictor, sam_model_registry
    except ImportError as exc:
        raise SystemExit(
            "Could not import segment_anything. Install the Segment Anything package before exporting embeddings."
        ) from exc
    return SamPredictor, sam_model_registry


def main() -> None:
    args = build_parser().parse_args()
    device = resolve_device(args.device)
    SamPredictor, sam_model_registry = require_segment_anything()
    sam = sam_model_registry[args.model_type](checkpoint=args.checkpoint)
    sam.to(device=device)
    predictor = SamPredictor(sam)

    image = load_rgb_image(args.image)
    predictor.set_image(image, image_format="RGB")
    embedding = predictor.get_image_embedding().detach().cpu().numpy()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, embedding)
    print(f"Saved embedding {embedding.shape} to {output_path}")
    print("Use this embedding only with the same image, checkpoint, model type, and preprocessing path.")


if __name__ == "__main__":
    main()
