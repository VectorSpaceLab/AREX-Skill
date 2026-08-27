#!/usr/bin/env python3
"""Safely preview ModelScope TrainingArgs-style CLI flags.

This helper is bundled with the DisCo ModelScope training-and-evaluation
sub-skill. It mirrors the public base TrainingArgs mapping closely enough for
planning, but intentionally does not import ModelScope, read datasets, download
models, create work directories, or launch train/eval jobs.

Examples:
  python build_training_args_preview.py --max_epochs 1 --lr 1e-5 --format summary
  python build_training_args_preview.py --optimizer_params weight_decay=0.01,eps=1e-8 --format json
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class ArgSpec:
    name: str
    default: Any
    cfg_node: str | tuple[str, ...] | None = None
    choices: tuple[str, ...] | None = None
    flattened: bool = False
    help: str = ""


SPECS: tuple[ArgSpec, ...] = (
    # DatasetArgs
    ArgSpec("train_dataset_name", None, help="Training dataset id or local directory."),
    ArgSpec("val_dataset_name", None, help="Validation/evaluation dataset id or local directory."),
    ArgSpec("train_subset_name", None, help="Training dataset subset name."),
    ArgSpec("val_subset_name", None, help="Validation dataset subset name."),
    ArgSpec("train_split", None, help="Training split name."),
    ArgSpec("val_split", None, help="Validation split name."),
    ArgSpec("train_dataset_namespace", "modelscope", help="Training dataset namespace."),
    ArgSpec("val_dataset_namespace", "modelscope", help="Validation dataset namespace."),
    ArgSpec("dataset_json_file", None, help="Complex dataset JSON mapping file path; not read by this helper."),
    # ModelArgs
    ArgSpec("task", None, "task", help="Task code."),
    ArgSpec("model", None, help="Model id or local model directory; not resolved by this helper."),
    ArgSpec("model_revision", None, help="Model revision; not resolved by this helper."),
    ArgSpec("model_type", None, "model.type", help="Model type if no model config is used."),
    # TrainArgs
    ArgSpec("seed", 42, help="Random seed."),
    ArgSpec("per_device_train_batch_size", 16, "train.dataloader.batch_size_per_gpu", help="Train batch size per device/process."),
    ArgSpec("train_data_worker", 0, "train.dataloader.workers_per_gpu", help="Train dataloader workers per device/process."),
    ArgSpec("train_shuffle", False, "train.dataloader.shuffle", help="Whether to shuffle training data."),
    ArgSpec("train_drop_last", False, "train.dataloader.drop_last", help="Whether to drop the last train batch."),
    ArgSpec("per_device_eval_batch_size", 16, "evaluation.dataloader.batch_size_per_gpu", help="Eval batch size per device/process."),
    ArgSpec("eval_data_worker", 0, "evaluation.dataloader.workers_per_gpu", help="Eval dataloader workers per device/process."),
    ArgSpec("eval_shuffle", False, "evaluation.dataloader.shuffle", help="Whether to shuffle eval data."),
    ArgSpec("eval_drop_last", False, "evaluation.dataloader.drop_last", help="Whether to drop the last eval batch."),
    ArgSpec("max_epochs", 5, "train.max_epochs", help="Maximum training epochs."),
    ArgSpec("work_dir", "./train_target", "train.work_dir", help="Real jobs write logs/checkpoints here; this helper does not create it."),
    ArgSpec("lr", 5e-5, "train.optimizer.lr", help="Optimizer learning rate."),
    ArgSpec("lr_scheduler", "LinearLR", "train.lr_scheduler.type", help="LR scheduler type."),
    ArgSpec("optimizer", "AdamW", "train.optimizer.type", help="Optimizer type."),
    ArgSpec("optimizer_params", None, "train.optimizer", flattened=True, help="Comma-separated optimizer key=value values."),
    ArgSpec("lr_scheduler_params", None, "train.lr_scheduler", flattened=True, help="Comma-separated scheduler key=value values."),
    ArgSpec("lr_strategy", "by_epoch", "train.lr_scheduler.options.lr_strategy", ("by_epoch", "by_step", "no"), help="LR strategy."),
    ArgSpec("local_rank", 0, help="Local rank; usually set by launcher."),
    ArgSpec("logging_interval", 5, "train.logging.interval", help="Text logging interval."),
    ArgSpec("eval_strategy", "by_epoch", "evaluation.period.eval_strategy", ("by_epoch", "by_step", "no"), help="Evaluation strategy."),
    ArgSpec("eval_interval", 1, "evaluation.period.interval", help="Evaluation interval."),
    ArgSpec("eval_metrics", None, "evaluation.metrics", help="Evaluation metric name/config."),
    ArgSpec("save_strategy", "by_epoch", "train.checkpoint.period.save_strategy", ("by_epoch", "by_step", "no"), help="Checkpoint save strategy."),
    ArgSpec("save_interval", 1, "train.checkpoint.period.interval", help="Checkpoint save interval."),
    ArgSpec("save_best_checkpoint", False, "train.checkpoint.best.save_best", help="Whether to save best checkpoints."),
    ArgSpec("metric_for_best_model", None, "train.checkpoint.best.metric_key", help="Metric key for best checkpoint."),
    ArgSpec("metric_rule_for_best_model", "max", "train.checkpoint.best.rule", ("max", "min"), help="Best metric comparison rule."),
    ArgSpec("max_checkpoint_num", None, "train.checkpoint.period.max_checkpoint_num", help="Maximum periodic checkpoints to keep."),
    ArgSpec("max_checkpoint_num_best", 1, "train.checkpoint.best.max_checkpoint_num", help="Maximum best checkpoints to keep."),
    ArgSpec("push_to_hub", False, "train.checkpoint.period.push_to_hub", help="Whether real jobs push periodic checkpoints to Hub."),
    ArgSpec("repo_id", None, "train.checkpoint.period.hub_repo_id", help="Hub repo id for periodic checkpoints."),
    ArgSpec("hub_token", None, "train.checkpoint.period.hub_token", help="Hub token; masked in output."),
    ArgSpec("private_hub", True, "train.checkpoint.period.private_hub", help="Whether periodic Hub repo is private."),
    ArgSpec("hub_revision", "master", "train.checkpoint.period.hub_revision", help="Hub revision for periodic checkpoints."),
    ArgSpec("push_to_hub_best", False, "train.checkpoint.best.push_to_hub", help="Whether real jobs push best checkpoints to Hub."),
    ArgSpec("repo_id_best", None, "train.checkpoint.best.hub_repo_id", help="Hub repo id for best checkpoints."),
    ArgSpec("hub_token_best", None, "train.checkpoint.best.hub_token", help="Hub token for best checkpoints; masked in output."),
    ArgSpec("private_hub_best", True, "train.checkpoint.best.private_hub", help="Whether best Hub repo is private."),
    ArgSpec("hub_revision_best", "master", "train.checkpoint.best.hub_revision", help="Hub revision for best checkpoints."),
    # TrainingArgs control field
    ArgSpec("use_model_config", False, help="If true, preview only manually supplied mapped fields by default."),
)

SPEC_BY_NAME = {spec.name: spec for spec in SPECS}
SECRET_RE = re.compile(r"(token|secret|password|credential)", re.IGNORECASE)


class PreviewError(ValueError):
    """User-facing parser/config error."""


def parse_scalar(value: str) -> Any:
    const_map = {
        "True": True,
        "true": True,
        "FALSE": False,
        "False": False,
        "false": False,
        "None": None,
        "none": None,
        "null": None,
    }
    if value in const_map:
        return const_map[value]
    stripped = value.strip()
    if (stripped.startswith("'") and stripped.endswith("'")) or (
        stripped.startswith('"') and stripped.endswith('"')
    ):
        return stripped[1:-1]
    if re.fullmatch(r"[+-]?\d+", stripped):
        try:
            return int(stripped)
        except ValueError:
            pass
    if re.fullmatch(r"[+-]?(?:(?:\d+\.\d*)|(?:\.\d+)|(?:\d+))(?:[eE][+-]?\d+)?", stripped):
        try:
            return float(stripped)
        except ValueError:
            pass
    return value


def find_next_top_level_comma(text: str) -> int:
    paren = bracket = brace = 0
    quote: str | None = None
    for idx, char in enumerate(text):
        if quote:
            if char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
        elif char == "(":
            paren += 1
        elif char == ")":
            paren -= 1
        elif char == "[":
            bracket += 1
        elif char == "]":
            bracket -= 1
        elif char == "{":
            brace += 1
        elif char == "}":
            brace -= 1
        elif char == "," and paren == bracket == brace == 0:
            return idx
        if paren < 0 or bracket < 0 or brace < 0:
            raise PreviewError(f"imbalanced brackets in value: {text!r}")
    if quote or paren or bracket or brace:
        raise PreviewError(f"imbalanced quotes or brackets in value: {text!r}")
    return len(text)


def parse_cli_value(value: str) -> Any:
    """Parse values like ModelScope's SingleAction, with safer booleans."""
    text = value.strip()
    is_tuple = False
    if len(text) >= 2 and text[0] == "(" and text[-1] == ")":
        is_tuple = True
        text = text[1:-1]
    elif len(text) >= 2 and text[0] == "[" and text[-1] == "]":
        text = text[1:-1]
    elif "," not in text:
        return parse_scalar(text)

    values: list[Any] = []
    while text:
        comma_idx = find_next_top_level_comma(text)
        chunk = text[:comma_idx].strip()
        if chunk:
            values.append(parse_cli_value(chunk))
        text = text[comma_idx + 1 :]
    return tuple(values) if is_tuple else values


def split_flattened_pairs(raw: Any) -> dict[str, Any]:
    if raw in (None, ""):
        return {}
    if isinstance(raw, str):
        chunks: Iterable[Any] = split_top_level_commas(raw)
    elif isinstance(raw, (list, tuple)):
        chunks = raw
    else:
        raise PreviewError(f"flattened params must be a string/list, got {type(raw).__name__}")

    params: dict[str, Any] = {}
    for chunk in chunks:
        item = str(chunk).strip()
        if not item:
            continue
        if "=" not in item:
            raise PreviewError(f"flattened parameter {item!r} is not key=value")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise PreviewError(f"flattened parameter {item!r} has an empty key")
        params[key] = parse_cli_value(value.strip())
    return params


def split_top_level_commas(text: str) -> list[str]:
    chunks: list[str] = []
    remaining = text
    while remaining:
        comma_idx = find_next_top_level_comma(remaining)
        chunks.append(remaining[:comma_idx])
        remaining = remaining[comma_idx + 1 :]
    return chunks


def set_nested(tree: dict[str, Any], dotted: str, value: Any) -> None:
    node = tree
    parts = dotted.split(".")
    for part in parts[:-1]:
        current = node.get(part)
        if not isinstance(current, dict):
            current = {}
            node[part] = current
        node = current
    leaf = parts[-1]
    if isinstance(value, dict) and isinstance(node.get(leaf), dict):
        node[leaf].update(value)
    else:
        node[leaf] = value


def mask_secrets(value: Any, key_path: str = "") -> Any:
    if SECRET_RE.search(key_path):
        if value not in (None, "", False):
            return "***MASKED***"
        return value
    if isinstance(value, dict):
        return {k: mask_secrets(v, f"{key_path}.{k}" if key_path else k) for k, v in value.items()}
    if isinstance(value, list):
        return [mask_secrets(v, key_path) for v in value]
    if isinstance(value, tuple):
        return [mask_secrets(v, key_path) for v in value]
    return value


def yamlish(value: Any, indent: int = 0) -> str:
    pad = " " * indent
    if isinstance(value, dict):
        if not value:
            return "{}"
        lines: list[str] = []
        for key, val in value.items():
            if isinstance(val, dict):
                nested = yamlish(val, indent + 2)
                lines.append(f"{pad}{key}:")
                lines.append(nested)
            elif isinstance(val, list):
                if not val:
                    lines.append(f"{pad}{key}: []")
                else:
                    lines.append(f"{pad}{key}:")
                    for item in val:
                        if isinstance(item, dict):
                            lines.append(f"{pad}  -")
                            lines.append(yamlish(item, indent + 4))
                        else:
                            lines.append(f"{pad}  - {format_scalar(item)}")
            else:
                lines.append(f"{pad}{key}: {format_scalar(val)}")
        return "\n".join(lines)
    return format_scalar(value)


def format_scalar(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if text == "" or re.search(r"[:#\[\]{}\n]|^\s|\s$", text):
        return json.dumps(text, ensure_ascii=False)
    return text


def parse_unknown_pairs(unknown: list[str]) -> tuple[dict[str, Any], list[str]]:
    filtered = [item for item in unknown if item not in ("\\", "\n") and not item.startswith("--local-rank=")]
    parsed: dict[str, Any] = {}
    manual: list[str] = []
    idx = 0
    while idx < len(filtered):
        flag = filtered[idx]
        if not flag.startswith("--"):
            raise PreviewError(f"unexpected positional/unknown value {flag!r}; unknown overrides must be --key value")
        if "=" in flag:
            raw_key, raw_value = flag[2:].split("=", 1)
            idx += 1
        else:
            if idx + 1 >= len(filtered) or filtered[idx + 1].startswith("--"):
                raise PreviewError(f"unknown override {flag!r} is missing a value")
            raw_key = flag[2:]
            raw_value = filtered[idx + 1]
            idx += 2
        # Source TrainingArgs strips '-' from unknown keys before merge. Preserve
        # dots for nested config overrides because they are useful and explicit.
        key = raw_key if "." in raw_key else raw_key.replace("-", "")
        parsed[key] = parse_cli_value(raw_value)
        manual.append(raw_key)
    return parsed, manual


def build_parser() -> argparse.ArgumentParser:
    epilog = """
Examples:
  %(prog)s --max_epochs 1 --lr 1e-5 --format summary
  %(prog)s --optimizer_params weight_decay=0.01,eps=1e-8 --lr_scheduler_params initial_lr=3e-5,niter_decay=1 --format json
  %(prog)s --use_model_config true --lr 2e-5 --eval_strategy no --format yaml

This is a preview only. It never imports ModelScope, downloads models/datasets,
creates work_dir, uploads to Hub, or launches train/eval.
"""
    parser = argparse.ArgumentParser(
        description="Safely preview ModelScope base TrainingArgs-style flags as config.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    parser.add_argument(
        "--format",
        choices=("summary", "json", "yaml"),
        default="summary",
        help="Output format. 'yaml' is a simple YAML-like preview, not a parser guarantee.",
    )
    parser.add_argument(
        "--ignore-default-config",
        choices=("auto", "true", "false"),
        default="auto",
        help="Whether to omit default mapped config values. 'auto' follows use_model_config like ModelScope to_config().",
    )
    for spec in SPECS:
        kwargs: dict[str, Any] = {
            "dest": spec.name,
            "default": argparse.SUPPRESS,
            "type": parse_cli_value,
            "help": f"{spec.help} (default: {spec.default!r})",
        }
        if spec.choices:
            kwargs["choices"] = spec.choices
            # Choices compare after type conversion; these fields are strings.
            kwargs["type"] = str
        parser.add_argument(f"--{spec.name}", **kwargs)
    return parser


def preview(argv: list[str]) -> dict[str, Any]:
    parser = build_parser()
    namespace, unknown = parser.parse_known_args(argv)
    provided = vars(namespace)
    output_format = provided.pop("format")
    ignore_default_option = provided.pop("ignore_default_config")

    values = {spec.name: copy.deepcopy(spec.default) for spec in SPECS}
    manual_args = []
    for name, value in provided.items():
        values[name] = value
        manual_args.append(name)

    unknown_config, unknown_manual = parse_unknown_pairs(unknown)
    manual_args.extend(unknown_manual)

    if ignore_default_option == "auto":
        ignore_default_config = bool(values.get("use_model_config"))
    else:
        ignore_default_config = ignore_default_option == "true"

    config: dict[str, Any] = {}
    extra_args: dict[str, Any] = {}
    for spec in SPECS:
        value = values[spec.name]
        if spec.cfg_node is None:
            extra_args[spec.name] = value
            continue
        include = (spec.name in provided) or not ignore_default_config
        if not include:
            continue
        mapped_value = split_flattened_pairs(value) if spec.flattened else value
        if spec.flattened and not mapped_value:
            continue
        nodes = (spec.cfg_node,) if isinstance(spec.cfg_node, str) else spec.cfg_node
        for node in nodes:
            set_nested(config, node, mapped_value)

    for key, value in unknown_config.items():
        set_nested(config, key, value)

    warnings = make_warnings(values, config, provided, ignore_default_config, unknown_config)
    masked_config = mask_secrets(config)
    masked_extra_args = mask_secrets(extra_args)

    return {
        "schema": "modelscope.training_args_preview.v1",
        "safe_preview": True,
        "format": output_format,
        "manual_args": manual_args,
        "ignore_default_config": ignore_default_config,
        "config": masked_config,
        "extra_args": masked_extra_args,
        "unknown_config_overrides": mask_secrets(unknown_config),
        "warnings": warnings,
    }


def make_warnings(
    values: dict[str, Any],
    config: dict[str, Any],
    provided: dict[str, Any],
    ignore_default_config: bool,
    unknown_config: dict[str, Any],
) -> list[str]:
    warnings: list[str] = [
        "Preview only: no ModelScope import, registry validation, model/dataset download, work_dir creation, Hub upload, training, or evaluation was performed."
    ]
    if ignore_default_config:
        warnings.append("Default mapped config values were omitted; this matches use_model_config-style merge planning.")
    if values.get("model") and isinstance(values["model"], str) and not values["model"].startswith(('.', '/', '~')):
        warnings.append("Model value looks like a model id; real trainer construction may access cache/network and remote-code/plugin trust gates.")
    if values.get("dataset_json_file"):
        warnings.append("dataset_json_file was recorded but not read; validate file schema and column_mapping before a real job.")
    if values.get("eval_strategy") != "no" and not values.get("eval_metrics"):
        warnings.append("Evaluation is not disabled and eval_metrics is unset; real evaluation needs task default metrics or an explicit metric config.")
    if values.get("save_best_checkpoint") and not values.get("metric_for_best_model"):
        warnings.append("Best checkpoint saving is enabled without metric_for_best_model; real jobs need a metric key emitted by evaluation.")
    if values.get("max_checkpoint_num") is not None:
        warnings.append("max_checkpoint_num can delete older periodic checkpoints during real training.")
    if values.get("push_to_hub") or values.get("push_to_hub_best"):
        warnings.append("Hub push is enabled in the preview; real jobs require explicit credential/repository authorization and may upload checkpoints.")
    if values.get("hub_token") or values.get("hub_token_best") or any(SECRET_RE.search(k) for k in unknown_config):
        warnings.append("Secret-like values were masked in output; do not paste real tokens into shared logs.")
    if any(key in unknown_config for key in ("launcher", "train.launcher")) or "launcher" in provided:
        warnings.append("Distributed launch settings require matching torchrun/MPI/Slurm/DeepSpeed environment and GPU verification.")
    train_cfg = config.get("train", {}) if isinstance(config.get("train"), dict) else {}
    hooks = train_cfg.get("hooks")
    if hooks:
        warnings.append("Custom hooks were provided as unknown overrides; check hook type, priority, and optional dependencies before launch.")
    return warnings


def print_summary(result: dict[str, Any]) -> None:
    print("ModelScope TrainingArgs preview (safe; no training/evaluation launched)")
    print("=" * 72)
    print(f"Manual args: {', '.join(result['manual_args']) if result['manual_args'] else '(none)'}")
    print(f"Ignore default mapped config: {result['ignore_default_config']}")
    print("\nEffective config preview:")
    print(yamlish(result["config"]) if result["config"] else "{}")
    print("\nNon-config args preview:")
    print(yamlish(result["extra_args"]) if result["extra_args"] else "{}")
    if result["unknown_config_overrides"]:
        print("\nUnknown config overrides:")
        print(yamlish(result["unknown_config_overrides"]))
    print("\nWarnings / preflight reminders:")
    for warning in result["warnings"]:
        print(f"- {warning}")


def main(argv: list[str] | None = None) -> int:
    try:
        result = preview(sys.argv[1:] if argv is None else argv)
        fmt = result.pop("format")
        if fmt == "json":
            print(json.dumps(result, indent=2, sort_keys=False, ensure_ascii=False))
        elif fmt == "yaml":
            print(yamlish(result))
        else:
            result["format"] = fmt
            print_summary(result)
        return 0
    except PreviewError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
