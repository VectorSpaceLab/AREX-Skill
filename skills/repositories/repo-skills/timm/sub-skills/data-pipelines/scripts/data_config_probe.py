#!/usr/bin/env python3
"""Probe timm model data config and transform construction without a dataset."""

import argparse
import json
from typing import Any

import timm
from timm.data import create_transform, resolve_data_config


def _json_safe(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if hasattr(value, "__name__"):
        return value.__name__
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _summarize_transform(transform: Any) -> Any:
    transforms = getattr(transform, "transforms", None)
    if transforms is not None:
        return {
            "type": type(transform).__name__,
            "steps": [str(step) for step in transforms],
        }
    if isinstance(transform, tuple):
        return {
            "type": "tuple",
            "items": [_summarize_transform(item) for item in transform],
        }
    return {
        "type": type(transform).__name__,
        "repr": str(transform),
    }


def _parse_input_size(value: str) -> tuple[int, int, int]:
    parts = [int(part.strip()) for part in value.split(",")]
    if len(parts) == 1:
        return (3, parts[0], parts[0])
    if len(parts) == 2:
        return (3, parts[0], parts[1])
    if len(parts) == 3:
        return (parts[0], parts[1], parts[2])
    raise argparse.ArgumentTypeError("input size must be H, H,W, or C,H,W")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="resnet50", help="timm model name to instantiate with pretrained=False")
    parser.add_argument("--input-size", type=_parse_input_size, help="Override input size as H, H,W, or C,H,W")
    parser.add_argument("--img-size", type=int, help="Override square image size")
    parser.add_argument("--use-test-size", action="store_true", help="Prefer test_input_size/test_crop_pct when present")
    parser.add_argument("--train-re-prob", type=float, default=0.0, help="Random erasing probability for train transform summary")
    parser.add_argument("--no-pretrained-cfg", action="store_true", help="Resolve config from args only instead of model cfg")
    args = parser.parse_args()

    model = timm.create_model(args.model, pretrained=False)
    overrides: dict[str, Any] = {}
    if args.input_size is not None:
        overrides["input_size"] = args.input_size
    if args.img_size is not None:
        overrides["img_size"] = args.img_size

    if args.no_pretrained_cfg:
        if not overrides:
            overrides["input_size"] = (3, 224, 224)
        data_config = resolve_data_config(args=overrides, use_test_size=args.use_test_size)
    else:
        data_config = resolve_data_config(args=overrides, model=model, use_test_size=args.use_test_size)

    eval_transform = create_transform(**data_config, is_training=False)
    train_transform = create_transform(**data_config, is_training=True, re_prob=args.train_re_prob)

    output = {
        "model": args.model,
        "num_classes": getattr(model, "num_classes", None),
        "overrides": _json_safe(overrides),
        "data_config": _json_safe(data_config),
        "eval_transform": _summarize_transform(eval_transform),
        "train_transform": _summarize_transform(train_transform),
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
