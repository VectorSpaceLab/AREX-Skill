#!/usr/bin/env python3
"""Validate Spleeter training JSON configs and CSV manifests.

This helper is pure Python and does not import Spleeter. It checks the source-
derived data/config rules that should be satisfied before running
`python -m spleeter train`.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

REQUIRED_TOP_LEVEL_KEYS = [
    "train_csv",
    "validation_csv",
    "model_dir",
    "mix_name",
    "instrument_list",
    "sample_rate",
    "frame_length",
    "frame_step",
    "T",
    "F",
    "n_channels",
    "n_chunks_per_song",
    "separation_exponent",
    "mask_extension",
    "learning_rate",
    "batch_size",
    "train_max_steps",
    "throttle_secs",
    "save_checkpoints_steps",
    "save_summary_steps",
    "random_seed",
    "model",
]

POSITIVE_INT_KEYS = [
    "sample_rate",
    "frame_length",
    "frame_step",
    "T",
    "F",
    "n_channels",
    "n_chunks_per_song",
    "batch_size",
    "train_max_steps",
    "throttle_secs",
    "save_checkpoints_steps",
    "save_summary_steps",
]

POSITIVE_NUMBER_KEYS = ["separation_exponent", "learning_rate"]
KNOWN_MODEL_TYPES = {"unet.unet", "unet.softmax_unet"}
VALID_MASK_EXTENSIONS = {"zeros", "average"}


class Reporter:
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a Spleeter training config JSON and its train/validation "
            "CSVs before running `python -m spleeter train`."
        )
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Spleeter training JSON config to validate.",
    )
    parser.add_argument(
        "--data",
        required=True,
        help="DATA_ROOT passed to `spleeter train --data/-d`.",
    )
    parser.add_argument(
        "--csv-base",
        choices=("auto", "config", "data", "cwd"),
        default="auto",
        help=(
            "How to resolve relative train_csv/validation_csv paths. "
            "auto tries config directory, data root, then current working directory."
        ),
    )
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Return non-zero when warnings are present.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print errors and warnings.",
    )
    return parser.parse_args(argv)


def load_json(path: Path, reporter: Reporter) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        reporter.error(f"config file does not exist: {path}")
        return {}
    except json.JSONDecodeError as exc:
        reporter.error(f"config is not valid JSON: {path}: {exc}")
        return {}
    if not isinstance(data, dict):
        reporter.error("config root must be a JSON object")
        return {}
    return data


def as_positive_int(config: Dict[str, Any], key: str, reporter: Reporter) -> int | None:
    value = config.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        reporter.error(f"{key} must be a positive integer; got {value!r}")
        return None
    if value <= 0:
        reporter.error(f"{key} must be > 0; got {value!r}")
        return None
    return value


def as_positive_number(config: Dict[str, Any], key: str, reporter: Reporter) -> float | None:
    value = config.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        reporter.error(f"{key} must be a positive number; got {value!r}")
        return None
    if not math.isfinite(float(value)) or float(value) <= 0:
        reporter.error(f"{key} must be finite and > 0; got {value!r}")
        return None
    return float(value)


def validate_top_level(config: Dict[str, Any], reporter: Reporter) -> None:
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in config:
            reporter.error(f"missing required config key: {key}")

    for key in POSITIVE_INT_KEYS:
        if key in config:
            as_positive_int(config, key, reporter)

    for key in POSITIVE_NUMBER_KEYS:
        if key in config:
            as_positive_number(config, key, reporter)

    if "chunk_duration" not in config:
        reporter.warn("chunk_duration is absent; get_training_dataset will default to 20.0 seconds")
    elif config.get("chunk_duration") is None:
        reporter.error("chunk_duration must not be null when present; omit it or set a positive number")
    elif as_positive_number(config, "chunk_duration", reporter) is None:
        pass

    for cache_key in ("training_cache", "validation_cache"):
        if cache_key not in config:
            reporter.warn(f"{cache_key} is absent; dataset caching will be disabled for that split")
        elif not isinstance(config.get(cache_key), str) or not config.get(cache_key):
            reporter.error(f"{cache_key} must be a non-empty string when present")

    if config.get("mask_extension") not in VALID_MASK_EXTENSIONS and "mask_extension" in config:
        reporter.error(
            f"mask_extension must be one of {sorted(VALID_MASK_EXTENSIONS)}; got {config.get('mask_extension')!r}"
        )

    model = config.get("model")
    if not isinstance(model, dict):
        if "model" in config:
            reporter.error("model must be an object with type and params")
        return
    model_type = model.get("type")
    if not isinstance(model_type, str) or not model_type:
        reporter.error("model.type must be a non-empty string such as 'unet.unet'")
    elif model_type not in KNOWN_MODEL_TYPES:
        reporter.warn(
            f"model.type {model_type!r} is not one of the evidence-backed built-ins {sorted(KNOWN_MODEL_TYPES)}; "
            "ensure it is importable under spleeter.model.functions"
        )
    if "params" not in model:
        reporter.error("model.params is required, even when empty")
    elif not isinstance(model.get("params"), dict):
        reporter.error("model.params must be an object")


def validate_instruments(config: Dict[str, Any], reporter: Reporter) -> Tuple[str | None, List[str]]:
    mix_name = config.get("mix_name")
    instruments = config.get("instrument_list")
    if not isinstance(mix_name, str) or not mix_name:
        reporter.error("mix_name must be a non-empty string")
        mix_name = None
    if not isinstance(instruments, list) or not instruments:
        reporter.error("instrument_list must be a non-empty list of strings")
        return mix_name, []
    normalized: List[str] = []
    seen = set()
    for index, instrument in enumerate(instruments):
        if not isinstance(instrument, str) or not instrument:
            reporter.error(f"instrument_list[{index}] must be a non-empty string")
            continue
        if instrument in seen:
            reporter.error(f"instrument_list contains duplicate instrument {instrument!r}")
        seen.add(instrument)
        normalized.append(instrument)
    if mix_name and mix_name in seen:
        reporter.error(f"mix_name {mix_name!r} must not also appear in instrument_list")
    return mix_name, normalized


def validate_dimensions(config: Dict[str, Any], reporter: Reporter) -> None:
    frame_length = config.get("frame_length")
    frame_step = config.get("frame_step")
    sample_rate = config.get("sample_rate")
    T = config.get("T")
    F = config.get("F")

    if all(isinstance(config.get(k), int) and not isinstance(config.get(k), bool) for k in ("frame_length", "F")):
        max_f = frame_length // 2 + 1
        if F > max_f:
            reporter.error(
                f"F={F} is too large for frame_length={frame_length}; set F <= frame_length/2+1 ({max_f})"
            )

    if all(
        isinstance(config.get(k), int) and not isinstance(config.get(k), bool)
        for k in ("sample_rate", "frame_length", "frame_step", "T")
    ):
        chunk_duration = config.get("chunk_duration", 20.0)
        if isinstance(chunk_duration, (int, float)) and not isinstance(chunk_duration, bool) and chunk_duration > 0:
            available_frames = (float(chunk_duration) * sample_rate - frame_length) / frame_step
            if available_frames < T:
                required_seconds = (T * frame_step + frame_length) / sample_rate
                reporter.error(
                    f"T={T} is too large for training chunk_duration={chunk_duration}, "
                    f"sample_rate={sample_rate}, frame_length={frame_length}, frame_step={frame_step}; "
                    f"use chunk_duration >= {required_seconds:.6f}s or reduce T/frame settings"
                )

    if isinstance(config.get("n_channels"), int) and config.get("n_channels") not in (1, 2):
        reporter.warn(
            f"n_channels={config.get('n_channels')} is unusual for Spleeter examples; confirm adapter output and model intent"
        )


def csv_resolution_candidates(raw_path: str, config_path: Path, data_root: Path, csv_base: str) -> List[Path]:
    path = Path(raw_path)
    if path.is_absolute():
        return [path]
    if csv_base == "config":
        return [config_path.parent / path]
    if csv_base == "data":
        return [data_root / path]
    if csv_base == "cwd":
        return [Path.cwd() / path]
    return [config_path.parent / path, data_root / path, Path.cwd() / path]


def resolve_csv_path(raw_path: Any, label: str, config_path: Path, data_root: Path, csv_base: str, reporter: Reporter) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path:
        reporter.error(f"{label} must be a non-empty string path; got {raw_path!r}")
        return None
    candidates = csv_resolution_candidates(raw_path, config_path, data_root, csv_base)
    for candidate in candidates:
        if candidate.exists():
            if not candidate.is_file():
                reporter.error(f"{label} resolves to a non-file path: {candidate}")
                return None
            return candidate
    formatted = ", ".join(str(candidate) for candidate in candidates)
    reporter.error(f"{label} not found; tried: {formatted}")
    return None


def safe_join_under_data(data_root: Path, raw_value: str, row_number: int, column: str, reporter: Reporter) -> Path | None:
    if not raw_value:
        reporter.error(f"row {row_number}: {column} is empty")
        return None
    rel_path = Path(raw_value)
    if rel_path.is_absolute():
        reporter.error(f"row {row_number}: {column} must be relative to --data, got absolute path {raw_value!r}")
        return None
    candidate = (data_root / rel_path).resolve()
    try:
        candidate.relative_to(data_root.resolve())
    except ValueError:
        reporter.error(f"row {row_number}: {column} escapes --data root: {raw_value!r}")
        return None
    if not candidate.exists():
        reporter.error(f"row {row_number}: {column} file does not exist under --data: {raw_value!r}")
        return None
    if not candidate.is_file():
        reporter.error(f"row {row_number}: {column} is not a file under --data: {raw_value!r}")
        return None
    return candidate


def minimum_audio_seconds(config: Dict[str, Any]) -> float | None:
    needed = ["T", "frame_step", "frame_length", "sample_rate"]
    if not all(isinstance(config.get(k), int) and not isinstance(config.get(k), bool) and config.get(k) > 0 for k in needed):
        return None
    return (config["T"] * config["frame_step"] + config["frame_length"]) / config["sample_rate"]


def validate_csv(
    csv_path: Path,
    label: str,
    data_root: Path,
    mix_name: str | None,
    instruments: List[str],
    config: Dict[str, Any],
    reporter: Reporter,
) -> None:
    try:
        with csv_path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames or []
            required_columns: List[str] = []
            if mix_name:
                required_columns.append(f"{mix_name}_path")
            required_columns.extend(f"{instrument}_path" for instrument in instruments)
            required_columns.append("duration")

            for column in required_columns:
                if column not in fieldnames:
                    reporter.error(f"{label}: missing required CSV column: {column}")

            min_seconds = minimum_audio_seconds(config)
            row_count = 0
            for row_count, row in enumerate(reader, start=2):
                for column in required_columns:
                    if column.endswith("_path") and column in row:
                        safe_join_under_data(data_root, row.get(column, ""), row_count, column, reporter)
                raw_duration = row.get("duration")
                try:
                    duration = float(raw_duration) if raw_duration not in (None, "") else float("nan")
                except ValueError:
                    reporter.error(f"{label}: row {row_count}: duration must be numeric, got {raw_duration!r}")
                    continue
                if not math.isfinite(duration) or duration <= 0:
                    reporter.error(f"{label}: row {row_count}: duration must be finite and > 0, got {raw_duration!r}")
                    continue
                if min_seconds is not None and duration < min_seconds:
                    reporter.error(
                        f"{label}: row {row_count}: duration {duration:g}s is shorter than the minimum "
                        f"{min_seconds:.6f}s implied by T/frame_step/frame_length/sample_rate"
                    )
                chunk_duration = config.get("chunk_duration")
                if isinstance(chunk_duration, (int, float)) and not isinstance(chunk_duration, bool):
                    if duration < float(chunk_duration):
                        reporter.warn(
                            f"{label}: row {row_count}: duration {duration:g}s is shorter than training "
                            f"chunk_duration {float(chunk_duration):g}s; Spleeter may load a shorter segment and filter it"
                        )

            if row_count == 0:
                reporter.error(f"{label}: CSV has no data rows")
    except OSError as exc:
        reporter.error(f"{label}: could not read CSV {csv_path}: {exc}")


def validate_paths(config: Dict[str, Any], config_path: Path, data_root: Path, csv_base: str, reporter: Reporter) -> None:
    if not data_root.exists():
        reporter.error(f"--data root does not exist: {data_root}")
        return
    if not data_root.is_dir():
        reporter.error(f"--data root is not a directory: {data_root}")
        return

    mix_name, instruments = validate_instruments(config, reporter)
    train_csv = resolve_csv_path(config.get("train_csv"), "train_csv", config_path, data_root, csv_base, reporter)
    validation_csv = resolve_csv_path(
        config.get("validation_csv"), "validation_csv", config_path, data_root, csv_base, reporter
    )
    if train_csv is not None:
        validate_csv(train_csv, "train_csv", data_root, mix_name, instruments, config, reporter)
    if validation_csv is not None:
        validate_csv(validation_csv, "validation_csv", data_root, mix_name, instruments, config, reporter)

    model_dir = config.get("model_dir")
    if isinstance(model_dir, str) and model_dir:
        model_path = Path(model_dir)
        if model_path.exists() and not model_path.is_dir():
            reporter.error(f"model_dir exists but is not a directory: {model_dir}")
    elif "model_dir" in config:
        reporter.error(f"model_dir must be a non-empty string; got {model_dir!r}")


def print_report(reporter: Reporter, quiet: bool) -> None:
    if reporter.errors:
        print("Validation failed:", file=sys.stderr)
        for message in reporter.errors:
            print(f"ERROR: {message}", file=sys.stderr)
    if reporter.warnings:
        if not reporter.errors:
            print("Validation warnings:", file=sys.stderr)
        for message in reporter.warnings:
            print(f"WARNING: {message}", file=sys.stderr)
    if not reporter.errors and not reporter.warnings and not quiet:
        print("Validation OK: config, CSV schema, paths, durations, and dimension rules passed.")
    elif not reporter.errors and reporter.warnings and not quiet:
        print("Validation OK with warnings.")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    reporter = Reporter()
    config_path = Path(args.config).expanduser()
    data_root = Path(args.data).expanduser()
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path
    if not data_root.is_absolute():
        data_root = Path.cwd() / data_root

    config = load_json(config_path, reporter)
    if config:
        validate_top_level(config, reporter)
        validate_dimensions(config, reporter)
        validate_paths(config, config_path, data_root, args.csv_base, reporter)

    print_report(reporter, args.quiet)
    if reporter.errors or (args.warnings_as_errors and reporter.warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
