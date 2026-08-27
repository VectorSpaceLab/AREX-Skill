#!/usr/bin/env python3
"""Summarize an MMOCR config without building a runner or starting training.

The script imports MMEngine only after argument parsing, so ``--help`` works in
minimal environments. A real config load requires an environment that can import
``mmengine`` and execute the target config's Python code.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

_MISSING = object()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Load an MMOCR/MMEngine config, apply optional KEY=VALUE overrides, "
            "and print a compact summary without building models, datasets, "
            "evaluators, runners, or training loops."
        )
    )
    parser.add_argument("--config", required=True, help="Path to the config file to load.")
    parser.add_argument(
        "--cfg-options",
        nargs="+",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help=(
            "Override config settings. May be repeated. Values are parsed as "
            "Python literals when possible; otherwise they remain strings."
        ),
    )
    parser.add_argument("--json", action="store_true", help="Emit compact JSON instead of text.")
    parser.add_argument(
        "--require-default-scope",
        nargs="?",
        const="mmocr",
        default=None,
        metavar="SCOPE",
        help=(
            "Require cfg.default_scope to equal SCOPE. If no SCOPE is given, "
            "requires 'mmocr'."
        ),
    )
    return parser


def flatten_cfg_options(raw: Sequence[Sequence[str]]) -> List[str]:
    tokens: List[str] = []
    for group in raw:
        tokens.extend(group)
    return tokens


def parse_value(raw: str) -> Any:
    value = raw.strip()
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"none", "null"}:
        return None
    try:
        return ast.literal_eval(value)
    except Exception:
        pass
    if "," in value and not value.startswith(("/", "./", "../")):
        return [parse_value(part) for part in value.split(",")]
    if (value.startswith("'") and value.endswith("'")) or (
        value.startswith('"') and value.endswith('"')
    ):
        return value[1:-1]
    return value


def parse_cfg_options(tokens: Iterable[str]) -> Dict[str, Any]:
    parsed: Dict[str, Any] = {}
    for token in tokens:
        if "=" not in token:
            raise ValueError(f"cfg option must be KEY=VALUE, got: {token!r}")
        key, value = token.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"cfg option has an empty key: {token!r}")
        parsed[key] = parse_value(value)
    return parsed


def get_value(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    getter = getattr(obj, "get", None)
    if callable(getter):
        try:
            return getter(key, default)
        except Exception:
            pass
    return getattr(obj, key, default)


def has_key(obj: Any, key: str) -> bool:
    if obj is None:
        return False
    try:
        return key in obj
    except Exception:
        return get_value(obj, key, _MISSING) is not _MISSING


def scalar(value: Any) -> Any:
    if value is _MISSING:
        return None
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [scalar(item) for item in value]
    if isinstance(value, Mapping):
        return {str(k): scalar(v) for k, v in value.items()}
    return str(value)


def type_of(node: Any) -> Optional[Any]:
    if node is None or node is _MISSING:
        return None
    if isinstance(node, (list, tuple)):
        return [type_of(item) for item in node]
    value = get_value(node, "type", _MISSING)
    if value is _MISSING:
        return None
    return scalar(value)


def dedupe(values: Iterable[Any]) -> List[Any]:
    seen = set()
    out: List[Any] = []
    for value in values:
        marker = json.dumps(scalar(value), sort_keys=True, default=str)
        if marker not in seen:
            seen.add(marker)
            out.append(scalar(value))
    return out


def collect_dataset_types(dataset_cfg: Any) -> List[Any]:
    if dataset_cfg is None or dataset_cfg is _MISSING:
        return []
    if isinstance(dataset_cfg, (list, tuple)):
        collected: List[Any] = []
        for item in dataset_cfg:
            collected.extend(collect_dataset_types(item))
        return dedupe(collected)

    collected: List[Any] = []
    root_type = type_of(dataset_cfg)
    if root_type is not None:
        if isinstance(root_type, list):
            collected.extend(root_type)
        else:
            collected.append(root_type)

    child = get_value(dataset_cfg, "dataset", _MISSING)
    if child is not _MISSING:
        collected.extend(collect_dataset_types(child))

    children = get_value(dataset_cfg, "datasets", _MISSING)
    if children is not _MISSING:
        collected.extend(collect_dataset_types(children))

    return dedupe(collected)


def dataloader_summary(cfg: Any, name: str) -> Dict[str, Any]:
    dataloader = get_value(cfg, f"{name}_dataloader", None)
    dataset = get_value(dataloader, "dataset", None)
    return {
        "batch_size": scalar(get_value(dataloader, "batch_size", None)),
        "dataset_type": scalar(type_of(dataset)),
        "dataset_types": collect_dataset_types(dataset),
    }


def collect_metric_types(node: Any) -> List[Any]:
    if node is None or node is _MISSING:
        return []
    if isinstance(node, (list, tuple)):
        collected: List[Any] = []
        for item in node:
            collected.extend(collect_metric_types(item))
        return dedupe(collected)
    node_type = type_of(node)
    collected = [] if node_type is None else [node_type]
    metrics = get_value(node, "metrics", _MISSING)
    if metrics is not _MISSING:
        collected.extend(collect_metric_types(metrics))
    return dedupe(collected)


def evaluator_summary(cfg: Any, name: str) -> Dict[str, Any]:
    evaluator = get_value(cfg, f"{name}_evaluator", None)
    return {
        "type": scalar(type_of(evaluator)),
        "metric_types": collect_metric_types(evaluator),
    }


def loop_type(cfg: Any, name: str) -> Any:
    return scalar(type_of(get_value(cfg, f"{name}_cfg", None)))


def build_summary(config_path: str, cfg: Any) -> Dict[str, Any]:
    env_cfg = get_value(cfg, "env_cfg", None)
    dist_cfg = get_value(env_cfg, "dist_cfg", None)
    optim_wrapper = get_value(cfg, "optim_wrapper", None)
    auto_scale_lr = get_value(cfg, "auto_scale_lr", None)
    model = get_value(cfg, "model", None)

    return {
        "config": config_path,
        "default_scope": scalar(get_value(cfg, "default_scope", None)),
        "model.type": scalar(type_of(model)),
        "work_dir": scalar(get_value(cfg, "work_dir", None)),
        "resume": scalar(get_value(cfg, "resume", False)),
        "load_from": scalar(get_value(cfg, "load_from", None)),
        "optim_wrapper.type": scalar(type_of(optim_wrapper)),
        "auto_scale_lr.base_batch_size": scalar(get_value(auto_scale_lr, "base_batch_size", None)),
        "loops": {
            "train": loop_type(cfg, "train"),
            "val": loop_type(cfg, "val"),
            "test": loop_type(cfg, "test"),
        },
        "dataloaders": {
            "train": dataloader_summary(cfg, "train"),
            "val": dataloader_summary(cfg, "val"),
            "test": dataloader_summary(cfg, "test"),
        },
        "evaluators": {
            "val": evaluator_summary(cfg, "val"),
            "test": evaluator_summary(cfg, "test"),
        },
        "has_tta": bool(has_key(cfg, "tta_pipeline") and has_key(cfg, "tta_model")),
        "env.dist_cfg.backend": scalar(get_value(dist_cfg, "backend", None)),
    }


def print_text(summary: Mapping[str, Any]) -> None:
    print(f"config: {summary['config']}")
    for key in (
        "default_scope",
        "model.type",
        "work_dir",
        "resume",
        "load_from",
        "optim_wrapper.type",
        "auto_scale_lr.base_batch_size",
        "has_tta",
        "env.dist_cfg.backend",
    ):
        print(f"{key}: {summary.get(key)}")
    loops = summary["loops"]
    print(f"loops: train={loops['train']} val={loops['val']} test={loops['test']}")
    for name, info in summary["dataloaders"].items():
        print(
            f"{name}_dataloader: batch_size={info['batch_size']} "
            f"dataset_type={info['dataset_type']} dataset_types={info['dataset_types']}"
        )
    for name, info in summary["evaluators"].items():
        print(f"{name}_evaluator: type={info['type']} metric_types={info['metric_types']}")


def import_config_class() -> Any:
    try:
        from mmengine.config import Config  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on caller environment
        print(
            "ERROR: failed to import mmengine.config.Config. Install or activate "
            f"a compatible MMOCR/MMEngine environment, then retry. ({type(exc).__name__}: {exc})",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return Config


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        cfg_options = parse_cfg_options(flatten_cfg_options(args.cfg_options))
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    Config = import_config_class()
    try:
        cfg = Config.fromfile(args.config)
        if cfg_options:
            cfg.merge_from_dict(cfg_options)
    except Exception as exc:  # pragma: no cover - config/env specific
        print(f"ERROR: failed to load or merge config: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    summary = build_summary(args.config, cfg)
    required_scope = args.require_default_scope
    if required_scope is not None and summary["default_scope"] != required_scope:
        print(
            "ERROR: default_scope mismatch: "
            f"expected {required_scope!r}, got {summary['default_scope']!r}",
            file=sys.stderr,
        )
        return 1

    if args.json:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    else:
        print_text(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
