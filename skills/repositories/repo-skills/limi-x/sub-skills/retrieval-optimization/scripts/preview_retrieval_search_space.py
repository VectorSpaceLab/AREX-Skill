#!/usr/bin/env python3
"""Preview and validate the LimiX retrieval search space safely.

This helper is intentionally model-free:
- no LimiXPredictor import
- no Optuna import
- no checkpoint loading

Use it to inspect the retrieval parameter ranges, confirm config keys, and
check whether a local retrieval config is internally consistent before tuning.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROFILE_SUMMARIES: dict[str, dict[str, Any]] = {
    "cls-16m": {
        "task": "classification",
        "profile_type": "sample-retrieval",
        "defaults": {
            "calculate_sample_attention": True,
            "calculate_feature_attention": False,
            "retrieval_len": 389,
            "use_cluster": True,
            "cluster_num": 22,
            "use_threshold": False,
            "use_dynamic": False,
            "threshold": 0.85,
            "dynamic_ratio": 0.4,
            "mixed_method": "min",
            "sub_feature_ratio": 1,
            "subsample_type": "sample",
            "use_type": "only_sample",
        },
    },
    "cls-2m": {
        "task": "classification",
        "profile_type": "sample-retrieval",
        "defaults": {
            "calculate_sample_attention": True,
            "calculate_feature_attention": False,
            "retrieval_len": "dynamic",
            "use_cluster": True,
            "cluster_num": 47,
            "use_threshold": True,
            "use_dynamic": True,
            "threshold": 0.95,
            "dynamic_ratio": 0.5,
            "mixed_method": "max",
            "sub_feature_ratio": 1,
            "subsample_type": "sample",
            "use_type": "only_sample",
        },
    },
    "reg-16m": {
        "task": "regression",
        "profile_type": "sample-retrieval",
        "defaults": {
            "calculate_sample_attention": True,
            "calculate_feature_attention": False,
            "retrieval_len": "dynamic",
            "use_cluster": True,
            "cluster_num": 45,
            "use_threshold": False,
            "use_dynamic": True,
            "threshold": 0.85,
            "dynamic_ratio": 0.35,
            "mixed_method": "max",
            "sub_feature_ratio": 1,
            "subsample_type": "sample",
            "use_type": "only_sample",
        },
    },
    "reg-2m": {
        "task": "regression",
        "profile_type": "sample-retrieval",
        "defaults": {
            "calculate_sample_attention": True,
            "calculate_feature_attention": False,
            "retrieval_len": "dynamic",
            "use_cluster": True,
            "cluster_num": 50,
            "use_threshold": True,
            "use_dynamic": True,
            "threshold": 0.67,
            "dynamic_ratio": 0.45,
            "mixed_method": "max",
            "sub_feature_ratio": 1,
            "subsample_type": "sample",
            "use_type": "only_sample",
        },
    },
}

SEARCH_SPACE_SPEC: dict[str, dict[str, Any]] = {
    "use_cluster": {
        "kind": "categorical",
        "values": [True, False],
        "lock_semantics": "truthy override locks; falsey override stays searchable",
    },
    "cluster_num": {
        "kind": "int",
        "default_min": 10,
        "default_max": 50,
        "conditional_on": "use_cluster",
    },
    "use_threshold": {
        "kind": "categorical",
        "values": [False, True],
        "lock_semantics": "truthy override locks; falsey override stays searchable",
    },
    "threshold": {
        "kind": "float",
        "default_min": 0.5,
        "default_max": 1.0,
        "conditional_on": "use_threshold",
    },
    "use_dynamic": {
        "kind": "categorical",
        "values": [False, True],
        "lock_semantics": "truthy override locks; falsey override stays searchable",
    },
    "sample_ratio": {
        "kind": "int",
        "default_min": 200,
        "default_max": 500,
        "conditional_on": "not use_dynamic",
    },
    "dynamic_ratio": {
        "kind": "float",
        "default_min": 0.1,
        "default_max": 0.5,
        "conditional_on": "use_dynamic",
    },
    "mixed_method": {
        "kind": "categorical",
        "values": ["max", "min"],
    },
    "sub_feature_ratio": {
        "kind": "fixed",
        "value": 1,
    },
}

RETURNED_UPDATE_KEYS = [
    "use_cluster",
    "cluster_num",
    "threshold",
    "retrieval_len",
    "dynamic_ratio",
    "mixed_method",
    "sub_feature_ratio",
]

CONFIG_REQUIRED_KEYS = [
    "use_retrieval",
    "retrieval_before_preprocessing",
    "calculate_feature_attention",
    "calculate_sample_attention",
    "retrieval_len",
    "subsample_type",
    "use_type",
]

CONFIG_RETRIEVAL_KEYS = [
    "use_retrieval",
    "retrieval_before_preprocessing",
    "calculate_feature_attention",
    "calculate_sample_attention",
    "retrieval_len",
    "subsample_type",
    "use_type",
    "use_cluster",
    "cluster_num",
    "use_threshold",
    "threshold",
    "use_dynamic",
    "dynamic_ratio",
    "mixed_method",
    "sub_feature_ratio",
    "sample_ratio",
]


def _load_json_source(value: str) -> Any:
    if value.startswith("@"):
        path = Path(value[1:])
        return json.loads(path.read_text())

    path = Path(value)
    if path.is_file():
        return json.loads(path.read_text())

    return json.loads(value)


def _truthy(value: Any) -> bool:
    return bool(value)


def _is_numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def resolve_search_space(overrides: dict[str, Any] | None) -> dict[str, Any]:
    overrides = overrides or {}
    resolved: dict[str, Any] = {}
    notes: list[str] = []

    def lock_or_range(name: str, default_range: tuple[Any, Any] | None = None, choices: list[Any] | None = None,
                      conditional_on: str | None = None, fixed_value: Any | None = None,
                      falsey_lock_is_ignored: bool = False) -> dict[str, Any]:
        override = overrides.get(name, None)
        item: dict[str, Any] = {"name": name}

        if fixed_value is not None:
            item["kind"] = "fixed"
            item["value"] = fixed_value
            if override is not None and override != fixed_value:
                item["override_note"] = f"override ignored; fixed at {fixed_value}"
            return item

        if choices is not None:
            item["kind"] = "categorical"
            item["choices"] = choices
            if override is not None:
                if _truthy(override):
                    item["locked"] = True
                    item["value"] = override
                else:
                    item["locked"] = False
                    item["searchable"] = True
                    item["values"] = choices
                    if falsey_lock_is_ignored:
                        item["override_note"] = "falsey override does not lock this flag in the source behavior"
            else:
                item["locked"] = False
                item["searchable"] = True
                item["values"] = choices
            return item

        low, high = default_range if default_range is not None else (None, None)
        item["kind"] = "range"
        item["min"] = low
        item["max"] = high
        if override is not None and _truthy(override):
            item["locked"] = True
            item["value"] = override
        else:
            item["locked"] = False
            item["searchable"] = True
            if conditional_on is not None:
                item["conditional_on"] = conditional_on
            if override is not None and not _truthy(override):
                item["override_note"] = "falsey override does not lock this value in the source behavior"
        return item

    resolved["use_cluster"] = lock_or_range(
        "use_cluster",
        choices=[True, False],
        falsey_lock_is_ignored=True,
    )
    resolved["cluster_num"] = lock_or_range(
        "cluster_num",
        default_range=(int(overrides.get("cluster_num_min", 10)), int(overrides.get("cluster_num_max", 50))),
        conditional_on="use_cluster",
    )
    resolved["use_threshold"] = lock_or_range(
        "use_threshold",
        choices=[False, True],
        falsey_lock_is_ignored=True,
    )
    resolved["threshold"] = lock_or_range(
        "threshold",
        default_range=(float(overrides.get("threshold_min", 0.5)), float(overrides.get("threshold_max", 1.0))),
        conditional_on="use_threshold",
    )
    resolved["use_dynamic"] = lock_or_range(
        "use_dynamic",
        choices=[False, True],
        falsey_lock_is_ignored=True,
    )

    if _truthy(overrides.get("use_dynamic", False)):
        resolved["retrieval_len"] = {"name": "retrieval_len", "kind": "fixed", "value": "dynamic"}
        resolved["dynamic_ratio"] = lock_or_range(
            "dynamic_ratio",
            default_range=(float(overrides.get("dynamic_ratio_min", 0.1)), float(overrides.get("dynamic_ratio_max", 0.5))),
            conditional_on="use_dynamic",
        )
        if overrides.get("sample_ratio") is not None:
            notes.append("sample_ratio is ignored when use_dynamic is true")
    else:
        if overrides.get("sample_ratio") is not None and _truthy(overrides.get("sample_ratio")):
            resolved["retrieval_len"] = {"name": "retrieval_len", "kind": "fixed", "value": overrides.get("sample_ratio")}
        else:
            resolved["retrieval_len"] = {
                "name": "retrieval_len",
                "kind": "range",
                "min": int(overrides.get("sample_ratio_min", 200)),
                "max": int(overrides.get("sample_ratio_max", 500)),
                "conditional_on": "not use_dynamic",
                "searchable": True,
            }
        resolved["dynamic_ratio"] = {
            "name": "dynamic_ratio",
            "kind": "inactive",
            "value": None,
            "note": "dynamic_ratio is unused when use_dynamic is false",
        }

    resolved["mixed_method"] = lock_or_range(
        "mixed_method",
        choices=["max", "min"],
    )
    resolved["sub_feature_ratio"] = lock_or_range("sub_feature_ratio", fixed_value=1)

    return {
        "overrides": overrides,
        "search_space": resolved,
        "returned_update_keys": RETURNED_UPDATE_KEYS,
        "notes": notes,
    }


def validate_config(config_obj: Any) -> dict[str, Any]:
    if isinstance(config_obj, dict):
        config_list = [config_obj]
    elif isinstance(config_obj, list):
        config_list = config_obj
    else:
        return {
            "ok": False,
            "errors": ["config must be a JSON object or a list of pipeline objects"],
            "warnings": [],
        }

    errors: list[str] = []
    warnings: list[str] = []
    pipeline_summaries: list[dict[str, Any]] = []
    retrieval_enabled_count = 0

    for idx, item in enumerate(config_list):
        if not isinstance(item, dict):
            errors.append(f"pipeline {idx}: expected an object")
            continue

        rc = item.get("retrieval_config")
        if not isinstance(rc, dict):
            errors.append(f"pipeline {idx}: missing retrieval_config object")
            continue

        missing = [key for key in CONFIG_REQUIRED_KEYS if key not in rc]
        if missing:
            errors.append(f"pipeline {idx}: missing keys {missing}")

        if rc.get("use_retrieval", False):
            retrieval_enabled_count += 1
        else:
            warnings.append(f"pipeline {idx}: use_retrieval is false; this is not a retrieval run")

        if rc.get("subsample_type") == "sample" and not rc.get("calculate_sample_attention", False):
            errors.append(f"pipeline {idx}: sample retrieval requires calculate_sample_attention=true")

        if rc.get("subsample_type") == "feature" and not rc.get("calculate_feature_attention", False):
            errors.append(f"pipeline {idx}: feature retrieval requires calculate_feature_attention=true")

        if rc.get("use_type") == "mixed" and not rc.get("calculate_feature_attention", False):
            errors.append(f"pipeline {idx}: mixed retrieval requires calculate_feature_attention=true")

        if rc.get("use_threshold", False) and rc.get("threshold") is None:
            errors.append(f"pipeline {idx}: use_threshold=true but threshold is missing")

        if rc.get("use_dynamic", False) and rc.get("dynamic_ratio") is None:
            errors.append(f"pipeline {idx}: use_dynamic=true but dynamic_ratio is missing")

        if rc.get("use_cluster", False) and rc.get("cluster_num") is None:
            errors.append(f"pipeline {idx}: use_cluster=true but cluster_num is missing")

        threshold = rc.get("threshold")
        if threshold is not None and _is_numeric(threshold) and not (0 <= float(threshold) <= 1):
            errors.append(f"pipeline {idx}: threshold must be within [0, 1]")

        dynamic_ratio = rc.get("dynamic_ratio")
        if dynamic_ratio is not None and _is_numeric(dynamic_ratio) and float(dynamic_ratio) <= 0:
            errors.append(f"pipeline {idx}: dynamic_ratio should be positive")

        mixed_method = rc.get("mixed_method")
        if mixed_method is not None and mixed_method not in {"max", "min"}:
            errors.append(f"pipeline {idx}: mixed_method must be 'max' or 'min'")

        if "sample_ratio" in rc and rc.get("retrieval_len") is not None and rc["sample_ratio"] != rc["retrieval_len"]:
            warnings.append(
                f"pipeline {idx}: sample_ratio and retrieval_len differ; search uses retrieval_len as the effective field"
            )

        if rc.get("retrieval_len") == "dynamic" and not rc.get("use_dynamic", False):
            warnings.append(f"pipeline {idx}: retrieval_len is dynamic but use_dynamic is false")

        if rc.get("use_dynamic", False) and rc.get("retrieval_len") != "dynamic":
            warnings.append(f"pipeline {idx}: use_dynamic is true but retrieval_len is not 'dynamic'")

        pipeline_summaries.append(
            {
                "pipeline_index": idx,
                "use_retrieval": rc.get("use_retrieval", False),
                "subsample_type": rc.get("subsample_type"),
                "use_type": rc.get("use_type"),
                "use_cluster": rc.get("use_cluster"),
                "use_threshold": rc.get("use_threshold"),
                "use_dynamic": rc.get("use_dynamic"),
                "retrieval_len": rc.get("retrieval_len"),
            }
        )

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "pipeline_count": len(config_list),
        "retrieval_enabled_pipelines": retrieval_enabled_count,
        "pipelines": pipeline_summaries,
    }


def build_output(args: argparse.Namespace) -> dict[str, Any]:
    profile_payload = None
    if args.profile != "none":
        if args.profile == "all":
            profile_payload = PROFILE_SUMMARIES
        else:
            profile_payload = {args.profile: PROFILE_SUMMARIES[args.profile]}

    overrides = None
    if args.args_json:
        overrides = _load_json_source(args.args_json)
        if not isinstance(overrides, dict):
            raise SystemExit("--args-json must resolve to a JSON object")

    search_space_payload = resolve_search_space(overrides)
    validation_payload = None
    if args.config:
        config_obj = _load_json_source(args.config)
        validation_payload = validate_config(config_obj)

    output = {
        "safe": True,
        "runs_inference": False,
        "profile": args.profile,
        "profile_summaries": profile_payload,
        "search_space_spec": SEARCH_SPACE_SPEC,
        "resolved_search_space": search_space_payload["search_space"],
        "search_overrides": search_space_payload["overrides"],
        "returned_update_keys": search_space_payload["returned_update_keys"],
        "notes": search_space_payload["notes"],
        "config_validation": validation_payload,
        "retrieval_config_keys": CONFIG_RETRIEVAL_KEYS,
        "required_config_keys": CONFIG_REQUIRED_KEYS,
    }
    return output


def format_text(output: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("LimiX retrieval search-space preview")
    lines.append(f"safe: {output['safe']}")
    lines.append(f"runs_inference: {output['runs_inference']}")
    lines.append("")

    if output.get("profile_summaries"):
        lines.append("Profiles:")
        profile_summaries = output["profile_summaries"]
        if isinstance(profile_summaries, dict) and "defaults" in profile_summaries:
            profile_summaries = {output["profile"]: profile_summaries}
        for name, summary in profile_summaries.items():
            lines.append(f"- {name}: {summary['task']} / {summary['profile_type']}")
            for key, value in summary["defaults"].items():
                lines.append(f"  - {key}: {value}")
    lines.append("")

    lines.append("Search space:")
    for name, spec in output["resolved_search_space"].items():
        lines.append(f"- {name}: {spec}")
    if output.get("notes"):
        lines.append("")
        lines.append("Notes:")
        for note in output["notes"]:
            lines.append(f"- {note}")

    if output.get("config_validation"):
        lines.append("")
        lines.append("Config validation:")
        validation = output["config_validation"]
        lines.append(f"- ok: {validation['ok']}")
        lines.append(f"- pipeline_count: {validation.get('pipeline_count')}")
        lines.append(f"- retrieval_enabled_pipelines: {validation.get('retrieval_enabled_pipelines')}")
        if validation.get("errors"):
            lines.append("- errors:")
            for err in validation["errors"]:
                lines.append(f"  - {err}")
        if validation.get("warnings"):
            lines.append("- warnings:")
            for warn in validation["warnings"]:
                lines.append(f"  - {warn}")

    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview and validate the LimiX retrieval search space without loading a checkpoint.",
    )
    parser.add_argument(
        "--profile",
        choices=["none", "cls-16m", "cls-2m", "reg-16m", "reg-2m", "all"],
        default="none",
        help="Optional distilled retrieval profile to display.",
    )
    parser.add_argument(
        "--args-json",
        default=None,
        help="JSON object or @path with search-space overrides that mirror the Optuna helper inputs.",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Optional JSON config file or JSON string to validate.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of text.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when config validation returns warnings or errors.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    output = build_output(args)

    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(format_text(output))

    validation = output.get("config_validation")
    if args.strict and validation:
        if validation.get("errors") or validation.get("warnings"):
            return 2
    elif args.strict and output.get("notes"):
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
