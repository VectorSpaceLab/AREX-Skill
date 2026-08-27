#!/usr/bin/env python3
"""Safe static checker for lm-evaluation-harness task YAML files.

This script parses YAML, resolves local includes, and checks common task-authoring
mistakes without importing !function code or downloading datasets.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised only when PyYAML is absent
    yaml = None

REGISTERED_FILTERS = {
    "custom",
    "format_span",
    "lowercase",
    "majority_vote",
    "map",
    "multi_choice_regex",
    "regex",
    "regex_pos",
    "remove_whitespace",
    "take_first",
    "take_first_k",
    "uppercase",
}

REGISTERED_METRICS = {
    "acc",
    "acc_all",
    "acc_bytes",
    "acc_mutual_info",
    "acc_norm",
    "bypass",
    "bleu",
    "brier_score",
    "byte_perplexity",
    "bits_per_byte",
    "chrf",
    "exact_match",
    "f1",
    "likelihood",
    "mcc",
    "perplexity",
    "ter",
    "word_perplexity",
}

REGISTERED_AGGREGATIONS = {
    "bypass",
    "bleu",
    "brier_score",
    "bits_per_byte",
    "chrf",
    "f1",
    "matthews_corrcoef",
    "mean",
    "median",
    "perplexity",
    "ter",
    "weighted_perplexity",
}

OUTPUT_TYPES = {
    "generate_until",
    "loglikelihood",
    "loglikelihood_rolling",
    "multiple_choice",
}

FUNCTION_FIELDS = {
    "class",
    "custom_dataset",
    "doc_to_audio",
    "doc_to_choice",
    "doc_to_decontamination_query",
    "doc_to_image",
    "doc_to_target",
    "doc_to_text",
    "process_docs",
    "process_results",
}

WARNING_PATTERNS = (
    ("\\\\n", "contains literal \\\\n; ensure this is intentional and not a quoted newline mistake"),
)


class FunctionRef(str):
    """Marker for a !function reference that has not been imported."""


if yaml is not None:
    class LintLoader(yaml.SafeLoader):
        pass

    def function_constructor(loader: Any, node: Any) -> FunctionRef:
        return FunctionRef(loader.construct_scalar(node))

    LintLoader.add_constructor("!function", function_constructor)
else:
    LintLoader = None


def parse_yaml_text(text: str) -> Any:
    if yaml is not None:
        return yaml.load(text, Loader=LintLoader)  # noqa: S506 - custom safe loader

    from ruamel.yaml import YAML

    ruamel_yaml = YAML(typ="safe")
    ruamel_yaml.constructor.add_constructor(
        "!function",
        lambda constructor, node: FunctionRef(constructor.construct_scalar(node)),
    )
    return ruamel_yaml.load(text)


def load_yaml(path: Path, seen: set[Path] | None = None) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if seen is None:
        seen = set()
    if path in seen:
        raise ValueError(f"include cycle detected at {path}")
    seen.add(path)
    data = parse_yaml_text(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected mapping at top level, got {type(data).__name__}")
    includes = data.pop("include", None)
    if not includes:
        return data
    merged: dict[str, Any] = {}
    for include in includes if isinstance(includes, list) else [includes]:
        include_path = Path(str(include))
        if not include_path.is_absolute():
            include_path = path.parent / include_path
        if not include_path.exists():
            raise FileNotFoundError(f"missing include {include!r} resolved to {include_path}")
        include_data = load_yaml(include_path, seen)
        include_data.pop("task_list", None)
        merged.update(include_data)
    merged.update(data)
    return merged


def walk_values(value: Any):
    if isinstance(value, dict):
        for child in value.values():
            yield from walk_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_values(child)
    else:
        yield value


def dotted_function_exists(base_dir: Path, ref: str) -> bool:
    module_name, dot, function_name = ref.rpartition(".")
    if not dot or not module_name or not function_name:
        return False
    local_file = base_dir / f"{module_name.replace('.', '/')}.py"
    if local_file.exists():
        try:
            text = local_file.read_text(encoding="utf-8")
        except OSError:
            return False
        return re.search(rf"^\s*(def|class)\s+{re.escape(function_name)}\b", text, re.MULTILINE) is not None
    return True


def validate_function_refs(path: Path, cfg: dict[str, Any], warnings: list[str], errors: list[str]) -> None:
    base_dir = path.expanduser().resolve().parent

    def check_ref(ref: FunctionRef, location: str) -> None:
        if not dotted_function_exists(base_dir, str(ref)):
            errors.append(f"{location}: !function {ref!s} does not resolve to a local def/class or importable dotted path shape")

    for field in FUNCTION_FIELDS:
        value = cfg.get(field)
        if isinstance(value, FunctionRef):
            check_ref(value, field)
            if field in {"class", "custom_dataset", "process_results"}:
                warnings.append(f"{field}: runtime validation will execute task-local Python")
    for index, metric in enumerate(cfg.get("metric_list") or []):
        if isinstance(metric, dict):
            for key in ("metric", "aggregation"):
                value = metric.get(key)
                if isinstance(value, FunctionRef):
                    check_ref(value, f"metric_list[{index}].{key}")
                    warnings.append(f"metric_list[{index}].{key}: custom function executes Python at runtime")


def validate_filters(cfg: dict[str, Any], warnings: list[str], errors: list[str]) -> None:
    filter_list = cfg.get("filter_list")
    if not filter_list:
        return
    if isinstance(filter_list, str):
        return
    if not isinstance(filter_list, list):
        errors.append("filter_list must be a string or list")
        return
    names = set()
    for pipeline_index, pipeline in enumerate(filter_list):
        if not isinstance(pipeline, dict):
            errors.append(f"filter_list[{pipeline_index}] must be a mapping")
            continue
        name = pipeline.get("name")
        if not name:
            errors.append(f"filter_list[{pipeline_index}] missing name")
        elif name in names:
            errors.append(f"duplicate filter pipeline name: {name}")
        names.add(name)
        steps = pipeline.get("filter")
        if not isinstance(steps, list) or not steps:
            errors.append(f"filter_list[{pipeline_index}].filter must be a non-empty list")
            continue
        previous_function = None
        for step_index, step in enumerate(steps):
            if not isinstance(step, dict):
                errors.append(f"filter_list[{pipeline_index}].filter[{step_index}] must be a mapping")
                continue
            function = step.get("function")
            if function not in REGISTERED_FILTERS:
                errors.append(f"unknown filter function {function!r} at filter_list[{pipeline_index}].filter[{step_index}]")
            if function == "take_first_k" and "k" not in step:
                errors.append(f"take_first_k at filter_list[{pipeline_index}].filter[{step_index}] requires k")
            if previous_function == "majority_vote" and function != "take_first":
                warnings.append("majority_vote returns a one-item list; usually follow it with take_first")
            previous_function = function


def validate_metrics(cfg: dict[str, Any], errors: list[str]) -> None:
    metrics = cfg.get("metric_list")
    if metrics is None:
        return
    if not isinstance(metrics, list):
        errors.append("metric_list must be a list")
        return
    for index, entry in enumerate(metrics):
        if not isinstance(entry, dict):
            errors.append(f"metric_list[{index}] must be a mapping")
            continue
        metric = entry.get("metric")
        if not isinstance(metric, FunctionRef) and metric not in REGISTERED_METRICS:
            errors.append(f"unknown metric {metric!r} at metric_list[{index}]")
        aggregation = entry.get("aggregation")
        if aggregation is not None and not isinstance(aggregation, FunctionRef) and aggregation not in REGISTERED_AGGREGATIONS:
            errors.append(f"unknown aggregation {aggregation!r} at metric_list[{index}]")
        if isinstance(metric, FunctionRef) and ("aggregation" not in entry or "higher_is_better" not in entry):
            errors.append(f"custom metric at metric_list[{index}] should define aggregation and higher_is_better")


def validate_task_shape(cfg: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    is_group = "group" in cfg
    is_task = "task" in cfg
    if not is_group and not is_task:
        errors.append("config must define task or group")
    if is_group:
        if not isinstance(cfg.get("task"), (list, str)):
            errors.append("group config must define task as a string or list")
        return
    if "dataset_path" not in cfg and "custom_dataset" not in cfg and "class" not in cfg:
        errors.append("task config should define dataset_path, custom_dataset, or class")
    output_type = cfg.get("output_type", "generate_until")
    if output_type not in OUTPUT_TYPES:
        errors.append(f"unknown output_type {output_type!r}")
    if output_type == "multiple_choice":
        if "doc_to_choice" not in cfg:
            errors.append("multiple_choice tasks require doc_to_choice")
        if "doc_to_target" not in cfg:
            errors.append("multiple_choice tasks require doc_to_target")
    if output_type == "generate_until" and "generation_kwargs" not in cfg:
        warnings.append("generate_until task has no generation_kwargs; harness will default until to fewshot_delimiter")
    if cfg.get("unsafe_code") is True:
        warnings.append("unsafe_code: true requires explicit runtime confirmation")


def validate_local_data_files(path: Path, cfg: dict[str, Any], warnings: list[str], errors: list[str]) -> None:
    dataset_kwargs = cfg.get("dataset_kwargs")
    if not isinstance(dataset_kwargs, dict):
        return
    data_files = dataset_kwargs.get("data_files")
    if data_files is None:
        return
    base_dir = path.expanduser().resolve().parent
    candidates: list[str] = []
    if isinstance(data_files, str):
        candidates = [data_files]
    elif isinstance(data_files, list):
        candidates = [str(item) for item in data_files]
    elif isinstance(data_files, dict):
        for value in data_files.values():
            if isinstance(value, list):
                candidates.extend(str(item) for item in value)
            else:
                candidates.append(str(value))
    for candidate in candidates:
        if "://" in candidate or any(char in candidate for char in "*?[]"):
            continue
        candidate_path = Path(candidate)
        if not candidate_path.is_absolute():
            candidate_path = base_dir / candidate_path
        if not candidate_path.exists():
            errors.append(f"dataset_kwargs.data_files path does not exist: {candidate}")


def lint(path: Path) -> tuple[list[str], list[str]]:
    cfg = load_yaml(path)
    warnings: list[str] = []
    errors: list[str] = []
    validate_task_shape(cfg, errors, warnings)
    validate_function_refs(path, cfg, warnings, errors)
    validate_filters(cfg, warnings, errors)
    validate_metrics(cfg, errors)
    validate_local_data_files(path, cfg, warnings, errors)
    for value in walk_values(cfg):
        if isinstance(value, str):
            for pattern, message in WARNING_PATTERNS:
                if pattern in value:
                    warnings.append(f"string value {message}: {value!r}")
    return warnings, errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Statically lint lm-evaluation-harness YAML task configs without imports or dataset downloads.",
    )
    parser.add_argument("yaml", nargs="+", help="Task or group YAML file(s) to lint.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    exit_code = 0
    for item in args.yaml:
        path = Path(item)
        print(f"==> {path}")
        try:
            warnings, errors = lint(path)
        except Exception as exc:  # noqa: BLE001 - CLI should report all parse/load failures cleanly
            print(f"ERROR: {exc}")
            exit_code = 1
            continue
        for warning in warnings:
            print(f"WARNING: {warning}")
        for error in errors:
            print(f"ERROR: {error}")
        if errors:
            exit_code = 1
        if not warnings and not errors:
            print("OK")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
