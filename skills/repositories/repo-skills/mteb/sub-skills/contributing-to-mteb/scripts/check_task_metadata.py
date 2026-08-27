#!/usr/bin/env python3
"""Safely validate MTEB task metadata without downloading datasets by default."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any

PROMPT_KEYS = {"query", "passage"}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise TypeError("metadata JSON must contain one object")
    if "metadata" in data and isinstance(data["metadata"], dict):
        return data["metadata"]
    return data


def load_task_metadata(task_class: str) -> Any:
    if ":" not in task_class:
        raise ValueError("--task-class must use module.path:ClassName")
    module_name, class_name = task_class.split(":", 1)
    module = importlib.import_module(module_name)
    task_cls = getattr(module, class_name)
    metadata = getattr(task_cls, "metadata", None)
    if metadata is None:
        task = task_cls()
        metadata = getattr(task, "metadata", None)
    if metadata is None:
        raise AttributeError(f"{task_class} does not expose metadata")
    return metadata


def build_task_metadata(data: dict[str, Any]) -> Any:
    from mteb.abstasks.task_metadata import TaskMetadata

    return TaskMetadata(**data)


def build_metadata_from_json(data: dict[str, Any], warnings: list[str]) -> Any:
    try:
        return build_task_metadata(data)
    except ModuleNotFoundError as exc:
        warnings.append(
            f"MTEB import unavailable ({exc}); running structural JSON checks only"
        )
        return data


def metadata_to_dict(metadata: Any) -> dict[str, Any]:
    if hasattr(metadata, "model_dump"):
        return metadata.model_dump()
    if isinstance(metadata, dict):
        return dict(metadata)
    raise TypeError(f"unsupported metadata object: {type(metadata)!r}")


def check_prompt(metadata_dict: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    prompt = metadata_dict.get("prompt")
    if isinstance(prompt, dict):
        extra = sorted(set(prompt) - PROMPT_KEYS)
        if extra:
            errors.append(f"prompt dict has invalid keys: {extra}; expected only query/passage")
        task_type = metadata_dict.get("type")
        if task_type not in {"Retrieval", "Reranking", "InstructionRetrieval", "InstructionReranking"}:
            warnings.append("prompt is a dict; MTEB usually reserves dict prompts for retrieval-like tasks")


def check_eval_langs(metadata_dict: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    eval_langs = metadata_dict.get("eval_langs")
    if not eval_langs:
        errors.append("eval_langs is required")
        return
    if isinstance(eval_langs, dict):
        for subset, languages in eval_langs.items():
            if not subset:
                errors.append("eval_langs contains an empty subset name")
            if not isinstance(languages, list) or not languages:
                errors.append(f"eval_langs[{subset!r}] must be a non-empty list")
            else:
                for code in languages:
                    if not isinstance(code, str) or "-" not in code:
                        warnings.append(f"language code {code!r} should usually include language and script, e.g. eng-Latn")
    elif isinstance(eval_langs, list):
        for code in eval_langs:
            if not isinstance(code, str) or "-" not in code:
                warnings.append(f"language code {code!r} should usually include language and script, e.g. eng-Latn")
    else:
        errors.append("eval_langs must be a list or a subset-to-list mapping")


def check_required_fields(metadata: Any, metadata_dict: dict[str, Any], require_filled: bool, errors: list[str], warnings: list[str]) -> None:
    dataset = metadata_dict.get("dataset")
    if not isinstance(dataset, dict):
        errors.append("dataset must be a mapping with path and revision")
    else:
        if not dataset.get("path"):
            errors.append("dataset.path is required")
        if not dataset.get("revision"):
            errors.append("dataset.revision must be pinned and non-null")
        if dataset.get("trust_remote_code", False) is not False:
            errors.append("dataset.trust_remote_code must be false or omitted")

    for field_name in ["name", "description", "type", "eval_splits", "main_score"]:
        if not metadata_dict.get(field_name):
            errors.append(f"{field_name} is required")

    if require_filled:
        if hasattr(metadata, "is_filled"):
            try:
                if not metadata.is_filled():
                    errors.append("metadata.is_filled() returned false")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"metadata.is_filled() raised {exc.__class__.__name__}: {exc}")
        else:
            nullable_allowed = {"prompt", "adapted_from", "contributed_by", "superseded_by"}
            expected_fields = {
                "dataset",
                "name",
                "description",
                "type",
                "modalities",
                "category",
                "reference",
                "eval_splits",
                "eval_langs",
                "main_score",
                "date",
                "domains",
                "task_subtypes",
                "license",
                "annotations_creators",
                "dialect",
                "sample_creation",
                "bibtex_citation",
                "is_public",
                "is_beta",
            }
            missing = sorted(
                key
                for key in expected_fields
                if key not in nullable_allowed and metadata_dict.get(key) is None
            )
            if missing:
                errors.append(f"metadata has unfilled fields: {missing}")

    if metadata_dict.get("is_beta"):
        warnings.append("task is marked beta; default task discovery excludes beta tasks")
    if metadata_dict.get("is_public") is False:
        warnings.append("task is private; default public workflows may skip it or require credentials")
    if metadata_dict.get("superseded_by"):
        warnings.append("task is superseded; default task discovery excludes superseded tasks")


def check_native_methods(metadata: Any, require_descriptive_stats: bool, errors: list[str], warnings: list[str]) -> None:
    if hasattr(metadata, "_validate_metadata"):
        try:
            metadata._validate_metadata()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"metadata._validate_metadata() raised {exc.__class__.__name__}: {exc}")

    if require_descriptive_stats:
        descriptive_stats = getattr(metadata, "descriptive_stats", None)
        if descriptive_stats is None:
            errors.append("metadata.descriptive_stats is missing; run task.calculate_descriptive_statistics()")
        n_samples = getattr(metadata, "n_samples", None)
        if n_samples is None:
            errors.append("metadata.n_samples is missing; descriptive statistics may not be available")
    else:
        descriptive_stats = getattr(metadata, "descriptive_stats", None)
        if descriptive_stats is None:
            warnings.append("metadata.descriptive_stats is not available; required before merging non-aggregate tasks")


def validate(args: argparse.Namespace) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    if args.metadata_json:
        metadata = build_metadata_from_json(load_json(args.metadata_json), warnings)
    elif args.task_class:
        metadata = load_task_metadata(args.task_class)
    else:
        raise ValueError("provide --metadata-json or --task-class")

    metadata_dict = metadata_to_dict(metadata)
    check_required_fields(metadata, metadata_dict, args.require_filled, errors, warnings)
    check_eval_langs(metadata_dict, errors, warnings)
    check_prompt(metadata_dict, errors, warnings)
    check_native_methods(metadata, args.require_descriptive_stats, errors, warnings)

    output = {
        "ok": not errors,
        "name": metadata_dict.get("name"),
        "type": metadata_dict.get("type"),
        "dataset": metadata_dict.get("dataset"),
        "warnings": warnings,
        "errors": errors,
    }
    print(json.dumps(output, indent=2, sort_keys=True, default=str))
    return 0 if not errors else 1


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--metadata-json", type=Path, help="JSON file containing TaskMetadata fields or {'metadata': ...}")
    source.add_argument("--task-class", help="Import path in module.path:ClassName form")
    parser.add_argument("--require-filled", action="store_true", help="Fail if metadata.is_filled() is false")
    parser.add_argument(
        "--require-descriptive-stats",
        action="store_true",
        help="Fail if descriptive statistics are not available for the metadata object",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        return validate(parse_args(sys.argv[1:] if argv is None else argv))
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "errors": [f"{exc.__class__.__name__}: {exc}"]}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
