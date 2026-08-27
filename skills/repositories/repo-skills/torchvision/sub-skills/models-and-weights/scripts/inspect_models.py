#!/usr/bin/env python3
"""Safely inspect TorchVision model and weight APIs without downloading weights."""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from collections.abc import Iterable
from typing import Any


def _load_torchvision():
    try:
        import torchvision
        from torchvision import models
    except Exception as error:  # pragma: no cover - diagnostic path
        raise SystemExit(f"Failed to import torchvision: {error}") from error
    return torchvision, models


def _module_from_name(torchvision: Any, module_name: str | None):
    if module_name in (None, "all"):
        return None
    mapping = {
        "classification": torchvision.models,
        "models": torchvision.models,
        "detection": torchvision.models.detection,
        "segmentation": torchvision.models.segmentation,
        "video": torchvision.models.video,
        "quantization": torchvision.models.quantization,
        "optical_flow": torchvision.models.optical_flow,
    }
    try:
        return mapping[module_name]
    except KeyError as error:
        valid = ", ".join(sorted(mapping)) + ", all"
        raise SystemExit(f"Unknown module '{module_name}'. Choose one of: {valid}") from error


def _json_default(value: Any):
    if isinstance(value, (set, tuple)):
        return list(value)
    if callable(value):
        return repr(value)
    return str(value)


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, default=_json_default))


def _truncate(items: Iterable[Any], limit: int | None) -> list[Any]:
    values = list(items)
    if limit is not None and limit >= 0:
        return values[:limit]
    return values


def command_list(args: argparse.Namespace) -> None:
    torchvision, models = _load_torchvision()
    module = _module_from_name(torchvision, args.module)
    names = models.list_models(module=module, include=args.include, exclude=args.exclude)
    names = _truncate(names, args.limit)
    if args.json:
        _print_json({"count": len(names), "models": names})
    else:
        for name in names:
            print(name)
        print(f"count={len(names)}", file=sys.stderr)


def command_weights(args: argparse.Namespace) -> None:
    _, models = _load_torchvision()
    try:
        weights_enum = models.get_model_weights(args.model)
    except Exception as error:
        raise SystemExit(f"Failed to get weights for '{args.model}': {error}") from error

    members = list(weights_enum)
    payload = {
        "model": args.model,
        "weights_enum": weights_enum.__name__,
        "default": repr(getattr(weights_enum, "DEFAULT", None)),
        "members": [member.name for member in members],
    }
    if args.with_meta:
        payload["metadata"] = {
            member.name: {
                "url_present": bool(member.url),
                "meta_keys": sorted(member.meta.keys()),
                "categories_count": len(member.meta.get("categories", []))
                if isinstance(member.meta.get("categories"), list)
                else None,
                "recipe": member.meta.get("recipe"),
                "num_params": member.meta.get("num_params"),
                "ops": member.meta.get("_ops"),
            }
            for member in members
        }
    _print_json(payload)


def command_weight(args: argparse.Namespace) -> None:
    _, models = _load_torchvision()
    try:
        weight = models.get_weight(args.name)
    except Exception as error:
        raise SystemExit(f"Failed to get weight '{args.name}': {error}") from error

    transform = weight.transforms()
    payload = {
        "name": repr(weight),
        "enum": weight.__class__.__name__,
        "member": weight.name,
        "url_present": bool(weight.url),
        "meta_keys": sorted(weight.meta.keys()),
        "categories_count": len(weight.meta.get("categories", []))
        if isinstance(weight.meta.get("categories"), list)
        else None,
        "recipe": weight.meta.get("recipe"),
        "num_params": weight.meta.get("num_params"),
        "ops": weight.meta.get("_ops"),
        "transform_type": type(transform).__name__,
        "transform_repr": repr(transform),
    }
    _print_json(payload)


def command_signature(args: argparse.Namespace) -> None:
    _, models = _load_torchvision()
    try:
        builder = models.get_model_builder(args.model)
    except Exception as error:
        raise SystemExit(f"Failed to get builder for '{args.model}': {error}") from error
    payload = {
        "model": args.model,
        "builder": f"{builder.__module__}.{builder.__name__}",
        "signature": str(inspect.signature(builder)),
    }
    _print_json(payload)


def command_construct(args: argparse.Namespace) -> None:
    _, models = _load_torchvision()
    kwargs: dict[str, Any] = {"weights": None}
    if args.no_backbone_weights:
        kwargs["weights_backbone"] = None
    try:
        model = models.get_model(args.model, **kwargs)
    except TypeError:
        kwargs.pop("weights_backbone", None)
        try:
            model = models.get_model(args.model, **kwargs)
        except Exception as error:
            raise SystemExit(f"Failed to construct '{args.model}' with weights=None: {error}") from error
    except Exception as error:
        raise SystemExit(f"Failed to construct '{args.model}' with weights=None: {error}") from error
    model.eval()
    trainable = sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
    total = sum(parameter.numel() for parameter in model.parameters())
    _print_json(
        {
            "model": args.model,
            "class": type(model).__name__,
            "training": model.training,
            "parameters": total,
            "trainable_parameters": trainable,
            "used_kwargs": kwargs,
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect TorchVision models and weights without downloading pretrained weights by default."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List registered model names.")
    list_parser.add_argument("--module", default="all", help="all, classification, detection, segmentation, video, quantization, or optical_flow")
    list_parser.add_argument("--include", help="Shell-style include filter such as 'resnet*'.")
    list_parser.add_argument("--exclude", help="Shell-style exclude filter.")
    list_parser.add_argument("--limit", type=int, default=None, help="Maximum number of names to print.")
    list_parser.add_argument("--json", action="store_true", help="Print JSON instead of newline names.")
    list_parser.set_defaults(func=command_list)

    weights_parser = subparsers.add_parser("weights", help="Show available weights for a model builder.")
    weights_parser.add_argument("model", help="Registered model name, for example resnet50.")
    weights_parser.add_argument("--with-meta", action="store_true", help="Include selected metadata keys without downloading weights.")
    weights_parser.set_defaults(func=command_weights)

    weight_parser = subparsers.add_parser("weight", help="Inspect one fully qualified weight enum member.")
    weight_parser.add_argument("name", help="Full name such as ResNet50_Weights.DEFAULT.")
    weight_parser.set_defaults(func=command_weight)

    signature_parser = subparsers.add_parser("signature", help="Show a model builder signature.")
    signature_parser.add_argument("model", help="Registered model name, for example fasterrcnn_resnet50_fpn.")
    signature_parser.set_defaults(func=command_signature)

    construct_parser = subparsers.add_parser("construct", help="Construct a model with weights=None for a no-download smoke check.")
    construct_parser.add_argument("model", help="Registered model name.")
    construct_parser.add_argument("--no-backbone-weights", action="store_true", help="Also pass weights_backbone=None when supported.")
    construct_parser.set_defaults(func=command_construct)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
