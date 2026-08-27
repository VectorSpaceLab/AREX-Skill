#!/usr/bin/env python3
"""Validate and summarize a LimiX inference config JSON list.

This script is standalone and intentionally avoids importing LimiX, torch,
sklearn, Hyperopt, or kditransform. It checks the JSON shape and the key
contracts that LimiXPredictor expects when building preprocessing pipelines.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


KNOWN_TOP_LEVEL_KEYS = {
    "RebalanceFeatureDistribution",
    "CategoricalFeatureEncoder",
    "FeatureShuffler",
    "FingerprintFeatureEncoder",
    "PolynomialInteractionGenerator",
    "retrieval_config",
}

DICT_TRANSFORM_KEYS = {
    "RebalanceFeatureDistribution",
    "CategoricalFeatureEncoder",
    "FeatureShuffler",
    "PolynomialInteractionGenerator",
}

ALLOWED_ENCODERS = {
    "ordinal",
    "ordinal_strict_feature_shuffled",
    "ordinal_shuffled",
    "onehot",
    "numeric",
    "none",
    None,
}

ALLOWED_SHUFFLER_MODES = {"shuffle", "rotate", None}

IMPLEMENTED_WORKER_TAGS = {
    None,
    "logNormal",
    "quantile_uniform_10",
    "quantile_uniform_5",
    "quantile_uniform_all_data",
    "power",
    "quantile_norm_10",
    "quantile_norm_5",
    "quantile_norm_all_data",
    "norm_and_kdi",
    "robust",
    "kdi_uni",
    "kdi_norm",
}

SOURCE_EMITS_IDENTITY_WORKER_TAGS = {
    "quantile",
    "none",
    "kdi_alpha_0.3",
    "kdi_alpha_3.0",
    "kdi",
}


def implemented_alpha_worker_tag(tag: str) -> bool:
    if tag.startswith("kdi_uni_alpha_") or tag.startswith("kdi_norm_alpha_"):
        suffix = tag.rsplit("_", maxsplit=1)[-1]
        try:
            float(suffix)
            return True
        except ValueError:
            return False
    return False


def worker_tag_warning(tag: Any) -> str | None:
    if tag in IMPLEMENTED_WORKER_TAGS:
        return None
    if isinstance(tag, str) and implemented_alpha_worker_tag(tag):
        return None
    if tag in SOURCE_EMITS_IDENTITY_WORKER_TAGS:
        return f"source helpers/search spaces can emit {tag!r}, but current preprocessing treats it as an unknown string and falls back to identity"
    return f"unknown tag {tag!r}; current preprocessing falls back to identity for unknown strings"


def describe_retrieval(use_values: list[bool]) -> str:
    if not use_values:
        return "unknown"
    enabled = sum(1 for value in use_values if value)
    if enabled == 0:
        return "none"
    if enabled == len(use_values):
        return "all"
    return f"mixed ({enabled}/{len(use_values)} enabled)"


def require_bool(
    cfg: dict[str, Any],
    key: str,
    path: str,
    errors: list[str],
    *,
    must_be_true: bool = False,
) -> bool | None:
    if key not in cfg:
        errors.append(f"{path}: missing boolean key {key!r}")
        return None
    value = cfg[key]
    if not isinstance(value, bool):
        errors.append(f"{path}.{key}: expected boolean, got {type(value).__name__}")
        return None
    if must_be_true and value is not True:
        errors.append(f"{path}.{key}: must be true for this retrieval mode")
    return value


def validate_rebalance(
    cfg: dict[str, Any],
    path: str,
    errors: list[str],
    warnings: list[str],
) -> None:
    worker_tags = cfg.get("worker_tags")
    if not isinstance(worker_tags, list):
        errors.append(f"{path}.worker_tags: expected a list")
    else:
        for idx, tag in enumerate(worker_tags):
            if tag is not None and not isinstance(tag, str):
                errors.append(f"{path}.worker_tags[{idx}]: expected string or null")
            else:
                warning = worker_tag_warning(tag)
                if warning:
                    warnings.append(f"{path}.worker_tags[{idx}]: {warning}")

    for key in ("discrete_flag", "original_flag"):
        if key in cfg and not isinstance(cfg[key], bool):
            errors.append(f"{path}.{key}: expected boolean")
    if cfg.get("svd_tag") not in ("svd", None):
        warnings.append(f"{path}.svd_tag: expected 'svd' or null, got {cfg.get('svd_tag')!r}")


def validate_categorical(
    cfg: dict[str, Any],
    path: str,
    errors: list[str],
) -> None:
    strategy = cfg.get("encoding_strategy")
    if strategy not in ALLOWED_ENCODERS:
        errors.append(
            f"{path}.encoding_strategy: unsupported value {strategy!r}; expected one of {sorted(str(v) for v in ALLOWED_ENCODERS)}"
        )


def validate_shuffler(
    cfg: dict[str, Any],
    path: str,
    errors: list[str],
) -> None:
    mode = cfg.get("mode", "shuffle")
    if mode not in ALLOWED_SHUFFLER_MODES:
        errors.append(f"{path}.mode: unsupported value {mode!r}; expected 'shuffle', 'rotate', or null")
    if "offset" in cfg and not isinstance(cfg["offset"], int):
        errors.append(f"{path}.offset: expected integer when provided")


def validate_polynomial(
    cfg: dict[str, Any],
    path: str,
    errors: list[str],
) -> None:
    if "max_interaction_features" in cfg:
        value = cfg["max_interaction_features"]
        if value is not None and (not isinstance(value, int) or value <= 0):
            errors.append(f"{path}.max_interaction_features: expected positive integer or null")


def validate_retrieval(
    cfg: Any,
    path: str,
    errors: list[str],
    warnings: list[str],
) -> bool | None:
    if not isinstance(cfg, dict):
        errors.append(f"{path}: expected object")
        return None

    use_retrieval = require_bool(cfg, "use_retrieval", path, errors)
    if use_retrieval is None:
        return None

    if not use_retrieval:
        for key in (
            "retrieval_before_preprocessing",
            "calculate_feature_attention",
            "calculate_sample_attention",
        ):
            if key not in cfg:
                warnings.append(f"{path}: no-retrieval config is missing optional default key {key!r}")
            elif not isinstance(cfg[key], bool):
                errors.append(f"{path}.{key}: expected boolean")
        return False

    retrieval_before = require_bool(cfg, "retrieval_before_preprocessing", path, errors)
    calculate_feature = require_bool(cfg, "calculate_feature_attention", path, errors)
    calculate_sample = require_bool(cfg, "calculate_sample_attention", path, errors)
    if retrieval_before is None or calculate_feature is None or calculate_sample is None:
        return True

    subsample_type = cfg.get("subsample_type")
    if subsample_type not in {"sample", "feature"}:
        errors.append(f"{path}.subsample_type: expected 'sample' or 'feature' when retrieval is enabled")
        return True

    use_type = cfg.get("use_type")
    if use_type not in {"mixed", "only_sample"}:
        errors.append(f"{path}.use_type: expected 'mixed' or 'only_sample' when retrieval is enabled")

    if subsample_type == "sample":
        if calculate_sample is not True:
            errors.append(f"{path}.calculate_sample_attention: sample retrieval requires true")
        if use_type == "mixed" and calculate_feature is not True:
            errors.append(f"{path}.calculate_feature_attention: mixed sample retrieval requires true")
        if "retrieval_len" not in cfg:
            errors.append(f"{path}.retrieval_len: required for sample retrieval")
    elif subsample_type == "feature" and calculate_feature is not True:
        errors.append(f"{path}.calculate_feature_attention: feature retrieval requires true")

    if "retrieval_len" in cfg:
        value = cfg["retrieval_len"]
        if value != "dynamic" and (not isinstance(value, int) or value <= 0):
            errors.append(f"{path}.retrieval_len: expected positive integer or 'dynamic'")

    for numeric_key in ("sub_feature_ratio", "subsample_ratio", "dynamic_ratio", "threshold"):
        if numeric_key in cfg and not isinstance(cfg[numeric_key], (int, float)):
            errors.append(f"{path}.{numeric_key}: expected number")
    if "cluster_num" in cfg and (not isinstance(cfg["cluster_num"], int) or cfg["cluster_num"] <= 0):
        errors.append(f"{path}.cluster_num: expected positive integer")
    if "mixed_method" in cfg and cfg["mixed_method"] not in {"min", "max"}:
        warnings.append(f"{path}.mixed_method: expected 'min' or 'max', got {cfg['mixed_method']!r}")

    return True


def validate_config(data: Any, source: str) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    transform_counts: Counter[str] = Counter()
    retrieval_use: list[bool] = []
    pipeline_summaries: list[dict[str, Any]] = []

    if not isinstance(data, list):
        return {
            "path": source,
            "valid": False,
            "errors": [f"root: expected JSON list, got {type(data).__name__}"],
            "warnings": [],
            "pipeline_count": 0,
            "retrieval_use": "unknown",
            "cpu_compatible": False,
            "transform_counts": {},
            "pipelines": [],
        }

    if len(data) == 0:
        errors.append("root: config list is empty")

    for idx, item in enumerate(data):
        item_path = f"pipeline[{idx}]"
        if not isinstance(item, dict):
            errors.append(f"{item_path}: expected object, got {type(item).__name__}")
            continue

        unknown_keys = sorted(set(item) - KNOWN_TOP_LEVEL_KEYS)
        for key in unknown_keys:
            warnings.append(f"{item_path}.{key}: unknown top-level key; predictor pipeline construction will ignore it")

        present_transforms = [key for key in item if key in KNOWN_TOP_LEVEL_KEYS and key != "retrieval_config"]
        transform_counts.update(present_transforms)

        for key in DICT_TRANSFORM_KEYS:
            if key in item and not isinstance(item[key], dict):
                errors.append(f"{item_path}.{key}: expected object")

        if isinstance(item.get("RebalanceFeatureDistribution"), dict):
            validate_rebalance(item["RebalanceFeatureDistribution"], f"{item_path}.RebalanceFeatureDistribution", errors, warnings)
        if isinstance(item.get("CategoricalFeatureEncoder"), dict):
            validate_categorical(item["CategoricalFeatureEncoder"], f"{item_path}.CategoricalFeatureEncoder", errors)
        if isinstance(item.get("FeatureShuffler"), dict):
            validate_shuffler(item["FeatureShuffler"], f"{item_path}.FeatureShuffler", errors)
        if isinstance(item.get("PolynomialInteractionGenerator"), dict):
            validate_polynomial(item["PolynomialInteractionGenerator"], f"{item_path}.PolynomialInteractionGenerator", errors)

        if "FingerprintFeatureEncoder" in item and not isinstance(item["FingerprintFeatureEncoder"], bool):
            warnings.append(f"{item_path}.FingerprintFeatureEncoder: predictor treats any truthy value as enabled and ignores nested args")

        if "retrieval_config" not in item:
            errors.append(f"{item_path}: missing retrieval_config")
            retrieval_state = None
        else:
            retrieval_state = validate_retrieval(item["retrieval_config"], f"{item_path}.retrieval_config", errors, warnings)
            if retrieval_state is not None:
                retrieval_use.append(retrieval_state)

        pipeline_summaries.append(
            {
                "index": idx,
                "retrieval": retrieval_state,
                "transforms": present_transforms,
                "unknown_top_level_keys": unknown_keys,
            }
        )

    any_retrieval = any(retrieval_use) if retrieval_use else False
    return {
        "path": source,
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "pipeline_count": len(data),
        "retrieval_use": describe_retrieval(retrieval_use),
        "cpu_compatible": bool(data) and not any_retrieval and not errors,
        "transform_counts": dict(sorted(transform_counts.items())),
        "pipelines": pipeline_summaries,
    }


def load_json(path_text: str) -> tuple[Any | None, str | None]:
    try:
        if path_text == "-":
            return json.load(sys.stdin), None
        with Path(path_text).open("r", encoding="utf-8") as handle:
            return json.load(handle), None
    except FileNotFoundError:
        return None, f"file not found: {path_text}"
    except json.JSONDecodeError as exc:
        return None, f"JSON parse error at line {exc.lineno}, column {exc.colno}: {exc.msg}"
    except OSError as exc:
        return None, f"could not read {path_text}: {exc}"


def print_text_report(report: dict[str, Any]) -> None:
    print(f"Config: {report['path']}")
    print(f"Status: {'valid' if report['valid'] else 'INVALID'}")
    print(f"Pipeline count: {report['pipeline_count']}")
    print(f"Retrieval use: {report['retrieval_use']}")
    cpu = "yes" if report["cpu_compatible"] else "no"
    print(f"CPU compatible: {cpu}")

    if report["transform_counts"]:
        print("Transform key counts:")
        for key, count in report["transform_counts"].items():
            print(f"  {key}: {count}")
    else:
        print("Transform key counts: none")

    if report["pipelines"]:
        print("Pipeline summaries:")
        for item in report["pipelines"]:
            transforms = ", ".join(item["transforms"]) if item["transforms"] else "none"
            print(f"  [{item['index']}] retrieval={item['retrieval']} transforms={transforms}")

    if report["warnings"]:
        print("Warnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")

    if report["errors"]:
        print("Errors:", file=sys.stderr)
        for error in report["errors"]:
            print(f"  - {error}", file=sys.stderr)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and summarize a LimiX inference config JSON list.",
    )
    parser.add_argument("config", help="Config JSON path, or '-' to read JSON from stdin.")
    parser.add_argument("--json", action="store_true", help="Emit the report as JSON instead of text.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)

    data, load_error = load_json(args.config)
    if load_error is not None:
        report = {
            "path": args.config,
            "valid": False,
            "errors": [load_error],
            "warnings": [],
            "pipeline_count": 0,
            "retrieval_use": "unknown",
            "cpu_compatible": False,
            "transform_counts": {},
            "pipelines": [],
        }
    else:
        report = validate_config(data, args.config)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)

    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
