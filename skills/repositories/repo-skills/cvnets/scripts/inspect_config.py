#!/usr/bin/env python3
"""Inspect a CVNets config and print the resolved dotted options.

This script is safe to run from any working directory as long as `--repo-root`
points at a CVNets checkout. It resolves relative config paths against that
checkout before loading the config.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from _bootstrap import activate_repo_root


def _jsonify(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_jsonify(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonify(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonify(val) for key, val in value.items()}
    return str(value)


def _resolve_config_path(repo_root: Path, config_file: str) -> Path:
    candidate = Path(config_file).expanduser()
    candidates = [candidate]
    if not candidate.is_absolute():
        candidates.extend(
            [
                repo_root / config_file,
                repo_root / "config" / config_file,
            ]
        )
    for path in candidates:
        if path.is_file():
            return path.resolve()
    raise SystemExit(
        f"Could not find config file: {config_file}. Tried: {', '.join(str(p) for p in candidates)}"
    )


def _get(opts: Any, key: str, default: Any = None) -> Any:
    return getattr(opts, key, default)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Path to a CVNets checkout.",
    )
    parser.add_argument(
        "--config-file",
        required=True,
        help="Config file path or name.",
    )
    parser.add_argument(
        "--key",
        action="append",
        default=[],
        help="Extra dotted option key to include in the output summary.",
    )
    args = parser.parse_args(argv)

    repo_root = activate_repo_root(args.repo_root)
    config_path = _resolve_config_path(repo_root, args.config_file)

    from options.opts import get_training_arguments
    from options.utils import load_config_file

    parser = get_training_arguments(parse_args=False)
    opts = parser.parse_args([])
    setattr(opts, "common.config_file", str(config_path))
    opts = load_config_file(opts)

    category = _get(opts, "dataset.category")
    model_key = f"model.{category}.name" if category else None
    summary = {
        "common.config_file": _get(opts, "common.config_file"),
        "common.results_loc": _get(opts, "common.results_loc"),
        "common.run_label": _get(opts, "common.run_label"),
        "dataset.category": category,
        "dataset.name": _get(opts, "dataset.name"),
        "dataset.root_train": _get(opts, "dataset.root_train"),
        "dataset.root_val": _get(opts, "dataset.root_val"),
        "dataset.root_test": _get(opts, "dataset.root_test"),
        "dataset.train_batch_size0": _get(opts, "dataset.train_batch_size0"),
        "dataset.val_batch_size0": _get(opts, "dataset.val_batch_size0"),
        "dataset.eval_batch_size0": _get(opts, "dataset.eval_batch_size0"),
        "dataset.workers": _get(opts, "dataset.workers"),
        "dataset.collate_fn_name_train": _get(opts, "dataset.collate_fn_name_train"),
        "dataset.collate_fn_name_val": _get(opts, "dataset.collate_fn_name_val"),
        "dataset.collate_fn_name_test": _get(opts, "dataset.collate_fn_name_test"),
        "sampler.name": _get(opts, "sampler.name"),
        "sampler.bs.crop_size_width": _get(opts, "sampler.bs.crop_size_width"),
        "sampler.bs.crop_size_height": _get(opts, "sampler.bs.crop_size_height"),
        "sampler.vbs.crop_size_width": _get(opts, "sampler.vbs.crop_size_width"),
        "sampler.vbs.crop_size_height": _get(opts, "sampler.vbs.crop_size_height"),
        "optim.name": _get(opts, "optim.name"),
        "scheduler.name": _get(opts, "scheduler.name"),
        "ema.enable": _get(opts, "ema.enable"),
        "stats.checkpoint_metric": _get(opts, "stats.checkpoint_metric"),
        "stats.checkpoint_metric_max": _get(opts, "stats.checkpoint_metric_max"),
        "common.mixed_precision": _get(opts, "common.mixed_precision"),
        "common.channels_last": _get(opts, "common.channels_last"),
        "common.resume": _get(opts, "common.resume"),
        "common.finetune": _get(opts, "common.finetune"),
        "common.auto_resume": _get(opts, "common.auto_resume"),
        "text_tokenizer.name": _get(opts, "text_tokenizer.name"),
        "video_reader.name": _get(opts, "video_reader.name"),
    }
    if model_key is not None:
        summary[model_key] = _get(opts, model_key)

    for extra_key in args.key:
        summary[extra_key] = _get(opts, extra_key)

    print(json.dumps(_jsonify(summary), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
