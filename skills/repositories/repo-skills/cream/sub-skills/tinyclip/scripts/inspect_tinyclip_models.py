#!/usr/bin/env python3
"""Inspect TinyCLIP / open_clip model configs and constructors.

This helper reads the installed `open_clip` package, lists available model
configs, and can optionally instantiate one model for a small smoke check.
It does not download checkpoints.
"""

from __future__ import annotations

import argparse
import json
import inspect
from pprint import pprint

import torch


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect TinyCLIP model configs")
    parser.add_argument("--model", help="Optional model name to inspect or instantiate")
    parser.add_argument("--pretrained", default="", help="Pretrained tag/path passed to open_clip.create_model")
    parser.add_argument("--device", default="cpu", help="Device for optional instantiation")
    parser.add_argument("--instantiate", action="store_true", help="Instantiate the selected model")
    args = parser.parse_args()

    import open_clip
    from open_clip.factory import create_model, get_model_config, list_models, create_model_and_transforms

    print("available_models:")
    pprint(list_models())
    print("create_model_signature:", inspect.signature(create_model))
    print("create_model_and_transforms_signature:", inspect.signature(create_model_and_transforms))

    if args.model:
        cfg = get_model_config(args.model)
        if cfg is None:
            raise SystemExit(f"unknown model: {args.model}")
        print("model_config:")
        print(json.dumps(cfg, indent=2, sort_keys=True))

        if args.instantiate:
            device = torch.device(args.device)
            model = create_model(args.model, pretrained=args.pretrained, device=device)
            print("instantiated_model:", type(model).__name__)
            if hasattr(model, "visual") and hasattr(model.visual, "image_size"):
                print("visual_image_size:", model.visual.image_size)
            if hasattr(model, "text"):  # open_clip CLIP model
                print("has_text_tower:", True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
