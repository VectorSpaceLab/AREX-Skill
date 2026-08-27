#!/usr/bin/env python3
"""Validate an NNI compression config_list JSON file without importing NNI or Torch."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

COMMON_INCLUDE_KEYS = ("op_names", "op_names_re", "op_types")
COMMON_EXCLUDE_KEYS = ("exclude_op_names", "exclude_op_names_re", "exclude_op_types")
COMMON_SELECTOR_KEYS = COMMON_INCLUDE_KEYS + COMMON_EXCLUDE_KEYS
COMMON_KEYS = set(COMMON_SELECTOR_KEYS) | {"target_names", "target_settings", "fuse_names"}
PRUNING_KEYS = {
    "sparse_ratio",
    "sparse_threshold",
    "max_sparse_ratio",
    "min_sparse_ratio",
    "global_group_id",
    "dependency_group_id",
    "internal_metric_block",
    "granularity",
    "apply_method",
    "align",
}
QUANTIZATION_KEYS = {
    "quant_dtype",
    "quant_scheme",
    "granularity",
    "apply_method",
    "fuse_names",
}
DISTILLATION_KEYS = {"lambda", "link", "apply_method"}
ALL_MODE_KEYS = PRUNING_KEYS | QUANTIZATION_KEYS | DISTILLATION_KEYS
PRUNING_INFERENCE_KEYS = PRUNING_KEYS - {"granularity", "apply_method"}
QUANTIZATION_INFERENCE_KEYS = QUANTIZATION_KEYS - {"granularity", "apply_method"}
DISTILLATION_INFERENCE_KEYS = DISTILLATION_KEYS - {"apply_method"}
VALID_GRANULARITY = {"default", "in_channel", "out_channel", "per_channel"}
VALID_PRUNING_APPLY = {"bypass", "mul", "add"}
VALID_QUANTIZATION_APPLY = {"bypass", "clamp_round", "qat_clamp_round"}
VALID_DISTILLATION_APPLY = {"mse", "kl"}
VALID_QUANT_SCHEME = {"affine", "symmetric"}
COMMON_TARGETS = {"_input_", "weight", "bias", "_output_"}
LEGACY_KEYS = {
    "exclude",
    "sparsity",
    "sparsity_per_layer",
    "total_sparsity",
    "max_sparsity_per_layer",
    "op_partial_names",
    "quant_types",
    "quant_bits",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Statically validate an NNI compression config_list JSON file."
    )
    parser.add_argument("config", type=Path, help="Path to a JSON file containing a list of config dictionaries.")
    parser.add_argument(
        "--mode",
        choices=("pruning", "quantization", "distillation", "auto"),
        default="auto",
        help="Validation mode. 'auto' infers modes from keys and applies common checks.",
    )
    parser.add_argument(
        "--allow-legacy",
        action="store_true",
        help="Warn instead of erroring on legacy keys such as exclude, sparsity, quant_types, and quant_bits.",
    )
    parser.add_argument(
        "--allow-empty-selection",
        action="store_true",
        help="Allow a config entry with no op_names, op_names_re, or op_types include selector.",
    )
    parser.add_argument(
        "--strict-targets",
        action="store_true",
        help="Warn when target_names omit common NNI targets such as _input_, weight, bias, or _output_.",
    )
    return parser.parse_args()


def add_error(errors: list[str], index: int | None, message: str) -> None:
    prefix = "config_list" if index is None else f"config[{index}]"
    errors.append(f"{prefix}: {message}")


def add_warning(warnings: list[str], index: int | None, message: str) -> None:
    prefix = "config_list" if index is None else f"config[{index}]"
    warnings.append(f"{prefix}: {message}")


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_string_list(config: dict[str, Any], key: str, index: int, errors: list[str]) -> None:
    if key not in config:
        return
    value = config[key]
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        add_error(errors, index, f"{key} must be a list of strings")


def validate_regex_list(config: dict[str, Any], key: str, index: int, errors: list[str]) -> None:
    validate_string_list(config, key, index, errors)
    if isinstance(config.get(key), list):
        for pattern in config[key]:
            if isinstance(pattern, str):
                try:
                    re.compile(pattern)
                except re.error as exc:
                    add_error(errors, index, f"{key} contains invalid regex {pattern!r}: {exc}")


def validate_ratio(value: Any, key: str, index: int, errors: list[str], *, lower: float, upper: float, lower_closed: bool, upper_closed: bool) -> None:
    if not is_number(value):
        add_error(errors, index, f"{key} must be a number")
        return
    lower_ok = value >= lower if lower_closed else value > lower
    upper_ok = value <= upper if upper_closed else value < upper
    if not (lower_ok and upper_ok):
        left = "[" if lower_closed else "("
        right = "]" if upper_closed else ")"
        add_error(errors, index, f"{key} must be in {left}{lower}, {upper}{right}")


def validate_granularity(value: Any, key: str, index: int, errors: list[str]) -> None:
    if isinstance(value, str):
        if value not in VALID_GRANULARITY:
            add_error(errors, index, f"{key} must be one of {sorted(VALID_GRANULARITY)} or a list of integers")
    elif isinstance(value, list):
        if not value or not all(isinstance(item, int) and not isinstance(item, bool) for item in value):
            add_error(errors, index, f"{key} list granularity must contain integers")
    else:
        add_error(errors, index, f"{key} must be a string or list of integers")


def validate_align(value: Any, index: int, errors: list[str]) -> None:
    if not isinstance(value, dict):
        add_error(errors, index, "align must be a dictionary")
        return
    if "target_name" not in value or not isinstance(value.get("target_name"), str):
        add_error(errors, index, "align.target_name must be a string")
    if "dims" not in value or not isinstance(value.get("dims"), list):
        add_error(errors, index, "align.dims must be a list")
    if "module_name" in value and value["module_name"] is not None and not isinstance(value["module_name"], str):
        add_error(errors, index, "align.module_name must be a string or null")


def validate_fuse_names(value: Any, index: int, errors: list[str]) -> None:
    if not isinstance(value, list):
        add_error(errors, index, "fuse_names must be a list")
        return
    for group in value:
        if isinstance(group, str):
            add_error(errors, index, "fuse_names entries should be lists of module names, not a bare string")
        elif not isinstance(group, list) or not all(isinstance(item, str) for item in group):
            add_error(errors, index, "each fuse_names entry must be a list of strings")


def validate_pruning_setting(setting: dict[str, Any], index: int, errors: list[str], path: str) -> None:
    has_sparse_ratio = "sparse_ratio" in setting
    has_sparse_threshold = "sparse_threshold" in setting
    if has_sparse_ratio:
        validate_ratio(setting["sparse_ratio"], f"{path}.sparse_ratio", index, errors, lower=0, upper=1, lower_closed=True, upper_closed=True)
    if has_sparse_threshold and not is_number(setting["sparse_threshold"]):
        add_error(errors, index, f"{path}.sparse_threshold must be a number")
    if has_sparse_ratio and has_sparse_threshold:
        add_error(errors, index, f"{path} should not set both sparse_ratio and sparse_threshold")
    if "max_sparse_ratio" in setting:
        validate_ratio(setting["max_sparse_ratio"], f"{path}.max_sparse_ratio", index, errors, lower=0, upper=1, lower_closed=False, upper_closed=True)
    if "min_sparse_ratio" in setting:
        validate_ratio(setting["min_sparse_ratio"], f"{path}.min_sparse_ratio", index, errors, lower=0, upper=1, lower_closed=True, upper_closed=False)
    if "min_sparse_ratio" in setting and "max_sparse_ratio" in setting:
        min_value = setting["min_sparse_ratio"]
        max_value = setting["max_sparse_ratio"]
        if is_number(min_value) and is_number(max_value) and min_value > max_value:
            add_error(errors, index, f"{path}.min_sparse_ratio must be <= max_sparse_ratio")
    for group_key in ("global_group_id", "dependency_group_id"):
        if group_key in setting and not isinstance(setting[group_key], (int, str)):
            add_error(errors, index, f"{path}.{group_key} must be a string or integer")
    if "internal_metric_block" in setting and not isinstance(setting["internal_metric_block"], int):
        add_error(errors, index, f"{path}.internal_metric_block must be an integer")
    if "granularity" in setting:
        validate_granularity(setting["granularity"], f"{path}.granularity", index, errors)
    if "apply_method" in setting and setting["apply_method"] not in VALID_PRUNING_APPLY:
        add_error(errors, index, f"{path}.apply_method must be one of {sorted(VALID_PRUNING_APPLY)}")
    if "align" in setting:
        validate_align(setting["align"], index, errors)


def validate_quantization_setting(setting: dict[str, Any], index: int, errors: list[str], path: str) -> None:
    if "quant_dtype" in setting and setting["quant_dtype"] is not None and not isinstance(setting["quant_dtype"], str):
        add_error(errors, index, f"{path}.quant_dtype must be a string or null")
    if "quant_scheme" in setting and setting["quant_scheme"] not in VALID_QUANT_SCHEME:
        add_error(errors, index, f"{path}.quant_scheme must be one of {sorted(VALID_QUANT_SCHEME)}")
    if "granularity" in setting:
        validate_granularity(setting["granularity"], f"{path}.granularity", index, errors)
    if "apply_method" in setting and setting["apply_method"] not in VALID_QUANTIZATION_APPLY:
        add_error(errors, index, f"{path}.apply_method must be one of {sorted(VALID_QUANTIZATION_APPLY)}")
    if "fuse_names" in setting:
        validate_fuse_names(setting["fuse_names"], index, errors)


def validate_distillation_setting(setting: dict[str, Any], index: int, errors: list[str], path: str) -> None:
    if "lambda" in setting and not is_number(setting["lambda"]):
        add_error(errors, index, f"{path}.lambda must be a number")
    if "link" in setting:
        link = setting["link"]
        if not isinstance(link, str) and not (isinstance(link, list) and all(isinstance(item, str) for item in link)):
            add_error(errors, index, f"{path}.link must be a string or list of strings")
    if "apply_method" in setting and setting["apply_method"] not in VALID_DISTILLATION_APPLY:
        add_error(errors, index, f"{path}.apply_method must be one of {sorted(VALID_DISTILLATION_APPLY)}")


def infer_modes(config: dict[str, Any], requested_mode: str) -> list[str]:
    if requested_mode != "auto":
        return [requested_mode]
    modes: list[str] = []
    keys = set(config)
    if keys & PRUNING_INFERENCE_KEYS:
        modes.append("pruning")
    if keys & QUANTIZATION_INFERENCE_KEYS:
        modes.append("quantization")
    if keys & DISTILLATION_INFERENCE_KEYS:
        modes.append("distillation")
    target_settings = config.get("target_settings")
    if isinstance(target_settings, dict):
        for setting in target_settings.values():
            if isinstance(setting, dict):
                setting_keys = set(setting)
                if setting_keys & PRUNING_INFERENCE_KEYS and "pruning" not in modes:
                    modes.append("pruning")
                if setting_keys & QUANTIZATION_INFERENCE_KEYS and "quantization" not in modes:
                    modes.append("quantization")
                if setting_keys & DISTILLATION_INFERENCE_KEYS and "distillation" not in modes:
                    modes.append("distillation")
    return modes


def validate_config(config: dict[str, Any], index: int, args: argparse.Namespace, warnings: list[str], errors: list[str]) -> None:
    for key in COMMON_SELECTOR_KEYS:
        validate_regex_list(config, key, index, errors) if key.endswith("_re") else validate_string_list(config, key, index, errors)

    if not args.allow_empty_selection and not any(config.get(key) for key in COMMON_INCLUDE_KEYS):
        add_error(errors, index, "must include at least one non-empty selector: op_names, op_names_re, or op_types")

    if "exclude" in config:
        message = "legacy boolean exclude is ambiguous; use exclude_op_names, exclude_op_names_re, or exclude_op_types"
        add_warning(warnings, index, message) if args.allow_legacy else add_error(errors, index, message)

    legacy_seen = sorted(key for key in LEGACY_KEYS - {"exclude"} if key in config)
    if legacy_seen:
        message = f"legacy keys found {legacy_seen}; prefer current target_names/target_settings and sparse_ratio fields"
        add_warning(warnings, index, message) if args.allow_legacy else add_error(errors, index, message)

    if "op_names" in config and "exclude_op_names" in config:
        repeated = sorted(set(config.get("op_names", [])) & set(config.get("exclude_op_names", [])))
        if repeated:
            add_error(errors, index, f"module names appear in both op_names and exclude_op_names: {repeated}")

    if "op_types" in config and "exclude_op_types" in config:
        repeated = sorted(set(config.get("op_types", [])) & set(config.get("exclude_op_types", [])))
        if repeated:
            add_error(errors, index, f"module types appear in both op_types and exclude_op_types: {repeated}")

    if "target_names" in config:
        validate_string_list(config, "target_names", index, errors)
        if args.strict_targets:
            unusual = [target for target in config.get("target_names", []) if isinstance(target, str) and not (target in COMMON_TARGETS or target.startswith("_input_") or target.startswith("_output_"))]
            if unusual:
                add_warning(warnings, index, f"target_names contain non-common targets: {unusual}")

    target_settings = config.get("target_settings")
    if target_settings is not None and not isinstance(target_settings, dict):
        add_error(errors, index, "target_settings must be a dictionary keyed by target name")
        target_settings = None

    modes = infer_modes(config, args.mode)
    if args.mode == "auto" and not modes:
        add_warning(warnings, index, "could not infer pruning, quantization, or distillation from mode-specific keys; pass --mode for stricter validation")
    top_level_setting = {key: value for key, value in config.items() if key in ALL_MODE_KEYS}

    unknown_keys = sorted(set(config) - COMMON_KEYS - ALL_MODE_KEYS - LEGACY_KEYS)
    if unknown_keys:
        add_warning(warnings, index, f"unrecognized keys will be passed through to NNI as target-setting shortcuts or custom settings: {unknown_keys}")

    for mode in modes:
        if mode == "pruning":
            validate_pruning_setting(top_level_setting, index, errors, "top-level")
        elif mode == "quantization":
            validate_quantization_setting(top_level_setting, index, errors, "top-level")
            if not target_settings and "target_names" not in config:
                add_warning(warnings, index, "quantization config usually needs target_names such as _input_, weight, or _output_")
        elif mode == "distillation":
            validate_distillation_setting(top_level_setting, index, errors, "top-level")

    if isinstance(target_settings, dict):
        for target_name, setting in target_settings.items():
            if not isinstance(target_name, str):
                add_error(errors, index, "target_settings keys must be strings")
                continue
            if not isinstance(setting, dict):
                add_error(errors, index, f"target_settings[{target_name!r}] must be a dictionary")
                continue
            for mode in modes:
                path = f"target_settings[{target_name!r}]"
                if mode == "pruning":
                    validate_pruning_setting(setting, index, errors, path)
                elif mode == "quantization":
                    validate_quantization_setting(setting, index, errors, path)
                elif mode == "distillation":
                    validate_distillation_setting(setting, index, errors, path)


def load_config(path: Path) -> tuple[Any | None, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except FileNotFoundError:
        return None, [f"config_list: file not found: {path}"]
    except json.JSONDecodeError as exc:
        return None, [f"config_list: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"]
    except OSError as exc:
        return None, [f"config_list: could not read {path}: {exc}"]


def main() -> int:
    args = parse_args()
    config_list, errors = load_config(args.config)
    warnings: list[str] = []
    if errors:
        print("NNI config_list validation failed", file=sys.stderr)
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if not isinstance(config_list, list):
        add_error(errors, None, "top-level JSON value must be a list")
    elif not config_list:
        add_error(errors, None, "must contain at least one config dictionary")
    else:
        for index, config in enumerate(config_list):
            if not isinstance(config, dict):
                add_error(errors, index, "must be a dictionary")
                continue
            validate_config(config, index, args, warnings, errors)

    if warnings:
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)

    if errors:
        print("NNI config_list validation failed", file=sys.stderr)
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {args.config} is a valid NNI compression config_list for mode={args.mode}")
    if warnings:
        print(f"OK with {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
