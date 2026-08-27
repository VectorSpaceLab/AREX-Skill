#!/usr/bin/env python3
"""Inspect an MMDetection3D/MMEngine config without building the model.

The script requires mmengine at runtime. It parses a config, optionally applies
MMEngine-style dotted overrides, and prints a compact summary of the model,
dataloaders, evaluators, loops, optimization, and runtime keys.

Examples:
  python check_config.py configs/pointpillars/example_config.py
  python check_config.py configs/centerpoint/example_config.py --json
  python check_config.py configs/example.py --cfg-options train_dataloader.batch_size=2 work_dir=./work_dirs/debug
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional


_SIMPLE_KEYS = (
    "type",
    "data_root",
    "ann_file",
    "load_eval_anns",
    "box_type_3d",
    "test_mode",
    "format_only",
    "metric",
    "submission_prefix",
    "prefix",
    "collect_device",
)

_COMPONENT_KEYS = (
    "data_preprocessor",
    "voxel_encoder",
    "pts_voxel_encoder",
    "middle_encoder",
    "pts_middle_encoder",
    "backbone",
    "pts_backbone",
    "neck",
    "pts_neck",
    "bbox_head",
    "pts_bbox_head",
    "decode_head",
    "seg_head",
    "roi_head",
    "rpn_head",
    "fusion_layer",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse and summarize an MMDetection3D config with MMEngine."
    )
    parser.add_argument("config", help="Path to the config file to inspect.")
    parser.add_argument(
        "--cfg-options",
        nargs="*",
        default=[],
        metavar="KEY=VALUE",
        help=(
            "Optional MMEngine-style dotted overrides to merge before "
            "summarizing, e.g. train_dataloader.batch_size=2."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the summary as JSON instead of human-readable text.",
    )
    parser.add_argument(
        "--show-top-keys",
        type=int,
        default=80,
        help="Maximum number of top-level keys to display in text mode.",
    )
    return parser.parse_args()


def _load_mmengine_config():
    try:
        from mmengine.config import Config  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on caller env
        print(
            "ERROR: mmengine is required to parse MMDetection3D configs, "
            "but it could not be imported.",
            file=sys.stderr,
        )
        print(
            "Install or activate an MMDetection3D/OpenMMLab runtime, then "
            "rerun this script from a location where the config and its "
            "relative _base_ files are available.",
            file=sys.stderr,
        )
        print(f"Import failure: {type(exc).__name__}: {exc}", file=sys.stderr)
        return None
    return Config


def _parse_value(raw: str) -> Any:
    lowered = raw.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "none" or lowered == "null":
        return None
    try:
        return ast.literal_eval(raw)
    except Exception:
        return raw


def _parse_overrides(items: Iterable[str]) -> Dict[str, Any]:
    overrides: Dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(
                f"Invalid --cfg-options item {item!r}; expected KEY=VALUE."
            )
        key, raw = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Invalid --cfg-options item {item!r}; empty key.")
        overrides[key] = _parse_value(raw.strip())
    return overrides


def _to_plain(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        try:
            return value.to_dict()
        except Exception:
            pass
    if isinstance(value, Mapping):
        return {str(k): _to_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_plain(v) for v in value]
    return value


def _is_mapping(value: Any) -> bool:
    return isinstance(value, MutableMapping) or isinstance(value, Mapping)


def _get(mapping: Any, key: str, default: Any = None) -> Any:
    if _is_mapping(mapping):
        return mapping.get(key, default)
    return default


def _short(value: Any, max_len: int = 120) -> str:
    if value is None:
        return "None"
    if isinstance(value, (str, int, float, bool)):
        text = repr(value) if isinstance(value, str) else str(value)
    else:
        text = json.dumps(_to_plain(value), ensure_ascii=False, default=str)
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def _type_of(node: Any) -> Optional[str]:
    t = _get(node, "type")
    return str(t) if t is not None else None


def _summarize_named_mapping(node: Any, extra_keys: Iterable[str] = ()) -> Dict[str, Any]:
    if not _is_mapping(node):
        return {"present": False, "python_type": type(node).__name__}
    result: Dict[str, Any] = {"present": True}
    for key in list(_SIMPLE_KEYS) + list(extra_keys):
        if key in node:
            result[key] = _to_plain(node[key])
    unknown_keys = [str(k) for k in node.keys() if k not in result]
    if unknown_keys:
        result["keys"] = unknown_keys[:30]
        if len(unknown_keys) > 30:
            result["keys_truncated"] = len(unknown_keys) - 30
    return result


def _classes_from_metainfo(metainfo: Any) -> Optional[List[Any]]:
    classes = _get(metainfo, "classes")
    if classes is None:
        return None
    if isinstance(classes, tuple):
        return list(classes)
    if isinstance(classes, list):
        return classes
    return [classes]


def _summarize_pipeline(pipeline: Any) -> Dict[str, Any]:
    if not isinstance(pipeline, list):
        return {"present": pipeline is not None, "python_type": type(pipeline).__name__}
    steps = []
    for idx, step in enumerate(pipeline[:12]):
        steps.append({"index": idx, "type": _type_of(step) or type(step).__name__})
    result: Dict[str, Any] = {"length": len(pipeline), "first_steps": steps}
    if len(pipeline) > 12:
        result["steps_truncated"] = len(pipeline) - 12
    return result


def _summarize_dataset_chain(dataset: Any, path: str = "dataset") -> List[Dict[str, Any]]:
    chain: List[Dict[str, Any]] = []

    def walk(ds: Any, current_path: str) -> None:
        if not _is_mapping(ds):
            chain.append({"path": current_path, "python_type": type(ds).__name__})
            return
        entry: Dict[str, Any] = {
            "path": current_path,
            "type": _type_of(ds),
        }
        for key in ("data_root", "ann_file", "box_type_3d", "test_mode", "load_eval_anns"):
            if key in ds:
                entry[key] = _to_plain(ds[key])
        data_prefix = _get(ds, "data_prefix")
        if _is_mapping(data_prefix):
            entry["data_prefix_keys"] = [str(k) for k in data_prefix.keys()]
        metainfo = _get(ds, "metainfo")
        classes = _classes_from_metainfo(metainfo)
        if classes is not None:
            entry["classes"] = classes
            entry["num_classes"] = len(classes)
        pipeline = _get(ds, "pipeline")
        if pipeline is not None:
            entry["pipeline"] = _summarize_pipeline(pipeline)
        chain.append(entry)

        inner = _get(ds, "dataset")
        if inner is not None:
            walk(inner, current_path + ".dataset")
        datasets = _get(ds, "datasets")
        if isinstance(datasets, list):
            for idx, item in enumerate(datasets[:10]):
                walk(item, f"{current_path}.datasets[{idx}]")
            if len(datasets) > 10:
                chain.append(
                    {
                        "path": current_path + ".datasets",
                        "items_truncated": len(datasets) - 10,
                    }
                )

    walk(dataset, path)
    return chain


def _summarize_dataloader(cfg: Mapping[str, Any], key: str) -> Dict[str, Any]:
    dataloader = cfg.get(key)
    if dataloader is None:
        return {"present": False}
    if not _is_mapping(dataloader):
        return {"present": True, "python_type": type(dataloader).__name__}
    result: Dict[str, Any] = {"present": True}
    for simple_key in ("batch_size", "num_workers", "persistent_workers", "drop_last"):
        if simple_key in dataloader:
            result[simple_key] = _to_plain(dataloader[simple_key])
    sampler = _get(dataloader, "sampler")
    if sampler is not None:
        result["sampler"] = _summarize_named_mapping(sampler)
    dataset = _get(dataloader, "dataset")
    if dataset is not None:
        result["dataset_chain"] = _summarize_dataset_chain(dataset)
    result["keys"] = [str(k) for k in dataloader.keys()]
    return result


def _summarize_model(model: Any) -> Dict[str, Any]:
    if model is None:
        return {"present": False}
    if not _is_mapping(model):
        return {"present": True, "python_type": type(model).__name__}
    result: Dict[str, Any] = {"present": True, "type": _type_of(model)}
    components: Dict[str, Any] = {}
    for key in _COMPONENT_KEYS:
        component = _get(model, key)
        if component is not None:
            components[key] = _summarize_named_mapping(
                component, extra_keys=("num_classes", "in_channels", "feat_channels")
            )
    if components:
        result["components"] = components
    for cfg_key in ("train_cfg", "test_cfg"):
        value = _get(model, cfg_key)
        if value is not None:
            if _is_mapping(value):
                result[cfg_key] = {"keys": [str(k) for k in value.keys()]}
            else:
                result[cfg_key] = _to_plain(value)
    result["keys"] = [str(k) for k in model.keys()]
    return result


def _summarize_evaluator(cfg: Mapping[str, Any], key: str) -> Dict[str, Any]:
    evaluator = cfg.get(key)
    if evaluator is None:
        return {"present": False}
    if isinstance(evaluator, list):
        return {
            "present": True,
            "items": [_summarize_named_mapping(item) for item in evaluator],
        }
    return _summarize_named_mapping(evaluator)


def _summarize_runtime(cfg: Mapping[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key in (
        "default_scope",
        "work_dir",
        "load_from",
        "resume",
        "log_level",
        "env_cfg",
        "default_hooks",
        "custom_hooks",
        "visualizer",
        "vis_backends",
        "log_processor",
    ):
        if key in cfg:
            value = cfg[key]
            if _is_mapping(value):
                result[key] = {"keys": [str(k) for k in value.keys()]}
                if "type" in value:
                    result[key]["type"] = value["type"]
            elif isinstance(value, list):
                result[key] = {"length": len(value)}
            else:
                result[key] = _to_plain(value)
    return result


def _summarize_config(config_path: str, cfg: Any, overrides: Mapping[str, Any]) -> Dict[str, Any]:
    cfg_dict = _to_plain(cfg)
    if not isinstance(cfg_dict, dict):
        raise TypeError("Parsed config did not produce a dictionary-like object.")
    top_keys = [str(k) for k in cfg_dict.keys()]
    summary: Dict[str, Any] = {
        "config": config_path,
        "applied_overrides": dict(overrides),
        "top_level_keys": top_keys,
        "default_scope": cfg_dict.get("default_scope"),
        "model": _summarize_model(cfg_dict.get("model")),
        "dataloaders": {
            "train": _summarize_dataloader(cfg_dict, "train_dataloader"),
            "val": _summarize_dataloader(cfg_dict, "val_dataloader"),
            "test": _summarize_dataloader(cfg_dict, "test_dataloader"),
        },
        "evaluators": {
            "val": _summarize_evaluator(cfg_dict, "val_evaluator"),
            "test": _summarize_evaluator(cfg_dict, "test_evaluator"),
        },
        "loops": {},
        "optimization": {},
        "runtime": _summarize_runtime(cfg_dict),
    }
    for key in ("train_cfg", "val_cfg", "test_cfg"):
        if key in cfg_dict:
            summary["loops"][key] = _summarize_named_mapping(cfg_dict[key])
    for key in ("optim_wrapper", "param_scheduler", "auto_scale_lr"):
        if key in cfg_dict:
            value = cfg_dict[key]
            if isinstance(value, list):
                summary["optimization"][key] = {
                    "length": len(value),
                    "items": [_summarize_named_mapping(item) for item in value[:10]],
                }
                if len(value) > 10:
                    summary["optimization"][key]["items_truncated"] = len(value) - 10
            else:
                summary["optimization"][key] = _summarize_named_mapping(value)
    legacy = [key for key in ("data", "total_epochs") if key in cfg_dict]
    if legacy:
        summary["legacy_or_compat_keys"] = legacy
    return summary


def _print_dataset_chain(chain: List[Dict[str, Any]], indent: str = "    ") -> None:
    for item in chain:
        label = item.get("path", "dataset")
        dtype = item.get("type") or item.get("python_type") or "unknown"
        print(f"{indent}- {label}: {dtype}")
        for key in ("data_root", "ann_file", "box_type_3d", "test_mode", "load_eval_anns"):
            if key in item:
                print(f"{indent}  {key}: {_short(item[key])}")
        if "num_classes" in item:
            print(f"{indent}  classes: {item['num_classes']} {_short(item.get('classes'))}")
        if "data_prefix_keys" in item:
            print(f"{indent}  data_prefix keys: {', '.join(item['data_prefix_keys'])}")
        if "pipeline" in item:
            pipeline = item["pipeline"]
            length = pipeline.get("length")
            steps = pipeline.get("first_steps", [])
            step_text = ", ".join(
                f"{step['index']}:{step['type']}" for step in steps[:8]
            )
            print(f"{indent}  pipeline: {length} steps [{step_text}]")


def _print_text(summary: Mapping[str, Any], show_top_keys: int) -> None:
    print("MMDetection3D config summary")
    print(f"Config: {summary['config']}")
    overrides = summary.get("applied_overrides") or {}
    if overrides:
        print("Applied overrides:")
        for key, value in overrides.items():
            print(f"  - {key} = {_short(value)}")
    print(f"default_scope: {_short(summary.get('default_scope'))}")

    top_keys = summary.get("top_level_keys", [])
    visible_keys = top_keys[:show_top_keys]
    print(f"top-level keys ({len(top_keys)}): {', '.join(visible_keys)}")
    if len(top_keys) > show_top_keys:
        print(f"  ... {len(top_keys) - show_top_keys} more")

    model = summary.get("model", {})
    print("\nModel:")
    if not model.get("present"):
        print("  not present")
    else:
        print(f"  type: {_short(model.get('type'))}")
        components = model.get("components", {})
        for name, component in components.items():
            ctype = component.get("type")
            extras = []
            for key in ("num_classes", "in_channels", "feat_channels"):
                if key in component:
                    extras.append(f"{key}={_short(component[key])}")
            suffix = f" ({'; '.join(extras)})" if extras else ""
            print(f"  {name}: {_short(ctype)}{suffix}")
        for cfg_key in ("train_cfg", "test_cfg"):
            if cfg_key in model:
                print(f"  {cfg_key}: {_short(model[cfg_key])}")

    print("\nDataloaders:")
    for split, dataloader in summary.get("dataloaders", {}).items():
        print(f"  {split}:")
        if not dataloader.get("present"):
            print("    not present")
            continue
        for key in ("batch_size", "num_workers", "persistent_workers", "drop_last"):
            if key in dataloader:
                print(f"    {key}: {_short(dataloader[key])}")
        sampler = dataloader.get("sampler")
        if sampler:
            print(f"    sampler: {_short(sampler.get('type'))}")
        chain = dataloader.get("dataset_chain")
        if chain:
            _print_dataset_chain(chain, indent="    ")

    print("\nEvaluators:")
    for split, evaluator in summary.get("evaluators", {}).items():
        print(f"  {split}: {_short(evaluator)}")

    print("\nLoops:")
    loops = summary.get("loops", {})
    if loops:
        for key, value in loops.items():
            print(f"  {key}: {_short(value)}")
    else:
        print("  no train/val/test loop keys found")

    print("\nOptimization:")
    optimization = summary.get("optimization", {})
    if optimization:
        for key, value in optimization.items():
            print(f"  {key}: {_short(value)}")
    else:
        print("  no optimization keys found")

    print("\nRuntime:")
    runtime = summary.get("runtime", {})
    if runtime:
        for key, value in runtime.items():
            print(f"  {key}: {_short(value)}")
    else:
        print("  no runtime keys found")

    legacy = summary.get("legacy_or_compat_keys")
    if legacy:
        print("\nLegacy/compatibility keys detected:")
        for key in legacy:
            print(f"  - {key}")


def main() -> int:
    args = _parse_args()
    Config = _load_mmengine_config()
    if Config is None:
        return 2

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"ERROR: config file not found: {args.config}", file=sys.stderr)
        return 2

    try:
        overrides = _parse_overrides(args.cfg_options)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    try:
        cfg = Config.fromfile(str(config_path))
        if overrides:
            cfg.merge_from_dict(overrides)
        summary = _summarize_config(args.config, cfg, overrides)
    except Exception as exc:
        print(
            "ERROR: failed to parse or summarize the config with MMEngine.",
            file=sys.stderr,
        )
        print(f"Failure: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(
            "Check that the config's relative _base_ files are present, required "
            "Python packages can be imported, and --cfg-options are valid.",
            file=sys.stderr,
        )
        return 1

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
    else:
        _print_text(summary, args.show_top_keys)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
