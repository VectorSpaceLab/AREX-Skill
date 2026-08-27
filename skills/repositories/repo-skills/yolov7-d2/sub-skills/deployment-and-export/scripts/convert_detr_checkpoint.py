#!/usr/bin/env python3
"""Convert reference DETR-family checkpoints to YOLOv7-d2/Detectron2 key names.

Supports DETR, AnchorDETR, and SMCA-DETR variants with optional mask remap.
Uses CPU torch/numpy operations only and does not import YOLOv7-d2.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
from pathlib import Path
import sys
from typing import Any

import numpy as np
import torch

DETR_92_TO_D2_81 = np.array([1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,25,27,28,31,32,33,34,35,36,37,38,39,40,41,42,43,44,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,67,70,72,73,74,75,76,77,78,79,80,81,82,84,85,86,87,88,89,90,91], dtype=np.int64)
ANCHOR_91_REORDER = np.array([1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,25,27,28,31,32,33,34,35,36,37,38,39,40,41,42,43,44,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,67,70,72,73,74,75,76,77,78,79,80,81,82,84,85,86,87,88,89,90,0,12,26,29,30,45,68,69,71,83], dtype=np.int64)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Convert DETR/AnchorDETR/SMCA-DETR checkpoints for YOLOv7-d2.")
    p.add_argument("--source-model", "--source_model", "--source", dest="source_model", required=True)
    p.add_argument("--output-model", "--output_model", "--output", dest="output_model", default="")
    p.add_argument("--variant", choices=["detr", "anchordetr", "smcadetr"], required=True)
    p.add_argument("--prefix", default="detr", help="Top-level output prefix; keep 'detr' for YOLOv7-d2 wrappers unless custom code expects another.")
    p.add_argument("--mask", action="store_true", help="Apply DETR segmentation/mask wrapper key remap.")
    p.add_argument("--class-remap", choices=["auto", "off"], default="auto")
    p.add_argument("--checkpoint-key", default="model")
    p.add_argument("--allow-url", action="store_true", help="Allow trusted URL checkpoint download.")
    p.add_argument("--check-hash", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="Print summary without saving.")
    p.add_argument("--print-mappings", action="store_true")
    return p


def load_checkpoint(source: str, allow_url: bool, check_hash: bool) -> Any:
    if source.startswith(("http://", "https://")):
        if not allow_url:
            raise ValueError("URL input requires --allow-url; prefer a local trusted checkpoint")
        return torch.hub.load_state_dict_from_url(source, map_location="cpu", check_hash=check_hash)
    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(f"source checkpoint not found: {source}")
    return torch.load(str(path), map_location="cpu")


def looks_like_state_dict(obj: Mapping[str, Any]) -> bool:
    return bool(obj) and sum(torch.is_tensor(v) for v in obj.values()) >= max(1, len(obj) // 2)


def state_dict_from(checkpoint: Any, key: str) -> Mapping[str, Any]:
    if isinstance(checkpoint, Mapping):
        if key in checkpoint and isinstance(checkpoint[key], Mapping):
            return checkpoint[key]
        if looks_like_state_dict(checkpoint):
            return checkpoint
    raise ValueError(f"checkpoint has no state dict under {key!r}; pass --checkpoint-key if needed")


def rewrite_backbone_key(key: str, variant: str) -> str:
    if variant == "anchordetr":
        prefixes = [("backbone.body.", "backbone.backbone."), ("backbone.0.body.", "backbone.backbone.")]
    else:
        prefixes = [("backbone.0.body.", "backbone.0.backbone."), ("backbone.body.", "backbone.0.backbone.")]
    for old, new_prefix in prefixes:
        if key.startswith(old):
            key = key.replace(old, "", 1)
            break
    else:
        return key
    if "layer" not in key:
        key = "stem." + key
    for i in (1, 2, 3, 4):
        key = key.replace(f"layer{i}", f"res{i + 1}")
    for i in (1, 2, 3):
        key = key.replace(f"bn{i}", f"conv{i}.norm")
    key = key.replace("downsample.0", "shortcut").replace("downsample.1", "shortcut.norm")
    return new_prefix + key


def remap_class(old_key: str, tensor: torch.Tensor, variant: str, mode: str) -> tuple[torch.Tensor, str]:
    value = tensor.detach().cpu().clone()
    if mode == "off" or "class_embed" not in old_key:
        return value, "unchanged"
    rows = int(value.shape[0]) if value.ndim else 0
    if variant in {"detr", "smcadetr"}:
        if rows == 92:
            return value.index_select(0, torch.as_tensor(DETR_92_TO_D2_81, dtype=torch.long)), "92->81"
        if rows == 81:
            return value, "already81"
        raise ValueError(f"{variant} class_embed {old_key} has {rows} rows; expected 92 or 81")
    if rows == 91:
        reordered = value.index_select(0, torch.as_tensor(ANCHOR_91_REORDER, dtype=torch.long))
        return torch.cat([reordered[:-10], reordered[-10:].sum(dim=0, keepdim=True)], dim=0), "91->81"
    if rows == 81:
        return value, "already81"
    raise ValueError(f"anchordetr class_embed {old_key} has {rows} rows; expected 91 or 81")


def add_prefix(key: str, prefix: str) -> str:
    prefix = prefix.strip(".")
    return f"{prefix}.{key}" if prefix else key


def mask_key(key: str) -> str:
    if "backbone" not in key:
        return key
    return ("detr." + key).replace("backbone.detr", "backbone").replace("stem.detr", "stem")


def convert(state: Mapping[str, Any], args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    out: dict[str, Any] = {}
    summary = {"keys_in": len(state), "keys_out": 0, "class_remaps": []}
    for old_key, old_val in state.items():
        new_key = add_prefix(rewrite_backbone_key(str(old_key), args.variant), args.prefix)
        if torch.is_tensor(old_val):
            new_val, kind = remap_class(str(old_key), old_val, args.variant, args.class_remap)
            if kind != "unchanged":
                summary["class_remaps"].append({"key": new_key, "kind": kind, "old_shape": list(old_val.shape), "new_shape": list(new_val.shape)})
        else:
            new_val = old_val
        if args.mask:
            new_key = mask_key(new_key)
        if new_key in out:
            raise ValueError(f"key collision after conversion: {old_key} -> {new_key}")
        out[new_key] = new_val
        if args.print_mappings:
            print(f"{old_key} -> {new_key}")
    summary["keys_out"] = len(out)
    return out, summary


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if not args.dry_run and not args.output_model:
        print("error: --output-model is required unless --dry-run is used", file=sys.stderr)
        return 2
    try:
        checkpoint = load_checkpoint(args.source_model, args.allow_url, args.check_hash)
        state = state_dict_from(checkpoint, args.checkpoint_key)
        converted, summary = convert(state, args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"variant={args.variant} prefix={args.prefix!r} mask={args.mask} keys={summary['keys_in']}->{summary['keys_out']}")
    for item in summary["class_remaps"]:
        print(f"class_remap {item['key']}: {item['kind']} {item['old_shape']}->{item['new_shape']}")
    if args.dry_run:
        print("dry-run: not saved")
        return 0
    out_path = Path(args.output_model)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model": converted}, str(out_path))
    print(f"saved converted checkpoint: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
