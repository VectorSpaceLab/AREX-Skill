#!/usr/bin/env python3
"""Validate RAG-Retrieval embedding training YAML, JSONL, and teacher arrays.

This helper is intentionally local and safe: it does not import RAG-Retrieval,
torch, transformers, sentence-transformers, or accelerate, and it never downloads
models. It uses PyYAML for YAML parsing and NumPy only when validating .npy
teacher arrays.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any

FLOAT32_BYTES = 4

KNOWN_CONFIG_KEYS = {
    "model_name_or_path",
    "train_type",
    "train_dataset",
    "train_dataset_vec",
    "val_dataset",
    "shuffle",
    "neg_nums",
    "query_max_len",
    "passage_max_len",
    "teacher_embedding_dim",
    "teacher_emebedding_dim",
    "output_dir",
    "save_on_epoch_end",
    "num_max_checkpoints",
    "epochs",
    "lr",
    "batch_size",
    "seed",
    "warmup_proportion",
    "temperature",
    "mixed_precision",
    "gradient_accumulation_steps",
    "gradient_checkpointing",
    "all_gather",
    "log_with",
    "log_interval",
    "eval_steps",
    "save_steps",
    "use_mrl",
    "mrl_dims",
}

POSITIVE_INT_KEYS = {
    "neg_nums",
    "query_max_len",
    "passage_max_len",
    "teacher_embedding_dim",
    "teacher_emebedding_dim",
    "num_max_checkpoints",
    "epochs",
    "batch_size",
    "gradient_accumulation_steps",
    "log_interval",
}
NON_NEGATIVE_INT_KEYS = {"seed", "eval_steps", "save_steps"}
FLOAT_KEYS = {"lr", "warmup_proportion", "temperature"}
BOOL_KEYS = {"shuffle", "gradient_checkpointing", "all_gather", "use_mrl"}


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely validate RAG-Retrieval embedding training config/data without launching training."
    )
    parser.add_argument("--config", required=True, help="Path to training_embedding.yaml or distill_embedding.yaml")
    parser.add_argument("--data", help="Optional JSONL dataset path to validate")
    parser.add_argument("--teacher-embeddings", help="Optional teacher embedding .mmap/raw-float32 or .npy path")
    parser.add_argument("--max-errors", type=int, default=30, help="Stop detailed JSONL validation after this many errors")
    return parser.parse_args()


def strip_inline_comment(value: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(value):
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
            return value[:index].rstrip()
    return value.rstrip()


def parse_simple_scalar(value: str) -> Any:
    stripped = strip_inline_comment(value).strip()
    if stripped == "":
        return ""
    if (stripped.startswith('"') and stripped.endswith('"')) or (stripped.startswith("'") and stripped.endswith("'")):
        return stripped[1:-1]
    lowered = stripped.lower()
    if lowered in {"true", "yes", "on"}:
        return True
    if lowered in {"false", "no", "off"}:
        return False
    if lowered in {"null", "none", "~"}:
        return None
    try:
        return int(stripped)
    except ValueError:
        pass
    try:
        return float(stripped)
    except ValueError:
        return stripped


def load_simple_flat_yaml(path: str, report: Report) -> dict[str, Any]:
    loaded: dict[str, Any] = {}
    with open(path, "r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if raw_line[:1].isspace():
                report.error(
                    f"line {line_no}: config uses nested or indented YAML; install PyYAML for full YAML parsing."
                )
                return {}
            if ":" not in raw_line:
                report.error(f"line {line_no}: cannot parse flat YAML line without ':'.")
                return {}
            key, raw_value = raw_line.split(":", 1)
            key = key.strip()
            if not key:
                report.error(f"line {line_no}: empty YAML key.")
                return {}
            loaded[key] = parse_simple_scalar(raw_value)
    report.warn("PyYAML is not installed; used a conservative flat-YAML parser suitable for simple training configs.")
    return loaded


def load_yaml_config(path: str, report: Report) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        try:
            return load_simple_flat_yaml(path, report)
        except FileNotFoundError:
            report.error(f"Config file not found: {path}")
            return {}
        except Exception as exc:  # noqa: BLE001 - report parser details without traceback noise.
            report.error(f"Could not parse YAML config {path} with fallback parser: {exc}")
            return {}

    try:
        with open(path, "r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle)
    except FileNotFoundError:
        report.error(f"Config file not found: {path}")
        return {}
    except Exception as exc:  # noqa: BLE001 - report parser details without traceback noise.
        report.error(f"Could not parse YAML config {path}: {exc}")
        return {}

    if not isinstance(loaded, dict):
        report.error("YAML config must parse to a mapping/object at the top level.")
        return {}
    return loaded


def as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y", "on"}:
            return True
        if lowered in {"false", "0", "no", "n", "off"}:
            return False
    return None


def as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def parse_mrl_dims(value: Any, report: Report) -> list[int]:
    if value is None:
        return []
    if not isinstance(value, str):
        report.error("mrl_dims must be a comma-separated string because train_embedding.py calls mrl_dims.split(',').")
        return []

    dims: list[int] = []
    for raw_part in value.split(","):
        part = raw_part.strip()
        if not part:
            continue
        try:
            dim = int(part)
        except ValueError:
            report.error(f"mrl_dims contains a non-integer value: {part!r}")
            continue
        if dim <= 0:
            report.error(f"mrl_dims values must be positive integers; got {dim}.")
        dims.append(dim)

    if len(set(dims)) != len(dims):
        report.warn("mrl_dims contains duplicate dimensions; training will repeat loss work for duplicates.")
    if dims and dims != sorted(dims):
        report.warn("mrl_dims is not sorted increasingly; this is allowed but harder to audit.")
    return dims


def effective_teacher_dim(config: dict[str, Any], report: Report) -> int | None:
    correct = config.get("teacher_embedding_dim")
    typo = config.get("teacher_emebedding_dim")
    correct_dim = as_int(correct) if correct is not None else None
    typo_dim = as_int(typo) if typo is not None else None

    if correct is not None and correct_dim is None:
        report.error("teacher_embedding_dim must be a positive integer when set.")
    if typo is not None and typo_dim is None:
        report.error("teacher_emebedding_dim must be a positive integer when set.")
    if correct_dim is not None and correct_dim <= 0:
        report.error("teacher_embedding_dim must be positive.")
    if typo_dim is not None and typo_dim <= 0:
        report.error("teacher_emebedding_dim must be positive.")
    if correct_dim is not None and typo_dim is not None and correct_dim != typo_dim:
        report.error("teacher_embedding_dim and teacher_emebedding_dim are both set but differ.")
    if correct_dim is not None:
        return correct_dim
    if typo_dim is not None:
        report.warn("Using compatibility typo teacher_emebedding_dim; prefer teacher_embedding_dim in new configs.")
        return typo_dim
    return None


def validate_config(config: dict[str, Any], report: Report) -> tuple[str, int | None, list[int]]:
    for key in sorted(set(config) - KNOWN_CONFIG_KEYS):
        report.warn(f"Unknown YAML key {key!r}; train_embedding.py will accept it but may ignore or mis-handle it.")

    train_type = config.get("train_type", "train")
    if "train_type" not in config:
        report.warn("train_type is missing; source parser default is 'train'.")
    if train_type not in {"train", "distill"}:
        report.error("train_type must be either 'train' or 'distill'.")
        train_type = str(train_type)

    for key in POSITIVE_INT_KEYS:
        if key in config:
            value = as_int(config[key])
            if value is None or value <= 0:
                report.error(f"{key} must be a positive integer.")
    for key in NON_NEGATIVE_INT_KEYS:
        if key in config and config[key] is not None:
            value = as_int(config[key])
            if value is None or value < 0:
                report.error(f"{key} must be a non-negative integer or null.")
    for key in FLOAT_KEYS:
        if key in config:
            value = as_float(config[key])
            if value is None:
                report.error(f"{key} must be numeric.")
    for key in BOOL_KEYS:
        if key in config and as_bool(config[key]) is None:
            report.error(f"{key} must be a boolean-like value.")

    warmup = as_float(config.get("warmup_proportion", 0.05))
    if warmup is not None and not (0 <= warmup < 1):
        report.error("warmup_proportion must satisfy 0 <= warmup_proportion < 1.")

    for required_key in ("train_dataset", "output_dir", "batch_size"):
        if required_key not in config or config.get(required_key) in (None, ""):
            report.error(f"{required_key} is required for a practical training launch.")

    if train_type == "distill" and not config.get("train_dataset_vec"):
        report.error("train_dataset_vec is required when train_type is 'distill'.")

    teacher_dim = effective_teacher_dim(config, report)
    if train_type == "distill" and teacher_dim is None:
        report.error("teacher_embedding_dim is required when train_type is 'distill'.")

    use_mrl = as_bool(config.get("use_mrl", False)) is True
    mrl_dims = parse_mrl_dims(config.get("mrl_dims"), report)
    if use_mrl and not mrl_dims:
        report.error("use_mrl is true but mrl_dims is empty or invalid.")
    if train_type == "distill" and use_mrl and teacher_dim is not None and mrl_dims and max(mrl_dims) > teacher_dim:
        report.error("For distillation, max(mrl_dims) must be <= teacher_embedding_dim.")

    log_with = config.get("log_with")
    if log_with not in (None, "", "wandb", "tensorboard"):
        report.warn("log_with is not 'wandb', 'tensorboard', empty, or null; confirm Accelerate supports it.")

    mixed_precision = config.get("mixed_precision")
    if mixed_precision not in (None, "no", "fp16", "bf16", "fp8"):
        report.warn("mixed_precision is unusual; common Accelerate values are 'no', 'fp16', and 'bf16'.")

    return str(train_type), teacher_dim, mrl_dims


def is_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def validate_train_record(obj: dict[str, Any], line_no: int, neg_nums: int | None, report: Report) -> str | None:
    if "query" not in obj or not isinstance(obj["query"], str):
        report.error(f"line {line_no}: query must be a string.")
        return None
    if "prompt_for_query" in obj and obj["prompt_for_query"] is not None and not isinstance(obj["prompt_for_query"], str):
        report.error(f"line {line_no}: prompt_for_query must be a string when present.")

    if "score" in obj and "scores" not in obj:
        report.error(f"line {line_no}: raw pair-score data should use list-valued 'scores', not singular 'score'.")

    if "pos" not in obj:
        report.error(f"line {line_no}: train records must include non-empty list field 'pos'.")
        return None
    if not is_string_list(obj.get("pos")):
        report.error(f"line {line_no}: pos must be a non-empty list of strings.")
        return None

    has_neg = "neg" in obj
    has_scores = "scores" in obj
    if has_neg and has_scores:
        report.error(f"line {line_no}: do not mix neg and scores; source data.py will ignore scores in the triplet branch.")
        return None

    if has_scores:
        scores = obj.get("scores")
        if not isinstance(scores, list) or not scores:
            report.error(f"line {line_no}: scores must be a non-empty list of numbers.")
            return None
        if len(scores) != len(obj["pos"]):
            report.error(f"line {line_no}: scores length ({len(scores)}) must equal pos length ({len(obj['pos'])}).")
            return None
        if not all(isinstance(score, (int, float)) and not isinstance(score, bool) for score in scores):
            report.error(f"line {line_no}: every scores entry must be numeric.")
            return None
        return "pair_score"

    if has_neg:
        neg = obj.get("neg")
        if not is_string_list(neg):
            report.error(f"line {line_no}: neg must be a non-empty list of strings.")
            return None
        if neg_nums is not None and len(neg) < neg_nums:
            report.warn(
                f"line {line_no}: neg has {len(neg)} entries but neg_nums is {neg_nums}; source code will resample repeated negatives."
            )
        return "triplet"

    return "pair"


def validate_distill_record(obj: dict[str, Any], line_no: int, report: Report) -> str | None:
    if "query" not in obj or not isinstance(obj["query"], str):
        report.error(f"line {line_no}: distillation records must include string field 'query'.")
        return None
    if "prompt_for_query" in obj and obj["prompt_for_query"] is not None and not isinstance(obj["prompt_for_query"], str):
        report.error(f"line {line_no}: prompt_for_query must be a string when present.")
    ignored = sorted(set(obj) & {"pos", "neg", "scores", "score"})
    if ignored:
        report.warn(f"line {line_no}: distillation dataset ignores fields {ignored}; confirm row count matches teacher embeddings.")
    return "distill"


def validate_jsonl(path: str, train_type: str, neg_nums: int | None, max_errors: int, report: Report) -> tuple[int, str | None, int]:
    line_count = 0
    expanded_count = 0
    schema: str | None = None
    prompt_count = 0

    try:
        handle = open(path, "r", encoding="utf-8")
    except FileNotFoundError:
        report.error(f"Data file not found: {path}")
        return 0, None, 0

    with handle:
        for line_no, raw_line in enumerate(handle, start=1):
            stripped = raw_line.strip()
            if not stripped:
                report.warn(f"line {line_no}: blank line ignored by validator but source json.loads would fail; remove it.")
                continue
            line_count += 1
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as exc:
                report.error(f"line {line_no}: invalid JSON: {exc}")
                if len(report.errors) >= max_errors:
                    break
                continue
            if not isinstance(obj, dict):
                report.error(f"line {line_no}: JSONL row must be an object.")
                if len(report.errors) >= max_errors:
                    break
                continue

            if obj.get("prompt_for_query"):
                prompt_count += 1

            row_schema = (
                validate_distill_record(obj, line_no, report)
                if train_type == "distill"
                else validate_train_record(obj, line_no, neg_nums, report)
            )
            if row_schema and schema is None:
                schema = row_schema
            elif row_schema and row_schema != schema and train_type != "distill":
                report.error(
                    f"line {line_no}: mixed training schemas ({schema} and {row_schema}) are unsafe because source collate_fn is chosen from the first expanded record."
                )

            if row_schema == "distill":
                expanded_count += 1
            elif row_schema in {"pair", "triplet", "pair_score"}:
                pos = obj.get("pos")
                expanded_count += len(pos) if isinstance(pos, list) else 0

            if len(report.errors) >= max_errors:
                report.warn(f"Stopped detailed JSONL validation after reaching --max-errors={max_errors}.")
                break

    if line_count == 0:
        report.error("Data file has no non-blank JSONL records.")
    if prompt_count:
        report.note(f"prompt_for_query is present and non-empty on {prompt_count} JSONL row(s); source code prepends it to query.")
    if schema:
        report.note(f"Detected dataset schema: {schema}; JSONL rows: {line_count}; expanded training rows: {expanded_count}.")
    return line_count, schema, expanded_count


def validate_teacher_embeddings(path: str, rows: int | None, teacher_dim: int | None, report: Report) -> None:
    if teacher_dim is None:
        report.error("Cannot validate teacher embeddings without teacher_embedding_dim.")
        return
    if teacher_dim <= 0:
        report.error("Cannot validate teacher embeddings because teacher_embedding_dim is not positive.")
        return
    if not os.path.exists(path):
        report.error(f"Teacher embedding file not found: {path}")
        return

    if path.endswith(".npy"):
        try:
            import numpy as np  # type: ignore
        except ImportError:
            report.error("NumPy is required to validate .npy teacher arrays. Install numpy or provide a raw memmap file.")
            return
        try:
            array = np.load(path, mmap_mode="r")
        except Exception as exc:  # noqa: BLE001
            report.error(f"Could not open .npy teacher array {path}: {exc}")
            return
        if len(array.shape) != 2:
            report.error(f"Teacher .npy array must be 2D; got shape {array.shape}.")
            return
        if rows is not None and array.shape[0] != rows:
            report.error(f"Teacher .npy row count {array.shape[0]} does not match JSONL row count {rows}.")
        if array.shape[1] != teacher_dim:
            report.error(f"Teacher .npy dimension {array.shape[1]} does not match teacher_embedding_dim {teacher_dim}.")
        if str(array.dtype) != "float32":
            report.error(f"Teacher .npy dtype must be float32 for source distillation; got {array.dtype}.")
        report.note(f"Teacher .npy shape: {tuple(array.shape)}, dtype: {array.dtype}.")
        return

    size = os.path.getsize(path)
    row_bytes = teacher_dim * FLOAT32_BYTES
    if rows is not None and rows > 0:
        expected_size = rows * row_bytes
        if size != expected_size:
            report.error(
                f"Raw teacher memmap size mismatch: got {size} bytes, expected {expected_size} bytes for rows={rows}, dim={teacher_dim}, float32."
            )
        else:
            report.note(f"Raw teacher memmap size matches rows={rows}, dim={teacher_dim}, dtype=float32.")
    elif size % row_bytes != 0:
        report.error(
            f"Raw teacher memmap size {size} is not divisible by teacher_embedding_dim * 4 ({row_bytes}); cannot infer row count."
        )
    else:
        inferred_rows = size // row_bytes
        report.note(f"Raw teacher memmap can be interpreted as rows={inferred_rows}, dim={teacher_dim}, dtype=float32.")


def print_report(report: Report) -> None:
    if report.notes:
        print("Notes:")
        for message in report.notes:
            print(f"  - {message}")
    if report.warnings:
        print("Warnings:")
        for message in report.warnings:
            print(f"  - {message}")
    if report.errors:
        print("Errors:")
        for message in report.errors:
            print(f"  - {message}")


def main() -> int:
    args = parse_args()
    report = Report()

    config = load_yaml_config(args.config, report)
    if config:
        train_type, teacher_dim, _mrl_dims = validate_config(config, report)
    else:
        train_type, teacher_dim = "train", None

    line_count: int | None = None
    neg_nums = as_int(config.get("neg_nums", 15)) if config else 15
    if neg_nums is not None and neg_nums <= 0:
        neg_nums = None

    if args.data:
        line_count, _schema, _expanded = validate_jsonl(args.data, train_type, neg_nums, args.max_errors, report)

    if args.teacher_embeddings:
        if train_type != "distill":
            report.warn("--teacher-embeddings was supplied but train_type is not 'distill'.")
        validate_teacher_embeddings(args.teacher_embeddings, line_count, teacher_dim, report)

    print_report(report)
    if report.errors:
        print(f"Validation failed with {len(report.errors)} error(s).", file=sys.stderr)
        return 1
    print("Validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
