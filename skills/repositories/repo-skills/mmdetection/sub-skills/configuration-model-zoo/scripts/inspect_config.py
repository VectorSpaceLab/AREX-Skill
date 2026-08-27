#!/usr/bin/env python3
"""Inspect an MMDetection/MMEngine config without training or inference."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

def import_mmengine() -> tuple[Any, Any]:
    try:
        from mmengine import Config, DictAction
    except Exception as exc:  # pragma: no cover - useful CLI failure path
        raise SystemExit(
            "Failed to import mmengine. Install compatible MMEngine/MMDetection "
            f"dependencies before inspecting configs. Original error: {exc}"
        ) from exc
    return Config, DictAction


class MissingDictAction(argparse.Action):
    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace, values: Any, option_string: str | None = None) -> None:
        parser.error("--cfg-options requires mmengine to be installed")


def cfg_options_action() -> type[argparse.Action]:
    try:
        from mmengine import DictAction
    except Exception:
        return MissingDictAction
    return DictAction


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Flatten and summarize an MMDetection/MMEngine config."
    )
    parser.add_argument("config", help="Path to a config file readable by mmengine.Config")
    parser.add_argument(
        "--cfg-options",
        nargs="+",
        action=cfg_options_action(),
        help=(
            "Override config keys in key=value form, e.g. "
            "model.test_cfg.rcnn.score_thr=0.3 or "
            "'model.data_preprocessor.mean=[0,0,0]'."
        ),
    )
    parser.add_argument(
        "--keys",
        nargs="+",
        help="Only print selected top-level keys, e.g. model auto_scale_lr train_dataloader.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a concise summary. This is the default unless --full or --keys is used.",
    )
    parser.add_argument("--full", action="store_true", help="Print the full merged config text.")
    parser.add_argument(
        "--replace-cfg-vals",
        action="store_true",
        help="Apply mmdet.utils.replace_cfg_vals if MMDetection is importable.",
    )
    parser.add_argument(
        "--update-data-root",
        action="store_true",
        help="Apply mmdet.utils.update_data_root using MMDET_DATASETS if available.",
    )
    parser.add_argument(
        "--save-path",
        help="Dump the merged config to a .py, .json, .yaml, or .yml file.",
    )
    return parser.parse_args()


def require_mmdet_utils() -> tuple[Any, Any]:
    try:
        from mmdet.utils import replace_cfg_vals, update_data_root
    except Exception as exc:  # pragma: no cover - useful CLI failure path
        raise SystemExit(
            "This option requires MMDetection to be importable with compatible "
            f"dependencies. Original error: {exc}"
        ) from exc
    return replace_cfg_vals, update_data_root


def dotted_get(data: Any, dotted_key: str, default: Any = None) -> Any:
    current = data
    for part in dotted_key.split("."):
        if isinstance(current, Mapping):
            current = current.get(part, default)
        elif isinstance(current, Sequence) and not isinstance(current, (str, bytes)):
            if not part.isdigit():
                return default
            index = int(part)
            if index >= len(current):
                return default
            current = current[index]
        else:
            return default
    return current


def first_present(data: Mapping[str, Any], keys: Sequence[str]) -> str:
    return ", ".join(key for key in keys if key in data) or "none"


def type_name(value: Any) -> str:
    if isinstance(value, Mapping):
        raw_type = value.get("type")
        if raw_type is not None:
            return str(raw_type)
    return "missing"


def summarize(cfg: Config) -> str:
    data = cfg.to_dict()
    model = data.get("model", {})
    auto_scale_lr = data.get("auto_scale_lr", {})
    train_dataloader = data.get("train_dataloader", {})
    val_dataloader = data.get("val_dataloader", {})
    test_dataloader = data.get("test_dataloader", {})

    lines = [
        "Config summary",
        f"- filename: {Path(cfg.filename).name if cfg.filename else 'unknown'}",
        f"- default_scope: {data.get('default_scope', 'mmdet (implicit fallback in many tools)')}",
        f"- top-level sections: {first_present(data, ['model', 'train_dataloader', 'val_dataloader', 'test_dataloader', 'val_evaluator', 'test_evaluator', 'auto_scale_lr'])}",
        f"- model.type: {type_name(model)}",
        f"- backbone.type: {type_name(dotted_get(model, 'backbone', {}))}",
        f"- neck.type: {type_name(dotted_get(model, 'neck', {}))}",
        f"- bbox_head.type: {type_name(dotted_get(model, 'bbox_head', {}))}",
        f"- roi_head.type: {type_name(dotted_get(model, 'roi_head', {}))}",
        f"- model.data_preprocessor.type: {type_name(dotted_get(model, 'data_preprocessor', {}))}",
        f"- train_dataloader.batch_size: {train_dataloader.get('batch_size', 'missing') if isinstance(train_dataloader, Mapping) else 'missing'}",
        f"- val_dataloader.batch_size: {val_dataloader.get('batch_size', 'missing') if isinstance(val_dataloader, Mapping) else 'missing'}",
        f"- test_dataloader.batch_size: {test_dataloader.get('batch_size', 'missing') if isinstance(test_dataloader, Mapping) else 'missing'}",
        f"- auto_scale_lr.enable: {auto_scale_lr.get('enable', 'missing') if isinstance(auto_scale_lr, Mapping) else 'missing'}",
        f"- auto_scale_lr.base_batch_size: {auto_scale_lr.get('base_batch_size', 'missing') if isinstance(auto_scale_lr, Mapping) else 'missing'}",
    ]
    return "\n".join(lines)


def print_selected_keys(config_class: Any, cfg: Any, keys: Sequence[str]) -> None:
    data = cfg.to_dict()
    for key in keys:
        if key not in data:
            print(f"# {key}: <missing>")
            continue
        selected = config_class({key: data[key]})
        print(selected.pretty_text)


def dump_config(cfg: Any, save_path: str) -> None:
    suffix = Path(save_path).suffix
    if suffix not in {".py", ".json", ".yaml", ".yml"}:
        raise SystemExit("--save-path must end with .py, .json, .yaml, or .yml")
    parent = os.path.dirname(save_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    cfg.dump(save_path)
    print(f"Saved merged config to {save_path}")


def main() -> int:
    args = parse_args()
    config_class, _ = import_mmengine()
    cfg = config_class.fromfile(args.config)

    if args.replace_cfg_vals or args.update_data_root:
        replace_cfg_vals, update_data_root = require_mmdet_utils()
        if args.replace_cfg_vals:
            cfg = replace_cfg_vals(cfg)
        if args.update_data_root:
            update_data_root(cfg)

    if args.cfg_options:
        cfg.merge_from_dict(args.cfg_options)

    if args.save_path:
        dump_config(cfg, args.save_path)

    if args.full:
        print(cfg.pretty_text)
    elif args.keys:
        print_selected_keys(config_class, cfg, args.keys)
    else:
        print(summarize(cfg))

    return 0


if __name__ == "__main__":
    sys.exit(main())
