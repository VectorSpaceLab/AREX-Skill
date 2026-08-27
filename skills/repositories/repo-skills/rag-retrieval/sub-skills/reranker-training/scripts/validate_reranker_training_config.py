#!/usr/bin/env python3
"""Validate RAG-Retrieval reranker training config and optional JSONL data.

This helper intentionally avoids importing RAG-Retrieval training modules,
Transformers, Accelerate, Torch, or model/tokenizer code. It performs static
checks only and never downloads models.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

POINTWISE_LOSSES = {"pointwise_bce", "pointwise_mse"}
GROUPED_LOSSES = {"pairwise_ranknet", "listwise_ce"}
ALL_LOSSES = POINTWISE_LOSSES | GROUPED_LOSSES
MODEL_TYPES = {"bert_encoder", "llm_decoder"}
DATASET_TYPES = {"pointwise", "grouped"}


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)

    def print(self) -> None:
        for message in self.errors:
            print(f"ERROR: {message}")
        for message in self.warnings:
            print(f"WARNING: {message}")
        for message in self.notes:
            print(f"OK: {message}")

    @property
    def ok(self) -> bool:
        return not self.errors


def strip_inline_comment(line: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_double:
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if char == "#" and not in_single and not in_double:
            return line[:index].rstrip()
    return line.rstrip()


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    lowered = value.lower()
    if lowered in {"none", "null", "~"}:
        return None
    if lowered in {"true", "yes", "on"}:
        return True
    if lowered in {"false", "no", "off"}:
        return False
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value[1:-1]
    if re.fullmatch(r"[-+]?\d+", value):
        try:
            return int(value)
        except ValueError:
            pass
    if re.fullmatch(r"[-+]?(?:\d+\.\d*|\d*\.\d+)(?:[eE][-+]?\d+)?", value) or re.fullmatch(
        r"[-+]?\d+[eE][-+]?\d+", value
    ):
        try:
            return float(value)
        except ValueError:
            pass
    return value


def fallback_yaml_load(path: Path) -> dict[str, Any]:
    config: dict[str, Any] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = strip_inline_comment(raw_line)
        if not line.strip():
            continue
        if line.startswith((" ", "\t", "-")):
            continue
        if ":" not in line:
            raise ValueError(f"cannot parse line {line_number}: {raw_line!r}")
        key, value = line.split(":", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"empty key on line {line_number}")
        config[key] = parse_scalar(value)
    return config


def load_config(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return fallback_yaml_load(path)

    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError("training config must be a YAML mapping")
    return dict(loaded)


def numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if math.isnan(float(value)) or math.isinf(float(value)):
            return None
        return float(value)
    if isinstance(value, str):
        try:
            parsed = float(value)
        except ValueError:
            return None
        if math.isnan(parsed) or math.isinf(parsed):
            return None
        return parsed
    return None


def as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        try:
            parsed = int(value)
        except ValueError:
            return None
        return parsed
    return None


def optional_path(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str) and value.strip().lower() in {"", "none", "null"}:
        return None
    return str(value)


def validate_config(config: dict[str, Any], reporter: Reporter) -> None:
    model_type = config.get("model_type")
    if model_type not in MODEL_TYPES:
        reporter.error(
            f"model_type must be one of {sorted(MODEL_TYPES)}, got {model_type!r}"
        )
    else:
        reporter.note(f"model_type={model_type}")

    train_dataset_type = config.get("train_dataset_type", "pointwise")
    if train_dataset_type not in DATASET_TYPES:
        reporter.error(
            f"train_dataset_type must be one of {sorted(DATASET_TYPES)}, got {train_dataset_type!r}"
        )
    else:
        reporter.note(f"train_dataset_type={train_dataset_type}")

    val_dataset_type = config.get("val_dataset_type", "pointwise")
    if optional_path(config.get("val_dataset")) and val_dataset_type not in DATASET_TYPES:
        reporter.error(
            f"val_dataset_type must be one of {sorted(DATASET_TYPES)}, got {val_dataset_type!r}"
        )

    loss_type = config.get("loss_type", "pointwise_bce")
    if loss_type not in ALL_LOSSES:
        reporter.error(
            f"loss_type must be one of {sorted(ALL_LOSSES)}, got {loss_type!r}"
        )
    elif train_dataset_type == "pointwise" and loss_type not in POINTWISE_LOSSES:
        reporter.error(
            f"loss_type={loss_type!r} requires train_dataset_type='grouped', not 'pointwise'"
        )
    elif train_dataset_type == "grouped" and loss_type not in GROUPED_LOSSES:
        reporter.error(
            f"loss_type={loss_type!r} requires train_dataset_type='pointwise', not 'grouped'"
        )
    else:
        reporter.note(f"loss_type={loss_type}")

    if train_dataset_type == "grouped":
        group_size = as_int(config.get("train_group_size", 8))
        if group_size is None or group_size < 2:
            reporter.error("train_group_size must be an integer >= 2 for grouped data")
        else:
            reporter.note(f"train_group_size={group_size}")

    min_label = numeric(config.get("min_label", 0))
    max_label = numeric(config.get("max_label", 1))
    if min_label is None or max_label is None:
        reporter.error("min_label and max_label must be numeric")
    elif min_label < 0 or max_label <= min_label:
        reporter.error("pointwise label scaling requires min_label >= 0 and max_label > min_label")

    shuffle_rate = numeric(config.get("shuffle_rate", 0.0))
    if shuffle_rate is None or not 0 <= shuffle_rate <= 1:
        reporter.error("shuffle_rate must be numeric and between 0 and 1")

    warmup = numeric(config.get("warmup_proportion", 0.1))
    stable = numeric(config.get("stable_proportion", 0.0))
    if warmup is None or stable is None:
        reporter.error("warmup_proportion and stable_proportion must be numeric")
    elif not (0 <= warmup <= 1 and 0 <= stable <= 1 and warmup + stable <= 1):
        reporter.error("warmup_proportion and stable_proportion must be in [0, 1] and sum to <= 1")

    if model_type == "llm_decoder":
        for field in ("query_format", "document_format"):
            value = str(config.get(field, "{}"))
            if "{}" not in value:
                reporter.warn(f"{field} does not contain '{{}}'; raw text may be dropped")
        if config.get("special_token", "") in {None, ""}:
            reporter.warn("llm_decoder special_token is empty; confirm this is intentional")

    mixed_precision = config.get("mixed_precision")
    if mixed_precision not in {None, "no", "fp16", "bf16", "fp8"}:
        reporter.warn(
            f"mixed_precision={mixed_precision!r} is unusual; ensure Accelerate supports it"
        )

    log_with = config.get("log_with")
    if log_with not in {None, "wandb", "tensorboard"}:
        reporter.warn(f"log_with={log_with!r} is unusual; ensure Accelerate tracker supports it")


def iter_jsonl(path: Path, reporter: Reporter):
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                reporter.error(f"line {line_number}: invalid JSON: {exc}")
                continue
            if not isinstance(value, dict):
                reporter.error(f"line {line_number}: JSONL record must be an object")
                continue
            yield line_number, value


def validate_pointwise_data(path: Path, config: dict[str, Any], reporter: Reporter) -> None:
    label_key = str(config.get("train_label_key", "label"))
    min_label = numeric(config.get("min_label", 0))
    max_label = numeric(config.get("max_label", 1))
    if min_label is None or max_label is None:
        min_label, max_label = 0.0, 1.0

    total = 0
    labels: list[float] = []
    missing = Counter()
    for line_number, record in iter_jsonl(path, reporter):
        total += 1
        for field in ("query", "content"):
            if field not in record or not isinstance(record[field], str):
                reporter.error(f"line {line_number}: pointwise record needs string field {field!r}")
                missing[field] += 1
        if "hits" in record:
            reporter.warn(f"line {line_number}: record has 'hits' but config says pointwise")
        if label_key not in record:
            reporter.error(f"line {line_number}: missing label field {label_key!r}")
            missing[label_key] += 1
            continue
        label = numeric(record[label_key])
        if label is None:
            reporter.error(f"line {line_number}: label field {label_key!r} must be numeric")
            continue
        labels.append(label)
        if label < min_label or label > max_label:
            reporter.error(
                f"line {line_number}: label {label:g} outside configured range [{min_label:g}, {max_label:g}]"
            )

    if total == 0:
        reporter.error(f"{path}: no JSONL records found")
        return

    reporter.note(f"pointwise records={total}, label_key={label_key!r}")
    if labels:
        reporter.note(
            f"pointwise label range observed=[{min(labels):g}, {max(labels):g}], unique={len(set(labels))}"
        )
        if len(set(labels)) == 1:
            reporter.warn("all pointwise labels are identical; training may not learn ranking behavior")
    if missing:
        reporter.warn(f"missing field counts: {dict(missing)}")


def chunk_count(hit_count: int, group_size: int) -> int:
    if hit_count < group_size:
        return 0
    return math.ceil(hit_count / group_size)


def validate_grouped_data(path: Path, config: dict[str, Any], reporter: Reporter) -> None:
    label_key = str(config.get("train_label_key", "label"))
    group_size = as_int(config.get("train_group_size", 8)) or 8
    loss_type = config.get("loss_type", "pairwise_ranknet")

    records = 0
    hits_total = 0
    undersized_records = 0
    all_identical_records = 0
    deterministic_groups = 0
    deterministic_identical_groups = 0
    no_positive_groups = 0
    multi_positive_groups = 0
    label_values: list[float] = []

    for line_number, record in iter_jsonl(path, reporter):
        records += 1
        if "content" in record:
            reporter.warn(f"line {line_number}: record has 'content' but config says grouped")
        if "query" not in record or not isinstance(record["query"], str):
            reporter.error(f"line {line_number}: grouped record needs string field 'query'")
        hits = record.get("hits")
        if not isinstance(hits, list):
            reporter.error(f"line {line_number}: grouped record needs list field 'hits'")
            continue
        hits_total += len(hits)
        if len(hits) < group_size:
            undersized_records += 1
        record_labels: list[float] = []
        for hit_index, hit in enumerate(hits):
            if not isinstance(hit, dict):
                reporter.error(f"line {line_number} hit {hit_index}: hit must be an object")
                continue
            if "content" not in hit or not isinstance(hit["content"], str):
                reporter.error(f"line {line_number} hit {hit_index}: hit needs string field 'content'")
            if label_key not in hit:
                reporter.error(f"line {line_number} hit {hit_index}: missing label field {label_key!r}")
                continue
            label = numeric(hit[label_key])
            if label is None:
                reporter.error(f"line {line_number} hit {hit_index}: label field {label_key!r} must be numeric")
                continue
            record_labels.append(label)
            label_values.append(label)

        if record_labels and len(set(record_labels)) == 1:
            all_identical_records += 1

        if len(hits) >= group_size:
            deterministic_groups += chunk_count(len(hits), group_size)
            for start in range(0, len(record_labels), group_size):
                group_labels = record_labels[start : start + group_size]
                if not group_labels:
                    continue
                if len(group_labels) < group_size:
                    group_labels = group_labels + record_labels[: group_size - len(group_labels)]
                if len(set(group_labels)) == 1:
                    deterministic_identical_groups += 1
                positive_count = sum(1 for label in group_labels if label != 0)
                if positive_count == 0:
                    no_positive_groups += 1
                elif positive_count > 1:
                    multi_positive_groups += 1

    if records == 0:
        reporter.error(f"{path}: no JSONL records found")
        return

    reporter.note(
        f"grouped records={records}, hits={hits_total}, label_key={label_key!r}, train_group_size={group_size}"
    )
    if label_values:
        reporter.note(
            f"grouped label range observed=[{min(label_values):g}, {max(label_values):g}], unique={len(set(label_values))}"
        )
    if undersized_records:
        reporter.warn(
            f"{undersized_records}/{records} grouped records have fewer hits than train_group_size and will be skipped"
        )
    if all_identical_records:
        reporter.warn(
            f"{all_identical_records}/{records} grouped records have only one distinct label and cannot produce useful groups"
        )
    if deterministic_identical_groups:
        reporter.warn(
            f"{deterministic_identical_groups}/{deterministic_groups} deterministic chunks have identical labels; shuffled training may skip similar groups"
        )
    surviving_estimate = max(deterministic_groups - deterministic_identical_groups, 0)
    reporter.note(
        f"deterministic grouped chunks={deterministic_groups}, estimated non-identical chunks={surviving_estimate}"
    )
    if deterministic_groups == 0 or surviving_estimate == 0:
        reporter.error("grouped data appears to produce no trainable non-identical groups")

    if loss_type == "listwise_ce":
        if no_positive_groups:
            reporter.warn(
                f"{no_positive_groups} deterministic groups have no non-zero positive labels for listwise_ce"
            )
        if multi_positive_groups:
            reporter.warn(
                f"{multi_positive_groups} deterministic groups have multiple non-zero labels; README recommends exactly one positive for listwise_ce"
            )


def resolve_data_path(config_path: Path, config: dict[str, Any], data_arg: str | None) -> Path | None:
    if data_arg:
        return Path(data_arg).expanduser()
    train_dataset = optional_path(config.get("train_dataset"))
    if not train_dataset:
        return None
    path = Path(train_dataset).expanduser()
    if path.is_absolute() or path.exists():
        return path
    config_relative = config_path.parent / path
    if config_relative.exists():
        return config_relative
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate RAG-Retrieval reranker training YAML and optional JSONL data."
    )
    parser.add_argument("--config", required=True, help="training YAML file")
    parser.add_argument("--data", help="optional JSONL data path; overrides train_dataset")
    args = parser.parse_args(argv)

    reporter = Reporter()
    config_path = Path(args.config).expanduser()
    if not config_path.exists():
        print(f"ERROR: config file not found: {config_path}")
        return 2

    try:
        config = load_config(config_path)
    except Exception as exc:  # noqa: BLE001 - show concise CLI error
        print(f"ERROR: failed to read config: {exc}")
        return 2

    validate_config(config, reporter)

    data_path = resolve_data_path(config_path, config, args.data)
    if data_path is None:
        reporter.warn("no --data provided and config has no train_dataset; skipped JSONL validation")
    elif not data_path.exists():
        reporter.error(f"data file not found: {data_path}")
    else:
        train_dataset_type = config.get("train_dataset_type", "pointwise")
        if train_dataset_type == "pointwise":
            validate_pointwise_data(data_path, config, reporter)
        elif train_dataset_type == "grouped":
            validate_grouped_data(data_path, config, reporter)

    reporter.print()
    if reporter.ok:
        print("Validation passed.")
        return 0
    print("Validation failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
