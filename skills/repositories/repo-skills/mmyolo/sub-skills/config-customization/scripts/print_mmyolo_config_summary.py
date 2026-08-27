#!/usr/bin/env python3
"""Print a safe summary of an MMYOLO/MMEngine config.

The helper loads and merges a config, then reports model, dataloader,
runtime, and TTA fields. It does not build a model, dataloader, runner, or
start any training/testing/inference work.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional


MISSING = object()


def parse_override_value(raw: str) -> Any:
    """Parse a lightweight --cfg-options value.

    This intentionally covers common MMEngine override values while keeping
    --help usable without importing mmengine. Bare strings remain strings;
    booleans, None/null, numbers, quoted strings, lists, tuples, and dicts are
    converted with Python literal syntax when possible.
    """
    lowered = raw.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"none", "null"}:
        return None
    try:
        return ast.literal_eval(raw)
    except Exception:
        return raw


class CfgOptionsAction(argparse.Action):
    """Argparse action compatible with simple MMEngine key=value overrides."""

    def __call__(self, parser, namespace, values, option_string=None):  # type: ignore[override]
        merged = getattr(namespace, self.dest, None) or {}
        for item in values:
            if "=" not in item:
                parser.error(
                    f"{option_string} expects key=value pairs; got {item!r}")
            key, raw_value = item.split("=", 1)
            key = key.strip()
            if not key:
                parser.error(f"{option_string} contains an empty key")
            merged[key] = parse_override_value(raw_value)
        setattr(namespace, self.dest, merged)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize an MMYOLO/MMEngine config without building models, "
            "dataloaders, runners, or running training/testing."))
    parser.add_argument("config", help="Path to a MMEngine/MMYOLO config file")
    parser.add_argument(
        "--cfg-options",
        nargs="+",
        action=CfgOptionsAction,
        default=None,
        metavar="KEY=VALUE",
        help=(
            "Merge simple config overrides before summarizing. Values may be "
            "booleans, numbers, quoted strings, lists, tuples, or dicts. "
            "Quote list/tuple values in the shell, for example "
            "model.data_preprocessor.mean=\"[0,0,0]\"."),
    )
    parser.add_argument(
        "--check-tta",
        action="store_true",
        help=(
            "Exit nonzero if the expanded config lacks top-level tta_model "
            "or tta_pipeline."),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the summary as JSON instead of text.",
    )
    return parser


def fail(message: str, code: int = 1) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return code


def import_mmengine_config():
    try:
        from mmengine import Config  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on user env
        raise RuntimeError(
            "mmengine is required to parse MMYOLO configs. Install the "
            "OpenMMLab/MMYOLO runtime, then rerun this helper.") from exc
    return Config


def maybe_register_mmyolo_modules() -> None:
    """Register MMYOLO modules when available; ignore missing installs."""
    try:
        from mmyolo.utils import register_all_modules  # type: ignore

        register_all_modules(init_default_scope=False)
    except Exception:
        return


def load_config(config_path: Path, cfg_options: Optional[Dict[str, Any]] = None):
    Config = import_mmengine_config()
    maybe_register_mmyolo_modules()
    cfg = Config.fromfile(str(config_path))

    # Match MMYOLO's print_config behavior when mmdet helpers are installed.
    try:
        from mmdet.utils import replace_cfg_vals, update_data_root  # type: ignore

        cfg = replace_cfg_vals(cfg)
        update_data_root(cfg)
    except Exception:
        pass

    if cfg_options:
        cfg.merge_from_dict(cfg_options)
    return cfg


def is_mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def cfg_get(obj: Any, path: str, default: Any = MISSING) -> Any:
    current = obj
    for part in path.split(".") if path else []:
        if current is MISSING:
            break
        if isinstance(current, (list, tuple)):
            try:
                current = current[int(part)]
            except Exception:
                current = MISSING
        elif is_mapping(current):
            current = current.get(part, MISSING)
        else:
            current = getattr(current, part, MISSING)
    if current is MISSING:
        if default is MISSING:
            return None
        return default
    return current


def present(obj: Any, path: str) -> bool:
    return cfg_get(obj, path, MISSING) is not MISSING


def plain(value: Any, depth: int = 0) -> Any:
    if depth > 5:
        return "..."
    if value is MISSING:
        return None
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if is_mapping(value):
        return {str(k): plain(v, depth + 1) for k, v in value.items()}
    if isinstance(value, tuple):
        return [plain(v, depth + 1) for v in value]
    if isinstance(value, list):
        return [plain(v, depth + 1) for v in value]
    return repr(value)


def node_type(value: Any) -> Optional[str]:
    if is_mapping(value):
        result = value.get("type")
        return str(result) if result is not None else None
    return None


def short(value: Any, max_len: int = 100) -> str:
    if value is None:
        return "None"
    text = json.dumps(plain(value), ensure_ascii=False, sort_keys=True)
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def unwrap_dataset(dataset: Any) -> Any:
    current = dataset
    seen = 0
    while is_mapping(current) and "dataset" in current and seen < 10:
        current = current.get("dataset")
        seen += 1
    return current


def pipeline_types(dataset: Any) -> List[str]:
    ds = unwrap_dataset(dataset)
    pipeline = cfg_get(ds, "pipeline", [])
    if not isinstance(pipeline, list):
        return []
    types: List[str] = []
    for step in pipeline:
        if is_mapping(step):
            typ = step.get("type")
            types.append(str(typ) if typ is not None else "<dict>")
        else:
            types.append(type(step).__name__)
    return types


def dataset_summary(dataset: Any) -> Dict[str, Any]:
    ds = unwrap_dataset(dataset)
    classes = cfg_get(ds, "metainfo.classes")
    palette = cfg_get(ds, "metainfo.palette")
    summary: Dict[str, Any] = {
        "type": node_type(ds),
        "data_root": cfg_get(ds, "data_root"),
        "ann_file": cfg_get(ds, "ann_file"),
        "data_prefix": plain(cfg_get(ds, "data_prefix")),
        "test_mode": cfg_get(ds, "test_mode"),
        "metainfo_classes": plain(classes),
        "metainfo_num_classes": len(classes) if isinstance(classes, (list, tuple)) else None,
        "palette_length": len(palette) if isinstance(palette, (list, tuple)) else None,
        "pipeline": pipeline_types(dataset),
        "has_batch_shapes_cfg": present(ds, "batch_shapes_cfg") and cfg_get(ds, "batch_shapes_cfg") is not None,
        "batch_shapes_cfg": plain(cfg_get(ds, "batch_shapes_cfg")),
    }
    if is_mapping(ds) and "datasets" in ds:
        datasets = ds.get("datasets") or []
        summary["nested_dataset_types"] = [node_type(item) for item in datasets]
    return summary


def dataloader_summary(cfg: Any, name: str) -> Dict[str, Any]:
    dl = cfg_get(cfg, name, {})
    dataset = cfg_get(dl, "dataset", {})
    return {
        "batch_size": cfg_get(dl, "batch_size"),
        "num_workers": cfg_get(dl, "num_workers"),
        "persistent_workers": cfg_get(dl, "persistent_workers"),
        "drop_last": cfg_get(dl, "drop_last"),
        "sampler": node_type(cfg_get(dl, "sampler", {})),
        "dataset": dataset_summary(dataset),
    }


def scheduler_summary(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, list):
        output = []
        for item in value:
            output.append({
                "type": node_type(item),
                "begin": cfg_get(item, "begin"),
                "end": cfg_get(item, "end"),
                "T_max": cfg_get(item, "T_max"),
                "by_epoch": cfg_get(item, "by_epoch"),
                "convert_to_iter_based": cfg_get(item, "convert_to_iter_based"),
            })
        return output
    if is_mapping(value):
        return {"type": node_type(value), **plain(value)}
    return plain(value)


def hook_summary(hooks: Any) -> Any:
    if hooks is None:
        return None
    if is_mapping(hooks):
        result = {}
        for name, hook in hooks.items():
            result[name] = {
                "type": node_type(hook),
                "interval": cfg_get(hook, "interval"),
                "max_keep_ckpts": cfg_get(hook, "max_keep_ckpts"),
                "save_best": cfg_get(hook, "save_best"),
                "max_epochs": cfg_get(hook, "max_epochs"),
                "warmup_mim_iter": cfg_get(hook, "warmup_mim_iter"),
            }
        return result
    if isinstance(hooks, list):
        return [
            {
                "type": node_type(item),
                "switch_epoch": cfg_get(item, "switch_epoch"),
                "num_last_epochs": cfg_get(item, "num_last_epochs"),
                "priority": cfg_get(item, "priority"),
            }
            for item in hooks
        ]
    return plain(hooks)


def visualizer_backends(cfg: Any) -> List[str]:
    backends = cfg_get(cfg, "visualizer.vis_backends", [])
    if not isinstance(backends, list):
        return []
    return [node_type(item) or "<dict>" for item in backends]


def build_summary(cfg: Any, config_path: Path, cfg_options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    model = cfg_get(cfg, "model", {})
    bbox_head = cfg_get(model, "bbox_head", {})
    head_module = cfg_get(bbox_head, "head_module", {})
    test_dataset = cfg_get(cfg, "test_dataloader.dataset", {})
    test_dataset_unwrapped = unwrap_dataset(test_dataset)

    summary = {
        "config": {
            "path": str(config_path),
            "basename": config_path.name,
            "cfg_options": plain(cfg_options or {}),
            "default_scope": cfg_get(cfg, "default_scope"),
            "work_dir": cfg_get(cfg, "work_dir"),
            "load_from": cfg_get(cfg, "load_from"),
            "resume": cfg_get(cfg, "resume"),
        },
        "model": {
            "type": node_type(model),
            "data_preprocessor": node_type(cfg_get(model, "data_preprocessor", {})),
            "backbone": node_type(cfg_get(model, "backbone", {})),
            "neck": node_type(cfg_get(model, "neck", {})),
            "bbox_head": node_type(bbox_head),
            "head_module": node_type(head_module),
            "head_num_classes": cfg_get(head_module, "num_classes"),
            "prior_generator": node_type(cfg_get(bbox_head, "prior_generator", {})),
            "train_cfg_assigner_num_classes": cfg_get(model, "train_cfg.assigner.num_classes"),
            "train_cfg_initial_assigner_num_classes": cfg_get(model, "train_cfg.initial_assigner.num_classes"),
            "test_cfg": {
                "score_thr": cfg_get(model, "test_cfg.score_thr"),
                "nms_pre": cfg_get(model, "test_cfg.nms_pre"),
                "nms": plain(cfg_get(model, "test_cfg.nms")),
                "max_per_img": cfg_get(model, "test_cfg.max_per_img"),
                "multi_label": cfg_get(model, "test_cfg.multi_label"),
            },
        },
        "dataloaders": {
            "train": dataloader_summary(cfg, "train_dataloader"),
            "val": dataloader_summary(cfg, "val_dataloader"),
            "test": dataloader_summary(cfg, "test_dataloader"),
        },
        "evaluators": {
            "val": {
                "type": node_type(cfg_get(cfg, "val_evaluator", {})),
                "ann_file": cfg_get(cfg, "val_evaluator.ann_file"),
                "metric": cfg_get(cfg, "val_evaluator.metric"),
                "format_only": cfg_get(cfg, "val_evaluator.format_only"),
                "outfile_prefix": cfg_get(cfg, "val_evaluator.outfile_prefix"),
            },
            "test": {
                "type": node_type(cfg_get(cfg, "test_evaluator", {})),
                "ann_file": cfg_get(cfg, "test_evaluator.ann_file"),
                "metric": cfg_get(cfg, "test_evaluator.metric"),
                "format_only": cfg_get(cfg, "test_evaluator.format_only"),
                "outfile_prefix": cfg_get(cfg, "test_evaluator.outfile_prefix"),
            },
        },
        "runtime": {
            "train_cfg": plain(cfg_get(cfg, "train_cfg")),
            "val_cfg": plain(cfg_get(cfg, "val_cfg")),
            "test_cfg": plain(cfg_get(cfg, "test_cfg")),
            "optim_wrapper": {
                "type": node_type(cfg_get(cfg, "optim_wrapper", {})),
                "optimizer_type": node_type(cfg_get(cfg, "optim_wrapper.optimizer", {})),
                "lr": cfg_get(cfg, "optim_wrapper.optimizer.lr"),
                "momentum": cfg_get(cfg, "optim_wrapper.optimizer.momentum"),
                "weight_decay": cfg_get(cfg, "optim_wrapper.optimizer.weight_decay"),
                "batch_size_per_gpu": cfg_get(cfg, "optim_wrapper.optimizer.batch_size_per_gpu"),
            },
            "param_scheduler": scheduler_summary(cfg_get(cfg, "param_scheduler")),
            "default_hooks": hook_summary(cfg_get(cfg, "default_hooks")),
            "custom_hooks": hook_summary(cfg_get(cfg, "custom_hooks")),
            "env_cfg": plain(cfg_get(cfg, "env_cfg")),
            "visualizer_backends": visualizer_backends(cfg),
            "log_processor": plain(cfg_get(cfg, "log_processor")),
            "log_level": cfg_get(cfg, "log_level"),
        },
        "tta": {
            "has_tta_model": present(cfg, "tta_model"),
            "has_tta_pipeline": present(cfg, "tta_pipeline"),
            "img_scales": plain(cfg_get(cfg, "img_scales")),
            "tta_model_type": node_type(cfg_get(cfg, "tta_model", {})),
            "tta_pipeline_steps": pipeline_types({"pipeline": cfg_get(cfg, "tta_pipeline", [])}),
            "test_dataset_has_batch_shapes_cfg": present(test_dataset_unwrapped, "batch_shapes_cfg") and cfg_get(test_dataset_unwrapped, "batch_shapes_cfg") is not None,
        },
    }
    return summary


def print_section(title: str) -> None:
    print(f"\n## {title}")


def print_kv(label: str, value: Any) -> None:
    print(f"{label}: {short(value)}")


def emit_text(summary: Dict[str, Any]) -> None:
    print("MMYOLO config summary")
    print("=====================")

    print_section("Config")
    for key in ["basename", "default_scope", "work_dir", "load_from", "resume", "cfg_options"]:
        print_kv(key, summary["config"].get(key))

    print_section("Model")
    model = summary["model"]
    for key in [
            "type", "data_preprocessor", "backbone", "neck", "bbox_head",
            "head_module", "head_num_classes", "prior_generator",
            "train_cfg_initial_assigner_num_classes",
            "train_cfg_assigner_num_classes"]:
        print_kv(key, model.get(key))
    print_kv("test_cfg", model.get("test_cfg"))

    print_section("Dataloaders")
    for name, info in summary["dataloaders"].items():
        ds = info["dataset"]
        print(f"[{name}]")
        for key in ["batch_size", "num_workers", "persistent_workers", "drop_last", "sampler"]:
            print_kv(f"  {key}", info.get(key))
        for key in [
                "type", "data_root", "ann_file", "data_prefix", "test_mode",
                "metainfo_classes", "metainfo_num_classes", "palette_length",
                "has_batch_shapes_cfg", "pipeline"]:
            print_kv(f"  dataset.{key}", ds.get(key))

    print_section("Evaluators")
    for name, info in summary["evaluators"].items():
        print(f"[{name}]")
        for key in ["type", "ann_file", "metric", "format_only", "outfile_prefix"]:
            print_kv(f"  {key}", info.get(key))

    print_section("Runtime")
    runtime = summary["runtime"]
    for key in [
            "train_cfg", "val_cfg", "test_cfg", "optim_wrapper",
            "param_scheduler", "default_hooks", "custom_hooks",
            "visualizer_backends", "log_level"]:
        print_kv(key, runtime.get(key))

    print_section("TTA")
    for key, value in summary["tta"].items():
        print_kv(key, value)
    if summary["tta"].get("has_tta_model") and summary["tta"].get("has_tta_pipeline"):
        if summary["tta"].get("test_dataset_has_batch_shapes_cfg"):
            print(
                "TTA note: MMYOLO test logic disables test dataset "
                "batch_shapes_cfg during TTA because it is incompatible with "
                "TTA output sizing.")
    else:
        print("TTA note: --tta requires both top-level tta_model and tta_pipeline.")


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    config_path = Path(args.config).expanduser()
    if not config_path.is_file():
        return fail(f"config file not found: {config_path}")

    try:
        cfg = load_config(config_path, args.cfg_options)
        summary = build_summary(cfg, config_path, args.cfg_options)
    except RuntimeError as exc:
        return fail(str(exc))
    except Exception as exc:
        return fail(f"failed to parse config: {exc}")

    has_tta_model = summary["tta"]["has_tta_model"]
    has_tta_pipeline = summary["tta"]["has_tta_pipeline"]
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        emit_text(summary)

    if args.check_tta and not (has_tta_model and has_tta_pipeline):
        missing = []
        if not has_tta_model:
            missing.append("tta_model")
        if not has_tta_pipeline:
            missing.append("tta_pipeline")
        print(
            "ERROR: TTA requested but missing " + ", ".join(missing),
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
