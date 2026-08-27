#!/usr/bin/env python3
"""Validate nnU-Net v2 inference input filenames against dataset.json.

This script checks names only. It does not import nnU-Net, load medical images,
inspect geometry, or validate image contents.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


CHANNEL_PATTERN = re.compile(r"^(?P<case>.+)_(?P<channel>\d{4})$")


def _load_dataset_json(dataset_json_or_model: Path) -> tuple[dict, Path]:
    if dataset_json_or_model.is_dir():
        dataset_json_path = dataset_json_or_model / "dataset.json"
    else:
        dataset_json_path = dataset_json_or_model

    if not dataset_json_path.is_file():
        raise FileNotFoundError(f"dataset.json not found: {dataset_json_path}")

    with dataset_json_path.open("r", encoding="utf-8") as handle:
        return json.load(handle), dataset_json_path


def _channel_count(dataset_json: dict) -> int:
    channel_names = dataset_json.get("channel_names", dataset_json.get("modality"))
    if not isinstance(channel_names, dict) or not channel_names:
        raise ValueError("dataset.json must contain a non-empty 'channel_names' mapping")
    return len(channel_names)


def _file_ending(dataset_json: dict) -> str:
    ending = dataset_json.get("file_ending")
    if not isinstance(ending, str) or not ending:
        raise ValueError("dataset.json must contain a non-empty 'file_ending' string")
    return ending


def _strip_file_ending(path: Path, file_ending: str) -> str | None:
    name = path.name
    if not name.endswith(file_ending):
        return None
    return name[: -len(file_ending)]


def check_inputs(input_folder: Path, dataset_json: dict, allow_extra_files: bool) -> tuple[list[str], list[str]]:
    expected_channels = _channel_count(dataset_json)
    file_ending = _file_ending(dataset_json)
    expected_channel_ids = {f"{channel_index:04d}" for channel_index in range(expected_channels)}

    errors: list[str] = []
    warnings: list[str] = []
    cases: dict[str, set[str]] = {}

    if not input_folder.is_dir():
        return [f"Input folder does not exist or is not a directory: {input_folder}"], warnings

    files = sorted(path for path in input_folder.iterdir() if path.is_file())
    if not files:
        return [f"Input folder contains no files: {input_folder}"], warnings

    for path in files:
        stem = _strip_file_ending(path, file_ending)
        if stem is None:
            message = f"Unexpected file ending: {path.name} (expected *{file_ending})"
            if allow_extra_files:
                warnings.append(message)
            else:
                errors.append(message)
            continue

        match = CHANNEL_PATTERN.match(stem)
        if not match:
            errors.append(
                f"Invalid inference filename: {path.name} "
                f"(expected CASE_0000{file_ending}, CASE_0001{file_ending}, ...)"
            )
            continue

        case_id = match.group("case")
        channel_id = match.group("channel")
        if channel_id not in expected_channel_ids:
            errors.append(
                f"Unexpected channel suffix in {path.name}: _{channel_id}; "
                f"expected channels {', '.join(sorted(expected_channel_ids))}"
            )
            continue

        channels = cases.setdefault(case_id, set())
        if channel_id in channels:
            errors.append(f"Duplicate channel _{channel_id} for case {case_id}")
        channels.add(channel_id)

    for case_id, present_channels in sorted(cases.items()):
        missing = expected_channel_ids - present_channels
        extra = present_channels - expected_channel_ids
        if missing:
            errors.append(f"Case {case_id} is missing channel(s): {', '.join(sorted(missing))}")
        if extra:
            errors.append(f"Case {case_id} has unexpected channel(s): {', '.join(sorted(extra))}")

    if not cases and not errors:
        errors.append(f"No valid nnU-Net inference files found with ending {file_ending}")

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check nnU-Net v2 inference input filenames against dataset.json."
    )
    parser.add_argument("input_folder", type=Path, help="Folder containing inference images")
    parser.add_argument(
        "dataset_json_or_model_folder",
        type=Path,
        help="Path to dataset.json or to a model/results folder containing dataset.json",
    )
    parser.add_argument(
        "--allow-extra-files",
        action="store_true",
        help="Warn instead of failing on files that do not match dataset.json file_ending",
    )
    args = parser.parse_args(argv)

    try:
        dataset_json, dataset_json_path = _load_dataset_json(args.dataset_json_or_model_folder)
        errors, warnings = check_inputs(args.input_folder, dataset_json, args.allow_extra_files)
    except Exception as exc:  # noqa: BLE001 - CLI should print concise failures for users.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    if errors:
        print(f"Checked against: {dataset_json_path}", file=sys.stderr)
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    channel_count = _channel_count(dataset_json)
    file_ending = _file_ending(dataset_json)
    print(
        f"OK: inference filenames match {channel_count} channel(s) "
        f"and file ending {file_ending} from {dataset_json_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
