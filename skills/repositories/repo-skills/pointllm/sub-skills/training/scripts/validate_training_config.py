#!/usr/bin/env python3
"""Validate PointLLM training paths and flags without launching training.

This script intentionally uses the standard library only. It reads JSON or a
small, dependency-free YAML subset (and uses PyYAML when available), checks
local path shapes, and applies the source repository's Stage 1/Stage 2
invariants. It never invokes torchrun, imports PointLLM, or loads torch.
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


STAGE_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "1": {
        "stage_2": False,
        "tune_mm_mlp_adapter": True,
        "fix_llm": True,
        "fix_pointnet": True,
        "model_max_length": 2048,
        "pointnum": 8192,
        "use_color": True,
        "conversation_types": ["simple_description"],
        "per_device_train_batch_size": 16,
        "per_device_eval_batch_size": 4,
        "learning_rate": 2e-3,
        "bf16": True,
        "gradient_checkpointing": True,
    },
    "2": {
        "stage_2": True,
        "tune_mm_mlp_adapter": True,
        "fix_llm": False,
        "fix_pointnet": True,
        "model_max_length": 2048,
        "pointnum": 8192,
        "use_color": True,
        "conversation_types": ["detailed_description", "single_round", "multi_round"],
        "per_device_train_batch_size": 4,
        "per_device_eval_batch_size": 1,
        "learning_rate": 2e-5,
        "bf16": True,
        "gradient_checkpointing": True,
        "fsdp": "full_shard auto_wrap",
        "fsdp_transformer_layer_cls_to_wrap": "LlamaDecoderLayer",
    },
}

PATH_FIELDS = {
    "model_name_or_path": "model directory or hub identifier",
    "data_path": "point-cloud directory",
    "anno_path": "annotation JSON file",
    "output_dir": "output directory",
    "point_backbone_ckpt": "PointBERT checkpoint file",
    "pretrained_mm_mlp_adapter": "adapter path",
}
BOOL_FIELDS = {
    "stage_2", "tune_mm_mlp_adapter", "fix_llm", "fix_pointnet", "use_color",
    "bf16", "gradient_checkpointing", "split_train_val", "model_debug",
    "remove_unused_columns", "force_fsdp",
}
KNOWN_CUSTOM = {
    "model_name_or_path", "version", "data_path", "anno_path", "use_color",
    "data_debug_num", "split_train_val", "split_ratio", "pointnum",
    "conversation_types", "is_multimodal", "cache_dir", "optim",
    "model_max_length", "model_debug", "fix_llm", "fix_pointnet",
    "remove_unused_columns", "force_fsdp", "tune_mm_mlp_adapter", "stage_2",
    "pretrained_mm_mlp_adapter", "detatch_point_token", "point_backbone_ckpt",
    "fsdp", "fsdp_transformer_layer_cls_to_wrap", "bf16",
    "gradient_checkpointing", "evaluation_strategy", "save_strategy",
    "per_device_train_batch_size", "per_device_eval_batch_size", "num_train_epochs",
    "gradient_accumulation_steps", "learning_rate", "weight_decay", "warmup_ratio",
    "lr_scheduler_type", "logging_steps", "save_steps", "save_total_limit",
    "report_to", "eval_steps", "output_dir",
}


def canonical_key(key: str) -> str:
    key = key.strip().lstrip("-").replace("-", "_")
    return key


def scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value.startswith(("'", '"')) and value.endswith(value[0]):
        return value[1:-1]
    low = value.lower()
    if low in {"true", "yes", "on"}:
        return True
    if low in {"false", "no", "off"}:
        return False
    if low in {"null", "none", "~"}:
        return None
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        pass
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value


def strip_comment(line: str) -> str:
    quote = None
    for i, char in enumerate(line):
        if char in "'\"":
            quote = None if quote == char else (char if quote is None else quote)
        elif char == "#" and quote is None:
            return line[:i]
    return line


def simple_yaml(text: str) -> Dict[str, Any]:
    """Parse flat or one-level nested YAML sufficient for run configs."""
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Dict[str, Any]]] = [(-1, root)]
    last_key: Tuple[int, Dict[str, Any], str] | None = None
    for raw in text.splitlines():
        raw = strip_comment(raw).rstrip()
        if not raw.strip() or raw.lstrip().startswith("---"):
            continue
        indent = len(raw) - len(raw.lstrip())
        content = raw.strip()
        if content.startswith("-"):
            if last_key is None:
                raise ValueError("YAML list item has no parent key")
            parent_indent, parent, key = last_key
            if indent <= parent_indent:
                raise ValueError("unsupported YAML indentation")
            if not isinstance(parent.get(key), list):
                parent[key] = []
            parent[key].append(scalar(content[1:].strip()))
            continue
        if ":" not in content:
            raise ValueError(f"unsupported YAML line: {content}")
        key, raw_value = content.split(":", 1)
        key = canonical_key(key)
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        target = stack[-1][1]
        if raw_value.strip() == "":
            child: Dict[str, Any] = {}
            target[key] = child
            stack.append((indent, child))
            last_key = (indent, target, key)
        else:
            target[key] = scalar(raw_value)
            last_key = (indent, target, key)
    return root


def flatten_mapping(value: Any, prefix: str = "") -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    if not isinstance(value, dict):
        return result
    for raw_key, item in value.items():
        key = canonical_key(str(raw_key))
        full = f"{prefix}_{key}" if prefix else key
        if isinstance(item, dict):
            result.update(flatten_mapping(item, full))
        else:
            result[full] = item
    return result


def load_config(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        loaded = json.loads(text)
    else:
        try:
            import yaml  # type: ignore
            loaded = yaml.safe_load(text)
        except ImportError:
            loaded = simple_yaml(text)
        except Exception as exc:
            raise ValueError(f"YAML parse failed: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ValueError("configuration root must be a mapping")
    return flatten_mapping(loaded)


def path_is_remote(value: str) -> bool:
    return "://" in value or value.startswith(("hf:", "s3:", "gs:"))


def bool_value(value: Any, key: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.lower() in {"true", "false"}:
        return value.lower() == "true"
    raise ValueError(f"{key} must be true or false, got {value!r}")


def add_path_issue(
    issues: List[str], warnings: List[str], key: str, value: Any,
    kind: str, allow_missing: bool, required: bool = True,
) -> None:
    if value is None or value == "":
        if required:
            issues.append(f"{key} is required ({kind})")
        return
    if not isinstance(value, str):
        issues.append(f"{key} must be a string path, got {type(value).__name__}")
        return
    if path_is_remote(value):
        warnings.append(f"{key}={value!r} is remote; local existence was not checked")
        return
    path = Path(value).expanduser()
    if path.exists():
        if kind.endswith("directory") and not path.is_dir():
            issues.append(f"{key} exists but is not a directory: {value}")
        elif kind.endswith("file") and not path.is_file():
            issues.append(f"{key} exists but is not a file: {value}")
        return
    if key == "output_dir":
        warnings.append(f"output_dir does not exist yet and may be created: {value}")
    elif allow_missing:
        warnings.append(f"missing planned {kind}: {value}")
    else:
        issues.append(f"missing {kind}: {value} (use --allow-missing only for planning)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate PointLLM training config; never launches torchrun."
    )
    parser.add_argument("--stage", choices=("1", "2"), required=True)
    parser.add_argument("--config", type=Path, help="JSON or YAML run configuration")
    parser.add_argument("--allow-missing", action="store_true", help="warn instead of failing for missing planned inputs")
    parser.add_argument("--check-runtime", action="store_true", help="check importable torch/Transformers and FlashAttention presence")
    parser.add_argument("--entrypoint", choices=("train_mem", "train"), default="train_mem")
    parser.add_argument("--set", dest="sets", action="append", default=[], metavar="KEY=VALUE", help="override a config value; repeatable")
    for name in ("model_name_or_path", "data_path", "anno_path", "output_dir", "point_backbone_ckpt"):
        parser.add_argument(f"--{name.replace('_', '-')}", dest=name)
    parser.add_argument("--conversation-types", nargs="+", dest="conversation_types")
    for name in sorted(BOOL_FIELDS):
        parser.add_argument(f"--{name.replace('_', '-')}", dest=name, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    issues: List[str] = []
    warnings: List[str] = []
    values = dict(STAGE_DEFAULTS[args.stage])

    if args.config:
        if not args.config.is_file():
            issues.append(f"config file does not exist: {args.config}")
        else:
            try:
                values.update(load_config(args.config))
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                issues.append(f"could not read config {args.config}: {exc}")

    for item in args.sets:
        if "=" not in item:
            issues.append(f"--set requires KEY=VALUE, got {item!r}")
            continue
        key, raw = item.split("=", 1)
        key = canonical_key(key)
        values[key] = scalar(raw)

    for name in PATH_FIELDS:
        explicit = getattr(args, name, None)
        if explicit is not None:
            values[name] = explicit
    if args.conversation_types is not None:
        values["conversation_types"] = args.conversation_types

    for name in BOOL_FIELDS:
        raw = getattr(args, name, None)
        if raw is not None:
            try:
                values[name] = bool_value(raw, name)
            except ValueError as exc:
                issues.append(str(exc))

    unknown = sorted(key for key in values if key not in KNOWN_CUSTOM)
    if unknown:
        warnings.append("unrecognized keys are retained for inherited Trainer args: " + ", ".join(unknown))

    for key in BOOL_FIELDS:
        if key in values:
            try:
                values[key] = bool_value(values[key], key)
            except ValueError as exc:
                issues.append(str(exc))

    if values.get("version", "v1") != "v1":
        issues.append("version must be v1; the source training code rejects v0")
    if values.get("stage_2") is not (args.stage == "2"):
        issues.append(f"stage {args.stage} requires stage_2={args.stage == '2'}")
    if not isinstance(values.get("conversation_types"), list) or not values["conversation_types"]:
        issues.append("conversation_types must be a non-empty list")
    for key in ("model_max_length", "pointnum", "per_device_train_batch_size"):
        if key in values:
            try:
                if int(values[key]) <= 0:
                    issues.append(f"{key} must be positive")
            except (TypeError, ValueError):
                issues.append(f"{key} must be an integer")
    if args.stage == "1" and not values.get("point_backbone_ckpt"):
        issues.append("stage 1 requires point_backbone_ckpt")
    if args.stage == "2" and values.get("point_backbone_ckpt"):
        warnings.append("stage 2 does not load point_backbone_ckpt directly; verify the Stage-1 model directory instead")

    fsdp = str(values.get("fsdp") or "").strip()
    if args.stage == "2" and not fsdp:
        warnings.append("stage 2 profile normally uses fsdp='full_shard auto_wrap'")
    if fsdp and values.get("fix_llm") is True:
        warnings.append("FSDP with frozen parameters follows the source's experimental use_orig_params path")
    if fsdp and values.get("fsdp_transformer_layer_cls_to_wrap") != "LlamaDecoderLayer":
        warnings.append("FSDP auto-wrap class differs from the source Stage-2 profile")
    if values.get("bf16") is True:
        warnings.append("bf16 requires a supported accelerator/runtime; this script does not launch a tensor operation")

    add_path_issue(issues, warnings, "model_name_or_path", values.get("model_name_or_path"), "model directory or hub identifier", args.allow_missing)
    add_path_issue(issues, warnings, "data_path", values.get("data_path"), "point-cloud directory", args.allow_missing)
    add_path_issue(issues, warnings, "anno_path", values.get("anno_path"), "annotation JSON file", args.allow_missing)
    add_path_issue(issues, warnings, "output_dir", values.get("output_dir"), "output directory", args.allow_missing)
    add_path_issue(issues, warnings, "point_backbone_ckpt", values.get("point_backbone_ckpt"), "PointBERT checkpoint file", args.allow_missing, required=args.stage == "1")

    anno_path = values.get("anno_path")
    if isinstance(anno_path, str) and not path_is_remote(anno_path) and Path(anno_path).is_file():
        try:
            annotation_root = json.loads(Path(anno_path).read_text(encoding="utf-8"))
            if not isinstance(annotation_root, list):
                issues.append("anno_path JSON root must be a list of annotation records")
            elif not annotation_root:
                issues.append("anno_path JSON contains no annotation records")
            else:
                selected_types = values.get("conversation_types") or []
                observed_types = {
                    item.get("conversation_type", "simple_description")
                    for item in annotation_root[:1000]
                    if isinstance(item, dict)
                }
                if selected_types and observed_types and not observed_types.intersection(selected_types):
                    warnings.append("the first sampled annotation records contain none of the selected conversation_types")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            issues.append(f"invalid annotation JSON {anno_path}: {exc}")

    model_path = values.get("model_name_or_path")
    if isinstance(model_path, str) and not path_is_remote(model_path) and Path(model_path).is_dir():
        model_config = Path(model_path) / "config.json"
        if model_config.is_file():
            try:
                cfg = json.loads(model_config.read_text(encoding="utf-8"))
                if not isinstance(cfg, dict):
                    issues.append(f"model config is not a JSON object: {model_config}")
                else:
                    name = str(cfg.get("point_backbone_config_name", ""))
                    ckpt = str(values.get("point_backbone_ckpt", ""))
                    if name and "base" in name.lower() and "v1.2" in ckpt.lower():
                        issues.append("model config selects the v1.1 base PointBERT but checkpoint looks like v1.2")
                    if name and "2layer" in name.lower() and "v1.1" in ckpt.lower():
                        issues.append("model config selects the v1.2 2-layer PointBERT but checkpoint looks like v1.1")
            except (OSError, json.JSONDecodeError) as exc:
                issues.append(f"invalid model config JSON {model_config}: {exc}")

    if args.check_runtime:
        for module in ("torch", "transformers"):
            if importlib.util.find_spec(module) is None:
                issues.append(f"runtime module is not importable: {module}")
        if args.entrypoint == "train_mem" and importlib.util.find_spec("flash_attn") is None:
            issues.append("train_mem entrypoint requires importable flash_attn")
        if fsdp and importlib.util.find_spec("torch") is None:
            issues.append("FSDP requested but torch is not importable")

    print(f"PointLLM training config: stage {args.stage} (validation only)")
    print(f"entrypoint: {args.entrypoint}; paths checked: {not args.allow_missing}")
    if warnings:
        print("WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
    if issues:
        print("ERRORS:")
        for issue in issues:
            print(f"  - {issue}")
        print("Result: INVALID (no training command was launched)")
        return 2
    print("Result: VALIDATED (no training command was launched)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
