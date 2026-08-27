#!/usr/bin/env python3
"""Static LLM Foundry evaluation YAML linter.

Safe by design: this helper never imports llmfoundry, loads models, downloads
remote datasets, contacts API providers, initializes distributed state, or
allocates accelerators. It parses one eval YAML, optionally follows local
`icl_tasks` and `eval_gauntlet` YAML references, samples local JSONL task rows,
and reports common schema mistakes before `llmfoundry eval` is launched.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml  # type: ignore
except Exception as exc:  # pragma: no cover - depends on target env
    yaml = None  # type: ignore[assignment]
    YAML_IMPORT_ERROR = exc
else:
    YAML_IMPORT_ERROR = None

REMOTE_PREFIXES = (
    "hf://",
    "s3://",
    "gs://",
    "oci://",
    "azure://",
    "http://",
    "https://",
    "dbfs:/",
)

EVAL_REQUIRED = ("models", "max_seq_len", "device_eval_batch_size")
EVAL_KNOWN = {
    "models", "model", "model_name", "tokenizer", "load_path",
    "max_seq_len", "device_eval_batch_size", "code_paths", "eval_gauntlet",
    "eval_gauntlet_str", "eval_loader", "eval_loaders",
    "eval_subset_num_batches", "icl_subset_num_batches", "icl_tasks",
    "icl_tasks_str", "python_log_level", "loggers", "console_log_interval",
    "log_config", "seed", "precision", "run_name", "metadata",
    "dist_timeout", "fsdp_config", "callbacks", "variables",
}

TASK_CONFIG_REQUIRED: dict[str, set[str]] = {
    "generation_task_with_answers": {"label", "dataset_uri", "num_fewshot", "icl_task_type"},
    "language_modeling": {"label", "dataset_uri", "num_fewshot", "icl_task_type"},
    "multiple_choice": {"label", "dataset_uri", "num_fewshot", "icl_task_type"},
    "schema": {"label", "dataset_uri", "num_fewshot", "icl_task_type"},
}

TASK_ROW_REQUIRED: dict[str, dict[str, type]] = {
    "generation_task_with_answers": {"context": str, "answer": str, "aliases": list},
    "language_modeling": {"context": str, "continuation": str},
    "multiple_choice": {"query": str, "choices": list, "gold": int},
    "schema": {"context_options": list, "continuation": str, "gold": int},
}

LIKELY_METRICS: dict[str, tuple[str, ...]] = {
    "generation_task_with_answers": ("InContextLearningGenerationExactMatchAccuracy",),
    "language_modeling": ("InContextLearningLMAccuracy", "InContextLearningLMExpectedCalibrationError"),
    "multiple_choice": ("InContextLearningMultipleChoiceAccuracy", "InContextLearningMCExpectedCalibrationError"),
    "schema": ("InContextLearningMultipleChoiceAccuracy", "InContextLearningMCExpectedCalibrationError"),
}

REGISTRY_ALIAS_TO_CLASS = {
    "qa_accuracy": "InContextLearningGenerationExactMatchAccuracy",
    "lm_accuracy": "InContextLearningLMAccuracy",
    "lm_expected_calibration_error": "InContextLearningLMExpectedCalibrationError",
    "mc_accuracy": "InContextLearningMultipleChoiceAccuracy",
    "mc_expected_calibration_error": "InContextLearningMCExpectedCalibrationError",
}

WEIGHTINGS = {"EQUAL", "SAMPLE_SZ", "LOG_SAMPLE_SZ"}


def _load_yaml(path: Path) -> Any:
    if yaml is None:
        raise RuntimeError(f"PyYAML is unavailable: {YAML_IMPORT_ERROR}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {} if data is None else data


def _is_remote(value: str) -> bool:
    return value.startswith(REMOTE_PREFIXES)


def _has_interpolation(value: str) -> bool:
    return "${" in value and "}" in value


def _unique(paths: Iterable[Path]) -> list[Path]:
    seen: set[str] = set()
    out: list[Path] = []
    for p in paths:
        key = os.fspath(p)
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def _candidate_roots(anchor: Path) -> list[Path]:
    # Search from CWD and from the config/reference directory upward. This is
    # safe and makes the linter usable from arbitrary working directories while
    # still never downloading remote resources.
    base = anchor.parent if anchor.suffix or anchor.is_file() else anchor
    return _unique([Path.cwd(), base, *list(base.parents)[:5]])


def _resolve_local_ref(value: str, anchor: Path) -> Path | None:
    if _is_remote(value) or _has_interpolation(value):
        return None
    p = Path(os.path.expanduser(value))
    if p.is_absolute():
        return p if p.exists() else None
    for root in _candidate_roots(anchor):
        candidate = root / p
        if candidate.exists():
            return candidate
    return None


def _resolve_yaml_section(value: Any, anchor: Path, wrapper_key: str) -> tuple[Any, Path | None, str | None]:
    """Return (section_value, source_path, unresolved_reason)."""
    if isinstance(value, str):
        resolved = _resolve_local_ref(value, anchor)
        if resolved is None:
            if _is_remote(value):
                return None, None, f"remote YAML reference not loaded: {value}"
            if _has_interpolation(value):
                return None, None, f"interpolated YAML reference not resolved: {value}"
            return None, None, f"local YAML reference not found from safe search roots: {value}"
        loaded = _load_yaml(resolved)
        if isinstance(loaded, dict) and wrapper_key in loaded:
            return loaded[wrapper_key], resolved, None
        return loaded, resolved, None
    if isinstance(value, dict) and wrapper_key in value:
        return value[wrapper_key], anchor, None
    return value, anchor, None


def _num_fewshot_values(value: Any, where: str, errors: list[str]) -> list[Any]:
    if isinstance(value, list):
        if not value:
            errors.append(f"{where}: num_fewshot must not be empty")
        return value
    errors.append(f"{where}: num_fewshot must be a list, for example [0]")
    return []


def _check_top_level(cfg: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    for key in cfg:
        if key == "subsets":
            warnings.append("top-level: `subsets` is not an EvalConfig key here; use eval_subset_num_batches or icl_subset_num_batches")
        elif key not in EVAL_KNOWN:
            warnings.append(f"top-level: unknown EvalConfig key {key!r}")
    for key in EVAL_REQUIRED:
        if key not in cfg:
            # A single-model shorthand exists, but the canonical eval contract
            # and result-comparison workflow use models:.
            if key == "models" and "model" in cfg:
                warnings.append("top-level: using single-model shorthand; canonical configs use a models: list")
                if "tokenizer" not in cfg:
                    errors.append("top-level: single-model shorthand requires tokenizer")
            else:
                errors.append(f"EvalConfig missing required top-level key {key!r}")
    if ("icl_tasks" in cfg or "icl_tasks_str" in cfg) and not isinstance(cfg.get("device_eval_batch_size"), int):
        errors.append("top-level: device_eval_batch_size must be an integer when ICL tasks are present")


def _models_from_cfg(cfg: dict[str, Any]) -> list[Any]:
    if isinstance(cfg.get("models"), list):
        return cfg["models"]
    if "model" in cfg:
        return [{"model_name": cfg.get("model_name"), "model": cfg.get("model"), "tokenizer": cfg.get("tokenizer"), "load_path": cfg.get("load_path")}]
    return []


def _check_models(cfg: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    models = _models_from_cfg(cfg)
    if "models" in cfg and not models:
        errors.append("models: must be a non-empty list")
    for idx, entry in enumerate(models):
        where = f"models[{idx}]"
        if not isinstance(entry, dict):
            errors.append(f"{where}: must be a mapping")
            continue
        if not entry.get("model_name"):
            errors.append(f"{where}: missing model_name; result tables require it")
        model = entry.get("model")
        tokenizer = entry.get("tokenizer")
        if not isinstance(model, dict):
            errors.append(f"{where}.model: missing or invalid model block")
            continue
        if not model.get("name"):
            errors.append(f"{where}.model.name: missing registry name")
        if not isinstance(tokenizer, dict) or not tokenizer.get("name"):
            errors.append(f"{where}.tokenizer.name: missing tokenizer name")
        if model.get("name") == "mpt_causal_lm" and not entry.get("load_path"):
            errors.append(f"{where}: mpt_causal_lm offline eval requires load_path")
        if model.get("load_in_8bit") and cfg.get("fsdp_config"):
            errors.append(f"{where}: fsdp_config is not supported with Hugging Face 8-bit loading")
        if model.get("name") in {"openai_chat", "openai_causal_lm"}:
            if not model.get("version"):
                warnings.append(f"{where}: OpenAI API wrapper usually needs model.version")
            if not model.get("base_url") and os.environ.get("OPENAI_API_KEY") is None:
                warnings.append(f"{where}: OPENAI_API_KEY is not set for default OpenAI endpoint")
        if model.get("name") in {"fmapi_chat", "fmapi_causal_lm"} and not (model.get("base_url") or model.get("local")):
            errors.append(f"{where}: FMAPI wrappers require base_url or local: true")


def _validate_jsonl_row(task: dict[str, Any], row: Any, line_no: int, where: str, errors: list[str]) -> None:
    task_type = task.get("icl_task_type")
    required = TASK_ROW_REQUIRED.get(str(task_type), {})
    if not isinstance(row, dict):
        errors.append(f"{where}: line {line_no}: expected JSON object")
        return
    for field, typ in required.items():
        if field not in row:
            errors.append(f"{where}: line {line_no}: missing row field {field!r}")
            continue
        value = row[field]
        if typ is int:
            if not isinstance(value, int) or isinstance(value, bool):
                errors.append(f"{where}: line {line_no}: {field!r} must be an integer")
        elif not isinstance(value, typ):
            errors.append(f"{where}: line {line_no}: {field!r} must be {typ.__name__}")
    if task_type == "generation_task_with_answers" and isinstance(row.get("aliases"), list):
        for alias in row["aliases"]:
            if not isinstance(alias, str):
                errors.append(f"{where}: line {line_no}: every alias must be a string")
    if task_type == "multiple_choice" and isinstance(row.get("choices"), list) and isinstance(row.get("gold"), int) and not isinstance(row.get("gold"), bool):
        if not row["choices"]:
            errors.append(f"{where}: line {line_no}: choices must not be empty")
        elif not (0 <= row["gold"] < len(row["choices"])):
            errors.append(f"{where}: line {line_no}: gold index {row['gold']} outside choices")
        for choice in row["choices"]:
            if not isinstance(choice, str):
                errors.append(f"{where}: line {line_no}: every choice must be a string")
    if task_type == "schema" and isinstance(row.get("context_options"), list) and isinstance(row.get("gold"), int) and not isinstance(row.get("gold"), bool):
        if not row["context_options"]:
            errors.append(f"{where}: line {line_no}: context_options must not be empty")
        elif not (0 <= row["gold"] < len(row["context_options"])):
            errors.append(f"{where}: line {line_no}: gold index {row['gold']} outside context_options")
        for option in row["context_options"]:
            if not isinstance(option, str):
                errors.append(f"{where}: line {line_no}: every context option must be a string")
    if task.get("has_categories"):
        if "category" not in row:
            errors.append(f"{where}: line {line_no}: has_categories requires category")
        elif not isinstance(row.get("category"), str):
            errors.append(f"{where}: line {line_no}: category must be a string")


def _sample_dataset(task: dict[str, Any], where: str, anchor: Path, max_rows: int, errors: list[str], warnings: list[str]) -> None:
    dataset_uri = task.get("dataset_uri")
    if not isinstance(dataset_uri, str):
        return
    if _is_remote(dataset_uri) or _has_interpolation(dataset_uri):
        return
    path = _resolve_local_ref(dataset_uri, anchor)
    if path is None:
        warnings.append(f"{where}: local dataset_uri not found from safe search roots: {dataset_uri}")
        return
    if not path.is_file():
        warnings.append(f"{where}: resolved dataset_uri is not a file: {path}")
        return
    inspected = 0
    try:
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except Exception as exc:
                    errors.append(f"{where}: line {line_no}: invalid JSON: {exc}")
                    continue
                _validate_jsonl_row(task, row, line_no, where, errors)
                inspected += 1
                if inspected >= max_rows:
                    break
    except Exception as exc:
        warnings.append(f"{where}: could not read local dataset {path}: {exc}")
        return
    if inspected == 0:
        errors.append(f"{where}: local dataset file contains no rows: {path}")


def _as_task_list(value: Any) -> list[Any] | None:
    if isinstance(value, dict) and "icl_tasks" in value:
        value = value["icl_tasks"]
    if isinstance(value, list):
        return value
    return None


def _lint_tasks(raw_value: Any, config_path: Path, max_rows: int, errors: list[str], warnings: list[str]) -> set[tuple[str, int]]:
    if raw_value is None:
        return set()
    loaded, source_path, reason = _resolve_yaml_section(raw_value, config_path, "icl_tasks")
    if reason:
        warnings.append(f"icl_tasks: {reason}")
        return set()
    tasks = _as_task_list(loaded)
    if tasks is None:
        errors.append("icl_tasks: provided but no task list could be parsed")
        return set()
    seen_pairs: set[tuple[str, int]] = set()
    labels: set[str] = set()
    anchor = source_path or config_path
    for idx, task in enumerate(tasks):
        where = f"icl_tasks[{idx}]"
        if not isinstance(task, dict):
            errors.append(f"{where}: expected mapping")
            continue
        task_type = task.get("icl_task_type")
        label = task.get("label")
        if task_type not in TASK_CONFIG_REQUIRED:
            errors.append(f"{where}: unsupported or missing icl_task_type {task_type!r}; expected one of {sorted(TASK_CONFIG_REQUIRED)}")
            continue
        missing = sorted(TASK_CONFIG_REQUIRED[task_type] - set(task))
        if missing:
            errors.append(f"{where} ({label!r}): missing required task config fields: {', '.join(missing)}")
        if not isinstance(label, str) or not label:
            errors.append(f"{where}: label must be a non-empty string")
        elif label in labels:
            warnings.append(f"{where}: duplicate label {label!r}; result tables may be ambiguous")
        elif isinstance(label, str):
            labels.add(label)
        fewshots = _num_fewshot_values(task.get("num_fewshot"), where, errors)
        for nfs in fewshots:
            if isinstance(label, str) and isinstance(nfs, int) and not isinstance(nfs, bool):
                seen_pairs.add((label, nfs))
            elif nfs is not None:
                errors.append(f"{where}: num_fewshot value {nfs!r} must be an integer")
        metric_names = task.get("metric_names") or []
        if isinstance(metric_names, str):
            metric_names = [metric_names]
        if metric_names and not isinstance(metric_names, list):
            errors.append(f"{where}: metric_names must be a list")
        elif isinstance(metric_names, list):
            expected = LIKELY_METRICS[task_type]
            for metric in metric_names:
                if metric in REGISTRY_ALIAS_TO_CLASS:
                    warnings.append(f"{where}: {metric!r} is a registry alias; ICL task YAMLs usually use {REGISTRY_ALIAS_TO_CLASS[metric]!r}")
                elif metric not in expected:
                    warnings.append(f"{where}: metric {metric!r} is unusual for {task_type}; expected one of {expected}")
        if "question_prelimiter" in task and "prelimiter" in task:
            errors.append(f"{where}: question_prelimiter and prelimiter are aliases; set only one")
        if "num_beams" in task:
            errors.append(f"{where}: top-level num_beams is unsupported; use generation_kwargs.num_beams")
        if task.get("batch_size") is not None and not isinstance(task.get("batch_size"), int):
            errors.append(f"{where}: batch_size must be an integer")
        if task.get("has_categories") is not None and not isinstance(task.get("has_categories"), bool):
            errors.append(f"{where}: has_categories must be true or false")
        _sample_dataset(task, where, anchor, max_rows, errors, warnings)
    return seen_pairs


def _lint_gauntlet(raw_value: Any, config_path: Path, seen_tasks: set[tuple[str, int]], errors: list[str], warnings: list[str]) -> None:
    if raw_value is None:
        return
    loaded, _source_path, reason = _resolve_yaml_section(raw_value, config_path, "eval_gauntlet")
    if reason:
        warnings.append(f"eval_gauntlet: {reason}")
        return
    if isinstance(loaded, dict) and "eval_gauntlet" in loaded:
        loaded = loaded["eval_gauntlet"]
    if not isinstance(loaded, dict) or not loaded:
        errors.append("eval_gauntlet: provided but no mapping could be parsed")
        return
    weighting = loaded.get("weighting", "EQUAL")
    if weighting not in WEIGHTINGS:
        errors.append(f"eval_gauntlet.weighting: expected one of {sorted(WEIGHTINGS)}, got {weighting!r}")
    subtract = loaded.get("subtract_random_baseline", True)
    rescale = loaded.get("rescale_accuracy", True)
    if not isinstance(subtract, bool):
        errors.append("eval_gauntlet.subtract_random_baseline must be true or false")
    if not isinstance(rescale, bool):
        errors.append("eval_gauntlet.rescale_accuracy must be true or false")
    if rescale is True and subtract is False:
        errors.append("eval_gauntlet: rescale_accuracy requires subtract_random_baseline=true")
    categories = loaded.get("categories")
    if not isinstance(categories, list) or not categories:
        errors.append("eval_gauntlet.categories must be a non-empty list")
        return
    category_names: set[str] = set()
    for cidx, category in enumerate(categories):
        cwhere = f"eval_gauntlet.categories[{cidx}]"
        if not isinstance(category, dict):
            errors.append(f"{cwhere}: must be a mapping")
            continue
        cname = category.get("name")
        if not isinstance(cname, str) or not cname:
            errors.append(f"{cwhere}: missing category name")
            cname = f"#{cidx}"
        if cname in category_names:
            errors.append(f"{cwhere}: duplicate category name {cname!r}")
        category_names.add(str(cname))
        benchmarks = category.get("benchmarks")
        if not isinstance(benchmarks, list) or not benchmarks:
            errors.append(f"{cwhere}: benchmarks must be a non-empty list")
            continue
        for bidx, benchmark in enumerate(benchmarks):
            bwhere = f"{cwhere}.benchmarks[{bidx}]"
            if not isinstance(benchmark, dict):
                errors.append(f"{bwhere}: must be a mapping")
                continue
            missing = {"name", "num_fewshot", "random_baseline"} - set(benchmark)
            if missing:
                errors.append(f"{bwhere}: missing {', '.join(sorted(missing))}")
                continue
            name, nfs = benchmark.get("name"), benchmark.get("num_fewshot")
            baseline = benchmark.get("random_baseline")
            if not isinstance(nfs, int) or isinstance(nfs, bool):
                errors.append(f"{bwhere}: num_fewshot must be an integer")
            if not isinstance(baseline, (int, float)) or isinstance(baseline, bool) or not (0 <= float(baseline) < 1):
                errors.append(f"{bwhere}: random_baseline must satisfy 0 <= value < 1")
            if seen_tasks and isinstance(name, str) and isinstance(nfs, int) and not isinstance(nfs, bool) and (name, nfs) not in seen_tasks:
                same_name = sorted(v for k, v in seen_tasks if k == name)
                if same_name:
                    warnings.append(f"{bwhere}: benchmark {(name, nfs)!r} has no exact task match; task few-shot values for {name!r}: {same_name}")
                else:
                    warnings.append(f"{bwhere}: benchmark {name!r} has no matching icl_tasks label")
    averages = loaded.get("averages")
    if averages is not None:
        if not isinstance(averages, dict):
            errors.append("eval_gauntlet.averages must be a mapping")
        else:
            for avg_name, cats in averages.items():
                if avg_name in category_names:
                    errors.append(f"eval_gauntlet.averages.{avg_name}: average name duplicates a category name")
                if not isinstance(cats, list):
                    errors.append(f"eval_gauntlet.averages.{avg_name}: must be a list of category names")
                    continue
                for cat in cats:
                    if cat not in category_names:
                        warnings.append(f"eval_gauntlet.averages.{avg_name}: unknown category {cat!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Statically lint an LLM Foundry eval YAML without running models or downloading data.")
    parser.add_argument("yaml_path", type=Path, help="Evaluation YAML to inspect")
    parser.add_argument("--max-jsonl-rows", type=int, default=20, help="Maximum local JSONL rows to sample per task")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args(argv)

    errors: list[str] = []
    warnings: list[str] = []
    yaml_path = args.yaml_path.expanduser()
    if not yaml_path.exists():
        errors.append(f"YAML file does not exist: {yaml_path}")
        result = {"ok": False, "errors": errors, "warnings": warnings, "tasks_checked": 0}
        print(json.dumps(result, indent=2) if args.json else "\n".join(errors))
        return 2
    # Keep process-substitution and /dev/fd paths usable; resolving them can
    # dereference to a non-openable procfs pipe target on some systems.
    yaml_path = yaml_path.absolute()
    try:
        cfg = _load_yaml(yaml_path)
    except Exception as exc:
        errors.append(f"Could not parse YAML: {exc}")
        result = {"ok": False, "errors": errors, "warnings": warnings, "tasks_checked": 0}
        print(json.dumps(result, indent=2) if args.json else "\n".join(errors))
        return 2
    if not isinstance(cfg, dict):
        errors.append(f"YAML root must be a mapping, got {type(cfg).__name__}")
        cfg = {}

    _check_top_level(cfg, errors, warnings)
    _check_models(cfg, errors, warnings)
    seen_tasks = _lint_tasks(cfg.get("icl_tasks", cfg.get("icl_tasks_str")), yaml_path, args.max_jsonl_rows, errors, warnings)
    _lint_gauntlet(cfg.get("eval_gauntlet", cfg.get("eval_gauntlet_str")), yaml_path, seen_tasks, errors, warnings)

    ok = not errors and not (args.strict and warnings)
    result = {"ok": ok, "tasks_checked": len({label for label, _ in seen_tasks}), "errors": errors, "warnings": warnings}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"LLM Foundry eval config lint: {'PASS' if ok else 'FAIL'}")
        print(f"Task labels checked: {result['tasks_checked']}")
        for err in errors:
            print(f"ERROR: {err}")
        for warn in warnings:
            print(f"WARNING: {warn}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
