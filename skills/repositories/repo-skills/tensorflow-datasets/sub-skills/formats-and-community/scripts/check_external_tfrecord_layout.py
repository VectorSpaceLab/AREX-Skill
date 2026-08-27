#!/usr/bin/env python3
"""Validate TFDS external TFRecord-style metadata and shard layout.

The checker is standalone: it does not import TensorFlow, TensorFlow Datasets,
or any source checkout. It validates the filesystem and JSON heuristics that
should be true before `builder_from_directory` or `folder_dataset.write_metadata`
is used on externally produced shards.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path
from typing import Any

DEFAULT_TEMPLATE = "{DATASET}-{SPLIT}.{FILEFORMAT}-{SHARD_X_OF_Y}"
REQUIRED_METADATA = ("dataset_info.json", "features.json")
KNOWN_FILE_FORMATS = ("tfrecord", "riegeli", "array_record", "parquet")
KNOWN_DOC_SUFFIXES = (".md", ".bib", ".rst", ".txt")
KNOWN_METADATA_SUFFIXES = ("-info.json", ".labels.txt", ".vocab")

PLACEHOLDER_PATTERNS = {
    "DATASET": r"(?P<dataset_name>[A-Za-z0-9_][A-Za-z0-9_\-]*)",
    "SPLIT": r"(?P<split>[A-Za-z0-9_][A-Za-z0-9_\-]*)",
    "FILEFORMAT": r"(?P<filetype_suffix>\w+)",
    "SHARD_INDEX": r"(?P<shard_index>\d{5,})",
    "NUM_SHARDS": r"(?P<num_shards>\d{5,})",
    "SHARD_X_OF_Y": r"(?P<shard_index>\d{5,})-of-(?P<num_shards>\d{5,})",
}


def _normalize_file_format(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower().replace("-", "_")
    for known in KNOWN_FILE_FORMATS:
        if text == known or text.endswith("_" + known):
            return known
    return text or None


def _template_to_regex(template: str) -> re.Pattern[str]:
    """Builds a conservative regex for TFDS-style filename templates."""
    placeholder_re = re.compile(r"\{([A-Z_]+)\}")
    placeholders = placeholder_re.findall(template)
    if not placeholders:
        raise ValueError("template must contain TFDS-style placeholders such as {SPLIT}")
    duplicates = sorted({name for name in placeholders if placeholders.count(name) > 1})
    if duplicates:
        raise ValueError(f"template repeats placeholders that map to named regex groups: {duplicates}")
    if "SHARD_X_OF_Y" in placeholders and ({"SHARD_INDEX", "NUM_SHARDS"} & set(placeholders)):
        raise ValueError("use either {SHARD_X_OF_Y} or {SHARD_INDEX}/{NUM_SHARDS}, not both")

    parts: list[str] = []
    cursor = 0
    for match in placeholder_re.finditer(template):
        placeholder = match.group(1)
        if placeholder not in PLACEHOLDER_PATTERNS:
            known = ", ".join(sorted(PLACEHOLDER_PATTERNS))
            raise ValueError(f"unknown placeholder {{{placeholder}}}; known placeholders: {known}")
        parts.append(re.escape(template[cursor : match.start()]))
        parts.append(PLACEHOLDER_PATTERNS[placeholder])
        cursor = match.end()
    parts.append(re.escape(template[cursor:]))
    return re.compile("^" + "".join(parts) + "$")


def _parse_relative_path(relative_path: str, regex: re.Pattern[str]) -> dict[str, Any] | None:
    match = regex.match(relative_path)
    if not match:
        return None
    data: dict[str, Any] = {key: value for key, value in match.groupdict().items() if value is not None}
    for key in ("shard_index", "num_shards"):
        if key in data:
            data[key] = int(data[key])
    if "filetype_suffix" in data:
        data["filetype_suffix"] = _normalize_file_format(data["filetype_suffix"])
    return data


def _read_json(path: Path, errors: list[str]) -> Any | None:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        errors.append(f"missing required metadata file: {path.name}")
    except json.JSONDecodeError as exc:
        errors.append(f"metadata file is not valid JSON: {path.name}: {exc}")
    except OSError as exc:
        errors.append(f"could not read metadata file {path.name}: {exc}")
    return None


def _is_hidden(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def _is_ignored_sidecar(relative: Path) -> bool:
    name = relative.name
    if name in REQUIRED_METADATA:
        return True
    if _is_hidden(relative):
        return True
    if name.upper().startswith("README"):
        return True
    if name.upper() in {"LICENSE", "COPYING"}:
        return True
    if any(name.endswith(suffix) for suffix in KNOWN_METADATA_SUFFIXES):
        return True
    if relative.suffix.lower() in KNOWN_DOC_SUFFIXES:
        return True
    return False


def _metadata_field(data: Any, *names: str) -> Any | None:
    if not isinstance(data, dict):
        return None
    for name in names:
        if name in data:
            return data[name]
    return None


def _validate_features_json(features_info: Any, errors: list[str]) -> None:
    if features_info is None:
        return
    if not isinstance(features_info, dict):
        errors.append("features.json should contain a JSON object")
    elif not features_info:
        errors.append("features.json is empty; a TFDS FeaturesDict description is expected")


def _validate_metadata(
    dataset_info: Any,
    grouped: dict[str, list[tuple[str, dict[str, Any]]]],
    dataset_name: str | None,
    file_format: str | None,
    expected_splits: set[str] | None,
    errors: list[str],
) -> None:
    if dataset_info is None:
        return
    if not isinstance(dataset_info, dict):
        errors.append("dataset_info.json should contain a JSON object")
        return

    metadata_name = _metadata_field(dataset_info, "name")
    if dataset_name and metadata_name and metadata_name != dataset_name:
        errors.append(f"dataset_info.json name {metadata_name!r} does not match expected {dataset_name!r}")
    if metadata_name is None:
        errors.append("dataset_info.json does not declare a dataset name")

    if _metadata_field(dataset_info, "version") is None:
        errors.append("dataset_info.json does not declare a dataset version")

    metadata_format = _normalize_file_format(_metadata_field(dataset_info, "fileFormat", "file_format"))
    if file_format and metadata_format and metadata_format != file_format:
        errors.append(f"dataset_info.json file format {metadata_format!r} does not match expected {file_format!r}")

    splits = _metadata_field(dataset_info, "splits")
    if splits is None:
        errors.append("dataset_info.json does not declare splits")
        return
    if not isinstance(splits, list):
        errors.append("dataset_info.json field 'splits' should be a list")
        return
    if not grouped:
        return

    meta_split_names = {
        split.get("name") for split in splits if isinstance(split, dict) and split.get("name")
    }
    file_split_names = set(grouped)
    if meta_split_names and meta_split_names != file_split_names:
        errors.append(
            f"dataset_info.json splits {sorted(meta_split_names)} do not match shard splits {sorted(file_split_names)}"
        )
    if expected_splits and meta_split_names and meta_split_names != expected_splits:
        errors.append(
            f"dataset_info.json splits {sorted(meta_split_names)} do not match expected splits {sorted(expected_splits)}"
        )

    for split in splits:
        if not isinstance(split, dict):
            errors.append("dataset_info.json contains a non-object split entry")
            continue
        split_name = split.get("name")
        if not split_name or split_name not in grouped:
            continue
        shard_lengths = _metadata_field(split, "shardLengths", "shard_lengths")
        if isinstance(shard_lengths, list) and len(shard_lengths) != len(grouped[split_name]):
            errors.append(
                f"split {split_name!r} metadata has {len(shard_lengths)} shard lengths "
                f"but {len(grouped[split_name])} shard files were found"
            )


def _validate_grouped_files(
    grouped: dict[str, list[tuple[str, dict[str, Any]]]],
    dataset_name: str | None,
    file_format: str | None,
    errors: list[str],
) -> None:
    for split, entries in sorted(grouped.items()):
        dataset_names = {info.get("dataset_name") for _, info in entries if info.get("dataset_name")}
        if len(dataset_names) > 1:
            errors.append(f"split {split!r} has multiple dataset names: {sorted(dataset_names)}")
        if dataset_name and dataset_names and dataset_names != {dataset_name}:
            errors.append(f"split {split!r} dataset names {sorted(dataset_names)} do not match expected {dataset_name!r}")

        suffixes = {info.get("filetype_suffix") for _, info in entries if info.get("filetype_suffix")}
        if len(suffixes) > 1:
            errors.append(f"split {split!r} has multiple file format suffixes: {sorted(suffixes)}")
        if file_format and suffixes and suffixes != {file_format}:
            errors.append(f"split {split!r} file format suffixes {sorted(suffixes)} do not match expected {file_format!r}")
        if file_format and not suffixes:
            errors.append(f"split {split!r} cannot validate expected file format because the template lacks {{FILEFORMAT}}")

        shard_indices = [info.get("shard_index") for _, info in entries if info.get("shard_index") is not None]
        if len(shard_indices) != len(set(shard_indices)):
            errors.append(f"split {split!r} has duplicate shard indices: {sorted(shard_indices)}")

        num_shards_values = {info.get("num_shards") for _, info in entries if info.get("num_shards") is not None}
        if len(num_shards_values) > 1:
            errors.append(f"split {split!r} has inconsistent num_shards values: {sorted(num_shards_values)}")
        if num_shards_values:
            (num_shards,) = num_shards_values
            expected = list(range(num_shards))
            if sorted(shard_indices) != expected:
                errors.append(f"split {split!r} shard indices {sorted(shard_indices)} do not match expected {expected}")
        elif shard_indices:
            expected = list(range(max(shard_indices) + 1))
            if sorted(shard_indices) != expected:
                errors.append(f"split {split!r} shard indices {sorted(shard_indices)} are not contiguous from zero")


def _print_report(
    root: Path,
    grouped: dict[str, list[tuple[str, dict[str, Any]]]],
    template: str,
    errors: list[str],
    json_output: bool,
) -> None:
    payload = {
        "data_dir": str(root),
        "template": template,
        "matched_files": sum(len(entries) for entries in grouped.values()),
        "splits": {
            split: {
                "num_shards": len(entries),
                "files": [relative for relative, _ in entries],
                "dataset_names": sorted({info.get("dataset_name") for _, info in entries if info.get("dataset_name")}),
                "file_formats": sorted({info.get("filetype_suffix") for _, info in entries if info.get("filetype_suffix")}),
                "shard_indices": sorted(info.get("shard_index") for _, info in entries if info.get("shard_index") is not None),
            }
            for split, entries in sorted(grouped.items())
        },
        "errors": errors,
        "ok": not errors,
    }
    if json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    if errors:
        print(f"External TFRecord layout check failed for {root}")
        for error in errors:
            print(f"ERROR: {error}")
        return

    print(f"External TFRecord layout check passed for {root}")
    print(f"Template: {template}")
    print("Metadata: dataset_info.json, features.json")
    print(f"Matched data files: {payload['matched_files']}")
    print("Splits:")
    for split, summary in payload["splits"].items():
        dataset = ",".join(summary["dataset_names"]) or "<not encoded>"
        suffix = ",".join(summary["file_formats"]) or "<not encoded>"
        print(
            f"  - {split}: {summary['num_shards']} shard(s), "
            f"dataset={dataset}, format={suffix}, shard_indices={summary['shard_indices']}"
        )


def check_layout(args: argparse.Namespace) -> int:
    root = args.data_dir.expanduser().resolve()
    errors: list[str] = []

    if not root.exists():
        print(f"ERROR: data directory does not exist: {root}", file=sys.stderr)
        return 1
    if not root.is_dir():
        print(f"ERROR: data directory is not a directory: {root}", file=sys.stderr)
        return 1

    dataset_info = _read_json(root / "dataset_info.json", errors)
    features_info = _read_json(root / "features.json", errors)
    _validate_features_json(features_info, errors)

    try:
        regex = _template_to_regex(args.template)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except re.error as exc:
        print(f"ERROR: invalid template regex generated from {args.template!r}: {exc}", file=sys.stderr)
        return 2

    grouped: dict[str, list[tuple[str, dict[str, Any]]]] = collections.defaultdict(list)
    unmatched: list[str] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative_path = path.relative_to(root)
        relative = relative_path.as_posix()
        if _is_ignored_sidecar(relative_path):
            continue
        info = _parse_relative_path(relative, regex)
        if info is None:
            unmatched.append(relative)
            continue
        split = info.get("split")
        if not split:
            unmatched.append(relative)
            errors.append(f"matched file {relative!r} does not expose a split; include {{SPLIT}} in the template")
            continue
        grouped[split].append((relative, info))

    if unmatched:
        errors.append("files do not match the filename template: " + ", ".join(sorted(unmatched)))
    if not grouped:
        errors.append("no data shards matched the filename template")

    expected_splits = set(args.expected_splits or []) or None
    if expected_splits and set(grouped) != expected_splits:
        errors.append(f"detected splits {sorted(grouped)} do not match expected splits {sorted(expected_splits)}")

    expected_format = _normalize_file_format(args.file_format)
    _validate_grouped_files(grouped, args.dataset_name, expected_format, errors)
    _validate_metadata(dataset_info, grouped, args.dataset_name, expected_format, expected_splits, errors)
    _print_report(root, grouped, args.template, errors, args.json)
    return 1 if errors else 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate metadata files and shard naming heuristics for a TFDS "
            "external TFRecord-style builder directory without importing TFDS."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("data_dir", type=Path, help="Directory containing dataset_info.json, features.json, and shard files.")
    parser.add_argument("--template", default=DEFAULT_TEMPLATE, help="Filename template using TFDS-style placeholders.")
    parser.add_argument("--dataset-name", help="Expected dataset name encoded in filenames or metadata.")
    parser.add_argument("--file-format", choices=KNOWN_FILE_FORMATS, help="Expected file format suffix.")
    parser.add_argument("--split", dest="expected_splits", action="append", help="Expected split name. Repeat for multiple splits.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    return check_layout(parse_args(sys.argv[1:] if argv is None else argv))


if __name__ == "__main__":
    raise SystemExit(main())
