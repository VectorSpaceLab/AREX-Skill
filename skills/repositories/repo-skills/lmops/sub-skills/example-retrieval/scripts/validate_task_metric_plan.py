#!/usr/bin/env python3
"""Validate tiny task/metric plans for retrieval-family workflows.

This script only reads JSON or YAML plans, checks them against distilled task
facts, and prints diagnostics. It does not import repository code.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple


ALLOWED_METRICS = {
    "simple_accuracy",
    "acc_and_f1",
    "f1",
    "rouge",
    "squad",
    "trivia_qa",
    "pubmed_qa_acc",
    "bleu",
    "acc_and_matthews_corrcoef",
}

ALLOWED_TASK_TYPES = {
    "multiple_choice",
    "text_completion",
    "generation",
    "qa",
    "cot",
}


@dataclass(frozen=True)
class TaskInfo:
    metric: str
    class_num: int
    alias_of: Optional[str] = None


UPRISE_TASKS: Dict[str, TaskInfo] = {
    "mnli": TaskInfo("simple_accuracy", 3),
    "mnli_m": TaskInfo("simple_accuracy", 3, alias_of="mnli"),
    "mnli_mm": TaskInfo("simple_accuracy", 3, alias_of="mnli"),
    "qnli": TaskInfo("simple_accuracy", 2),
    "rte": TaskInfo("simple_accuracy", 3),
    "snli": TaskInfo("simple_accuracy", 3),
    "boolq": TaskInfo("simple_accuracy", 2),
    "multirc": TaskInfo("f1", 2),
    "openbookqa": TaskInfo("simple_accuracy", 4),
    "squad_v1": TaskInfo("squad", 1),
    "copa": TaskInfo("simple_accuracy", 2),
    "hellaswag": TaskInfo("simple_accuracy", 4),
    "piqa": TaskInfo("simple_accuracy", 2),
    "sentiment140": TaskInfo("simple_accuracy", 2),
    "sst2": TaskInfo("simple_accuracy", 2),
    "yelp": TaskInfo("simple_accuracy", 2),
    "arc_c": TaskInfo("simple_accuracy", 4),
    "arc_e": TaskInfo("simple_accuracy", 4, alias_of="arc_c"),
    "natural_questions": TaskInfo("trivia_qa", 1),
    "mrpc": TaskInfo("acc_and_f1", 2),
    "qqp": TaskInfo("acc_and_f1", 2),
    "paws": TaskInfo("simple_accuracy", 2),
    "wsc": TaskInfo("simple_accuracy", 2),
    "wsc273": TaskInfo("simple_accuracy", 2),
    "winogrande": TaskInfo("simple_accuracy", 2),
    "common_gen": TaskInfo("rouge", 1),
    "dart": TaskInfo("rouge", 1),
    "e2e_nlg": TaskInfo("rouge", 1),
    "ag_news": TaskInfo("simple_accuracy", 4),
    "aeslc": TaskInfo("rouge", 1),
    "gigaword": TaskInfo("rouge", 1),
    "pubmed_qa": TaskInfo("pubmed_qa_acc", 1),
}

SE2_TASKS: Dict[str, TaskInfo] = {
    "mnli": TaskInfo("simple_accuracy", 3),
    "mnli_m": TaskInfo("simple_accuracy", 3, alias_of="mnli"),
    "mnli_mm": TaskInfo("simple_accuracy", 3, alias_of="mnli"),
    "qnli": TaskInfo("simple_accuracy", 2),
    "rte": TaskInfo("simple_accuracy", 3),
    "snli": TaskInfo("simple_accuracy", 3),
    "openbookqa": TaskInfo("simple_accuracy", 4),
    "arc_c": TaskInfo("simple_accuracy", 4),
    "arc_e": TaskInfo("simple_accuracy", 4, alias_of="arc_c"),
    "copa": TaskInfo("simple_accuracy", 2),
    "hellaswag": TaskInfo("simple_accuracy", 4),
    "sentiment140": TaskInfo("simple_accuracy", 2),
    "sst2": TaskInfo("simple_accuracy", 2),
    "sst5": TaskInfo("simple_accuracy", 5),
    "mrpc": TaskInfo("acc_and_f1", 2),
    "qqp": TaskInfo("acc_and_f1", 2),
    "paws": TaskInfo("simple_accuracy", 2),
    "common_gen": TaskInfo("rouge", 1),
    "e2e_nlg": TaskInfo("rouge", 1),
    "ag_news": TaskInfo("simple_accuracy", 4),
    "aeslc": TaskInfo("rouge", 1),
    "gigaword": TaskInfo("rouge", 1),
    "roc_story": TaskInfo("rouge", 1),
    "roc_ending": TaskInfo("rouge", 1),
    "pubmed_qa": TaskInfo("pubmed_qa_acc", 1),
}

PROJECT_TASKS = {
    "uprise": UPRISE_TASKS,
    "se2": SE2_TASKS,
    "llm-retriever": {**UPRISE_TASKS, **SE2_TASKS},
}


CLUSTER_HINTS = {
    "uprise": {
        "close_qa", "common_reason", "coreference", "nli", "paraphrase", "reading",
        "sentiment", "struct2text", "summarize", "train_example_1", "train_example_2",
        "test_example_1", "test_example_2", "cot_train_example", "cot_test_example",
    },
    "se2": {
        "copa", "arc_c", "arc_e", "openbookqa", "mrpc", "qqp", "paws", "mnli",
        "qnli", "snli", "rte", "sst2", "sst5", "sentiment140", "hellaswag",
        "ag_news", "roc_story", "roc_ending", "gigaword", "aeslc", "common_gen", "e2e_nlg",
    },
}


def load_plan(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".json":
        return json.loads(text)
    if suffix in {".yml", ".yaml"}:
        try:
            import yaml  # type: ignore
        except Exception as exc:  # pragma: no cover - friendly runtime branch
            raise RuntimeError(
                "YAML input requires PyYAML. Use JSON instead or install pyyaml."
            ) from exc
        return yaml.safe_load(text)
    raise ValueError(f"Unsupported plan format: {path.suffix}")


def flatten_entries(obj: Any) -> List[Dict[str, Any]]:
    if isinstance(obj, list):
        return [dict(item) for item in obj]
    if isinstance(obj, dict) and isinstance(obj.get("tasks"), list):
        base = {k: v for k, v in obj.items() if k != "tasks"}
        entries = []
        for item in obj["tasks"]:
            merged = dict(base)
            merged.update(item)
            entries.append(merged)
        return entries
    if isinstance(obj, dict):
        return [dict(obj)]
    raise TypeError(f"Plan must be an object or list, not {type(obj).__name__}")


def canonical_task_name(entry: Mapping[str, Any]) -> Optional[str]:
    for key in ("task_name", "task", "name"):
        value = entry.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def canonical_project(entry: Mapping[str, Any], fallback: str) -> str:
    value = entry.get("project")
    if value not in (None, ""):
        return str(value)
    return fallback


def canonical_metric(entry: Mapping[str, Any]) -> Optional[str]:
    for key in ("metric", "metric_name"):
        value = entry.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def canonical_int(entry: Mapping[str, Any], *keys: str) -> Optional[int]:
    for key in keys:
        value = entry.get(key)
        if value not in (None, ""):
            try:
                return int(value)
            except Exception:
                return None
    return None


def resolve_task_info(project: str, task_name: str) -> Optional[TaskInfo]:
    project_map = PROJECT_TASKS.get(project, {})
    info = project_map.get(task_name)
    if info is None:
        return None
    seen = set()
    while info.alias_of is not None and info.alias_of not in seen:
        seen.add(info.alias_of)
        parent = project_map.get(info.alias_of)
        if parent is None:
            break
        info = parent
    return info


def split_tokens(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [token.strip() for token in str(value).split("+") if token.strip()]


def classify_task_type(metric: str, class_num: int) -> str:
    if metric in {"rouge", "squad", "trivia_qa", "bleu"}:
        return "generation" if class_num == 1 else "qa"
    if class_num == 1:
        return "text_completion"
    if class_num > 1:
        return "multiple_choice"
    return "qa"


def validate_entry(entry: Mapping[str, Any], default_project: str, strict: bool) -> Tuple[List[str], List[str]]:
    warnings: List[str] = []
    errors: List[str] = []

    project = canonical_project(entry, default_project)
    if project not in PROJECT_TASKS:
        errors.append(f"unknown project {project!r}; expected one of {sorted(PROJECT_TASKS)}")
        return warnings, errors

    task_name = canonical_task_name(entry)
    if not task_name:
        errors.append("missing task_name/task/name field")
        return warnings, errors

    metric = canonical_metric(entry)
    class_num = canonical_int(entry, "class_num", "num_classes")
    task_type = entry.get("task_type") or entry.get("type")
    allow_custom = bool(entry.get("custom_task") or entry.get("allow_custom_task"))

    info = resolve_task_info(project, task_name)
    if info is None:
        if not allow_custom:
            errors.append(
                f"unknown task {task_name!r} for project {project!r}; set custom_task=true if this is intentional"
            )
        if metric is None:
            errors.append("custom task needs an explicit metric")
        elif metric not in ALLOWED_METRICS:
            errors.append(f"unknown metric {metric!r}; allowed metrics: {sorted(ALLOWED_METRICS)}")
        if class_num is None:
            errors.append("custom task needs an explicit class_num/num_classes")
        elif class_num < 1:
            errors.append(f"class_num must be positive, got {class_num}")
        if task_type and task_type not in ALLOWED_TASK_TYPES:
            errors.append(
                f"unknown task_type {task_type!r}; expected one of {sorted(ALLOWED_TASK_TYPES)}"
            )
        return warnings, errors

    expected_metric = info.metric
    expected_class_num = info.class_num
    if metric is None:
        warnings.append(
            f"{task_name}: metric missing; expected {expected_metric!r}"
        )
    elif metric != expected_metric:
        errors.append(
            f"{task_name}: metric mismatch, got {metric!r} but expected {expected_metric!r}"
        )

    if class_num is None:
        warnings.append(f"{task_name}: class_num missing; expected {expected_class_num}")
    elif class_num != expected_class_num:
        errors.append(
            f"{task_name}: class_num mismatch, got {class_num} but expected {expected_class_num}"
        )

    if metric and metric not in ALLOWED_METRICS:
        warnings.append(f"{task_name}: metric {metric!r} is not in the bundled allowed list")

    if task_type and task_type not in ALLOWED_TASK_TYPES:
        warnings.append(
            f"{task_name}: task_type {task_type!r} is not one of the bundled values {sorted(ALLOWED_TASK_TYPES)}"
        )

    if metric and class_num:
        inferred = classify_task_type(metric, class_num)
        if task_type and task_type != inferred:
            warnings.append(
                f"{task_name}: task_type {task_type!r} does not match the inferred shape {inferred!r}"
            )

    for field in ("train_clusters", "test_clusters", "prompt_pool_path", "output_dir", "data_dir"):
        value = entry.get(field)
        if isinstance(value, str) and "/" in value and value.startswith("<"):
            warnings.append(f"{task_name}: {field} uses a placeholder path string; that is fine for planning")

    clusters = split_tokens(entry.get("train_clusters")) + split_tokens(entry.get("test_clusters"))
    if clusters:
        known = CLUSTER_HINTS.get(project, set())
        unknown = [cluster for cluster in clusters if cluster not in known]
        if unknown:
            warnings.append(
                f"{task_name}: cluster names {unknown} are not in the bundled hints; this is fine if they are custom"
            )

    return warnings, errors


def format_messages(title: str, messages: Sequence[str]) -> List[str]:
    if not messages:
        return []
    out = [title]
    out.extend(f"- {msg}" for msg in messages)
    return out


def validate_plan(plan: Any, default_project: str, strict: bool) -> Tuple[List[str], List[str]]:
    entries = flatten_entries(plan)
    lines: List[str] = []
    warnings: List[str] = []
    errors: List[str] = []
    for idx, entry in enumerate(entries, start=1):
        entry_warnings, entry_errors = validate_entry(entry, default_project=default_project, strict=strict)
        task_name = canonical_task_name(entry) or f"entry-{idx}"
        project = canonical_project(entry, default_project)
        if entry_errors:
            lines.append(f"[ERROR] {project}:{task_name}")
            lines.extend(f"  - {msg}" for msg in entry_errors)
            errors.extend(entry_errors)
        elif entry_warnings:
            lines.append(f"[WARN] {project}:{task_name}")
            lines.extend(f"  - {msg}" for msg in entry_warnings)
            warnings.extend(entry_warnings)
        else:
            lines.append(f"[OK] {project}:{task_name}")
    return lines, warnings + errors


def print_known() -> None:
    for project, tasks in PROJECT_TASKS.items():
        print(project)
        for name in sorted(tasks):
            info = tasks[name]
            print(f"  {name}: metric={info.metric}, class_num={info.class_num}, alias_of={info.alias_of}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a tiny retrieval-family task/metric plan")
    parser.add_argument("plan", nargs="?", help="Path to JSON or YAML plan file")
    parser.add_argument("--project", default="uprise", choices=sorted(PROJECT_TASKS), help="Default project if a plan entry omits it")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--show-known", action="store_true", help="Print the bundled task/metric map and exit")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.show_known:
        print_known()
        return 0

    if not args.plan:
        parser.error("plan is required unless --show-known is used")

    plan_path = Path(args.plan)
    if not plan_path.exists():
        print(f"Plan file not found: {plan_path}", file=sys.stderr)
        return 2

    try:
        plan = load_plan(plan_path)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Failed to read plan: {exc}", file=sys.stderr)
        return 2

    lines, findings = validate_plan(plan, default_project=args.project, strict=args.strict)
    for line in lines:
        print(line)

    warnings = [line for line in findings if "mismatch" not in line and "unknown" not in line]
    # The validator stores both warnings and errors in `findings`; errors have already been printed above.
    # Any error was emitted as [ERROR] in the main output, so exit non-zero if needed by scanning the lines.
    has_error = any(line.startswith("[ERROR]") for line in lines)
    has_warn = any(line.startswith("[WARN]") for line in lines)

    if has_error:
        return 1
    if args.strict and has_warn:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
