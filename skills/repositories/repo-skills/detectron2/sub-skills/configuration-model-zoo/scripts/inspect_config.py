#!/usr/bin/env python3
"""Safely inspect Detectron2 Yacs, LazyConfig, or model-zoo configs.

This helper loads configs for static inspection only. It does not call
model_zoo.get(), DefaultPredictor, build_model(), instantiate(), or checkpoint
loading APIs, so it should not download model weights.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Iterable


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect Detectron2 Yacs YAML, LazyConfig Python, or model-zoo configs without building models or downloading weights."
    )
    parser.add_argument(
        "config",
        help="Local config path, or model-zoo relative path when --model-zoo is set.",
    )
    parser.add_argument(
        "--model-zoo",
        action="store_true",
        help="Treat CONFIG as a Detectron2 model-zoo relative path such as COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_1x.yaml.",
    )
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        help="Override to apply. For Yacs, pass 'KEY VALUE'. For LazyConfig, pass 'key=value'. Can be repeated.",
    )
    parser.add_argument(
        "--show",
        action="append",
        default=[],
        help="Dot-separated key to print after loading. Can be repeated.",
    )
    parser.add_argument(
        "--checkpoint-url",
        action="store_true",
        help="For model-zoo configs, print the official checkpoint URL if one is mapped. This only prints the URL.",
    )
    parser.add_argument(
        "--dump",
        action="store_true",
        help="Print the full merged config dump or LazyConfig pseudo-Python.",
    )
    return parser


def _import_detectron2():
    try:
        from detectron2 import model_zoo
        from detectron2.config import CfgNode, LazyConfig, get_cfg
    except Exception as exc:  # pragma: no cover - depends on user's environment
        raise SystemExit(f"Unable to import detectron2 configuration APIs: {exc}") from exc
    return model_zoo, CfgNode, LazyConfig, get_cfg


def _looks_lazy(path: str) -> bool:
    return path.endswith(".py")


def _load_config(args: argparse.Namespace):
    model_zoo, CfgNode, LazyConfig, get_cfg = _import_detectron2()
    source = args.config

    if args.model_zoo:
        try:
            config_file = model_zoo.get_config_file(source)
        except Exception as exc:
            raise SystemExit(f"Model-zoo config not found: {source}: {exc}") from exc
        try:
            cfg = model_zoo.get_config(source, trained=False)
        except Exception as exc:
            raise SystemExit(f"Unable to load model-zoo config {source}: {exc}") from exc
        return cfg, config_file, model_zoo, CfgNode, LazyConfig

    if not os.path.exists(source):
        raise SystemExit(f"Config path does not exist: {source}")
    config_file = source
    if _looks_lazy(source):
        try:
            cfg = LazyConfig.load(source)
        except Exception as exc:
            raise SystemExit(f"Unable to load LazyConfig {source}: {exc}") from exc
    else:
        cfg = get_cfg()
        try:
            cfg.merge_from_file(source)
        except Exception as exc:
            raise SystemExit(f"Unable to merge Yacs config {source}: {exc}") from exc
    return cfg, config_file, model_zoo, CfgNode, LazyConfig


def _apply_overrides(cfg: Any, overrides: Iterable[str], CfgNode: Any, LazyConfig: Any) -> None:
    overrides = list(overrides)
    if not overrides:
        return
    if isinstance(cfg, CfgNode):
        tokens = []
        for item in overrides:
            tokens.extend(item.split())
        if len(tokens) % 2:
            raise SystemExit("Yacs overrides must be alternating KEY VALUE tokens, e.g. --override 'MODEL.DEVICE cpu'.")
        try:
            cfg.merge_from_list(tokens)
        except Exception as exc:
            raise SystemExit(f"Unable to apply Yacs overrides {tokens}: {exc}") from exc
    else:
        try:
            LazyConfig.apply_overrides(cfg, overrides)
        except Exception as exc:
            raise SystemExit(f"Unable to apply LazyConfig overrides {overrides}: {exc}") from exc


def _select(cfg: Any, dotted_key: str) -> Any:
    value = cfg
    for part in dotted_key.split("."):
        if isinstance(value, dict):
            value = value[part]
        else:
            value = getattr(value, part)
    return value


def _top_level_keys(cfg: Any) -> list[str]:
    if hasattr(cfg, "keys"):
        try:
            return sorted(str(k) for k in cfg.keys())
        except Exception:
            return []
    return []


def _print_summary(cfg: Any, config_file: str, source: str, CfgNode: Any, LazyConfig: Any) -> None:
    kind = "Yacs CfgNode" if isinstance(cfg, CfgNode) else "LazyConfig/OmegaConf"
    print(f"source: {source}")
    print(f"resolved_config_file: {config_file}")
    print(f"kind: {kind}")
    keys = _top_level_keys(cfg)
    if keys:
        print("top_level_keys: " + ", ".join(keys[:40]))

    if isinstance(cfg, CfgNode):
        if hasattr(cfg, "MODEL"):
            print(f"MODEL.DEVICE: {getattr(cfg.MODEL, 'DEVICE', '<missing>')}")
            print(f"MODEL.WEIGHTS: {getattr(cfg.MODEL, 'WEIGHTS', '<missing>')}")
        print("override_hint: --override 'MODEL.DEVICE cpu' --override 'MODEL.WEIGHTS /path/model.pth'")
    else:
        for key in ("model.device", "train.init_checkpoint", "dataloader.train.total_batch_size"):
            try:
                print(f"{key}: {_select(cfg, key)}")
            except Exception:
                pass
        print("override_hint: --override \"model.device='cpu'\" --override \"train.init_checkpoint='/path/model.pth'\"")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    cfg, config_file, model_zoo, CfgNode, LazyConfig = _load_config(args)
    _apply_overrides(cfg, args.override, CfgNode, LazyConfig)
    _print_summary(cfg, config_file, args.config, CfgNode, LazyConfig)

    for key in args.show:
        try:
            print(f"show.{key}: {_select(cfg, key)}")
        except Exception as exc:
            print(f"show.{key}: <missing or unreadable: {exc}>")

    if args.checkpoint_url:
        if not args.model_zoo:
            print("checkpoint_url: <requires --model-zoo>")
        else:
            try:
                print(f"checkpoint_url: {model_zoo.get_checkpoint_url(args.config)}")
            except Exception as exc:
                print(f"checkpoint_url: <not available: {exc}>")

    if args.dump:
        print("--- dump ---")
        if isinstance(cfg, CfgNode):
            print(cfg.dump())
        else:
            print(LazyConfig.to_py(cfg))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
