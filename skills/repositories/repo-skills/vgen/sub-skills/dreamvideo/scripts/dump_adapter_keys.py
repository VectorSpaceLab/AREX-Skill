#!/usr/bin/env python3
"""Export DreamVideo adapter-bearing UNet parameter names.

This helper adapts the repository's key-selection inspection logic into a
configurable runtime script. It is useful when preparing DreamVideo subject
or motion adapters and when you need a deterministic list of parameter names
for adapter-bearing temporal or spatial blocks.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from copy import deepcopy
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export DreamVideo temporal or spatial adapter key names.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path('.'),
        help="VGen checkout root used to import the package and resolve configs.",
    )
    parser.add_argument(
        "--config",
        required=True,
        help="DreamVideo config to inspect, relative to the repo root unless absolute.",
    )
    parser.add_argument(
        "--mode",
        choices=["temporal", "spatial", "both"],
        default="both",
        help="Which adapter-friendly block family to export.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON output path. Defaults to workspace/module_list/ under the repo root.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only the output path and counts.",
    )
    return parser.parse_args(argv)


def load_cfg(repo_root: Path, config: str):
    repo_root = repo_root.resolve()
    config_path = Path(config)
    if not config_path.is_absolute():
        config_path = repo_root / config_path
    if not config_path.exists():
        raise FileNotFoundError(config_path)

    os.chdir(repo_root)
    sys.path.insert(0, str(repo_root))

    from utils.config import Config

    original_argv = sys.argv[:]
    try:
        sys.argv = [original_argv[0], "--cfg", str(config_path)]
        cfg_update = Config(load=True)
    finally:
        sys.argv = original_argv
    return cfg_update, config_path


def merge_into(global_cfg, update_cfg):
    for key, value in update_cfg.cfg_dict.items():
        if isinstance(value, dict) and key in global_cfg:
            global_cfg[key].update(value)
        else:
            global_cfg[key] = value
    return global_cfg


def build_model(cfg):
    from utils.registry_class import MODEL
    import tools  # noqa: F401 - register repo modules before building

    model = MODEL.build(cfg.UNet)
    return model


def _import_block_classes():
    try:
        from tools.modules.unet.util import (
            SpatialTransformer,
            SpatialTransformerWithAdapter,
            TemporalAttentionBlock,
            TemporalAttentionMultiBlock,
            TemporalConvBlock,
            TemporalConvBlock_v2,
            TemporalTransformer,
            TemporalTransformerWithAdapter,
            TemporalTransformer_attemask,
        )
    except Exception as exc:
        raise RuntimeError(f"unable to import DreamVideo block classes: {exc}") from exc

    temporal = (
        TemporalTransformerWithAdapter,
        TemporalTransformer,
        TemporalTransformer_attemask,
        TemporalAttentionBlock,
        TemporalAttentionMultiBlock,
        TemporalConvBlock_v2,
        TemporalConvBlock,
    )
    spatial = (
        SpatialTransformerWithAdapter,
        SpatialTransformer,
    )
    return temporal, spatial


def collect_prefixes(model, block_types: Sequence[type]) -> List[str]:
    prefixes: List[str] = []
    for name, module in model.named_modules():
        if isinstance(module, tuple(block_types)):
            if name:
                prefixes.append(name)
    return prefixes


def collect_parameter_names(model, prefixes: Sequence[str]) -> List[str]:
    matches: List[str] = []
    for param_name, _ in model.named_parameters():
        for prefix in prefixes:
            if param_name == prefix or param_name.startswith(prefix + "."):
                matches.append(param_name)
                break
    return sorted(dict.fromkeys(matches))


def export_keys(model, mode: str) -> Dict[str, List[str]]:
    temporal_types, spatial_types = _import_block_classes()
    result: Dict[str, List[str]] = {}
    if mode in {"temporal", "both"}:
        result["temporal"] = collect_parameter_names(model, collect_prefixes(model, temporal_types))
    if mode in {"spatial", "both"}:
        result["spatial"] = collect_parameter_names(model, collect_prefixes(model, spatial_types))
    return result


def default_output(repo_root: Path, config_path: Path, mode: str) -> Path:
    stem = config_path.stem
    suffix = mode if mode != "both" else "adapter"
    return repo_root / "workspace" / "module_list" / f"{stem}_{suffix}_keys.json"


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    cfg_update, config_path = load_cfg(repo_root, args.config)

    from tools.modules.config import cfg as global_cfg

    cfg = deepcopy(global_cfg)
    for layer_key in ("subject_cfg", "motion_cfg"):
        layer_path = cfg_update.cfg_dict.get(layer_key)
        if layer_path:
            layer_update, _ = load_cfg(repo_root, layer_path)
            cfg = merge_into(cfg, layer_update)

    cfg = merge_into(cfg, cfg_update)
    model = build_model(cfg)

    key_map = export_keys(model, args.mode)
    total = sum(len(v) for v in key_map.values())

    output_path = args.output if args.output is not None else default_output(repo_root, config_path, args.mode)
    if not output_path.is_absolute():
        output_path = repo_root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(key_map, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if not args.quiet:
        print(f"Loaded config: {config_path}")
        print(f"Wrote key export to: {output_path}")
        for family, names in key_map.items():
            print(f"{family}: {len(names)} parameter name(s)")
    else:
        print(f"{output_path} ({total} parameter name(s))")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
