#!/usr/bin/env python3
"""Validate a local RecBole atomic dataset directory.

This checker is intentionally standalone: it does not import RecBole and it does
not write, download, or modify data. It validates the file names and headers
that RecBole expects before dataset construction.

Examples:
  # General recommendation dataset. Dataset name defaults to directory basename.
  scripts/validate_atomic_dataset.py /path/to/dataset-root/book_clicks \
      --task-family general

  # Context-aware dataset with an explicit RecBole dataset name.
  scripts/validate_atomic_dataset.py /path/to/dataset-root/ad_clicks \
      --dataset ad_clicks --task-family context

  # Knowledge-aware dataset and config load_col check.
  scripts/validate_atomic_dataset.py /path/to/dataset-root/movie_kg \
      --dataset movie_kg --task-family knowledge --config-yaml recbole.yaml

  # Pre-split sequential benchmark files: sessions.train.inter, etc.
  scripts/validate_atomic_dataset.py /path/to/dataset-root/sessions \
      --dataset sessions --task-family sequential \
      --benchmark-filename train valid test

  # Non-tab atomic files. Use shell quoting so \t and other escapes survive.
  scripts/validate_atomic_dataset.py /path/to/dataset-root/csv_data \
      --dataset csv_data --delimiter ','
"""

from __future__ import annotations

import argparse
import codecs
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

SUPPORTED_TYPES = {"token", "token_seq", "float", "float_seq"}
KNOWN_SUFFIXES = {"inter", "user", "item", "kg", "link", "net"}
TASK_REQUIRED = {
    "general": ["inter"],
    "context": ["inter", "user", "item"],
    "knowledge": ["inter", "kg", "link"],
    "sequential": ["inter"],
    "social": ["inter", "net"],
}


class Report:
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.infos: List[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def info(self, message: str) -> None:
        self.infos.append(message)

    def emit(self) -> int:
        for message in self.infos:
            print(f"INFO: {message}")
        for message in self.warnings:
            print(f"WARNING: {message}")
        if self.errors:
            for message in self.errors:
                print(f"ERROR: {message}")
            print(f"FAILED: {len(self.errors)} error(s), {len(self.warnings)} warning(s)")
            return 1
        print(f"OK: 0 error(s), {len(self.warnings)} warning(s)")
        return 0


def decode_delimiter(value: str) -> str:
    """Decode common shell strings such as '\\t' into an actual delimiter."""
    try:
        decoded = codecs.decode(value, "unicode_escape")
    except Exception:
        decoded = value
    if decoded == "":
        raise argparse.ArgumentTypeError("delimiter must not be empty")
    return decoded


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate RecBole atomic dataset files, headers, and optional load_col YAML.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Supported task families and required files:
  general:    <dataset>.inter
  context:    <dataset>.inter, <dataset>.user, <dataset>.item
  knowledge:  <dataset>.inter, <dataset>.kg, <dataset>.link
  sequential: <dataset>.inter
  social:     <dataset>.inter, <dataset>.net

Header rule:
  Every header cell must be field_name:field_type, where field_type is one of
  token, token_seq, float, float_seq. The default delimiter is a tab.
""",
    )
    parser.add_argument(
        "dataset_dir",
        type=Path,
        help="Directory containing files named <dataset>.<suffix>, e.g. book_clicks.inter.",
    )
    parser.add_argument(
        "--dataset",
        help="Expected RecBole dataset name. Defaults to the dataset directory basename.",
    )
    parser.add_argument(
        "--task-family",
        choices=sorted(TASK_REQUIRED),
        default="general",
        help="Recommendation task family that determines mandatory atomic files.",
    )
    parser.add_argument(
        "--delimiter",
        default="\\t",
        type=decode_delimiter,
        help="Column delimiter used by atomic files. Default: tab. Accepts escapes like '\\t'.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Encoding for reading headers. Default: utf-8.",
    )
    parser.add_argument(
        "--config-yaml",
        type=Path,
        help="Optional YAML config to validate load_col/unload_col/additional_feat_suffix against headers. Requires PyYAML.",
    )
    parser.add_argument(
        "--benchmark-filename",
        nargs="*",
        default=None,
        metavar="NAME",
        help="Pre-split interaction suffixes such as train valid test; checks <dataset>.<NAME>.inter instead of <dataset>.inter.",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Treat warnings as errors.",
    )
    return parser


def expected_files(dataset: str, required_suffixes: Sequence[str], benchmark: Optional[Sequence[str]]) -> Dict[str, List[Path]]:
    result: Dict[str, List[Path]] = {}
    for suffix in required_suffixes:
        if suffix == "inter" and benchmark:
            result[suffix] = [Path(f"{dataset}.{name}.inter") for name in benchmark]
        else:
            result[suffix] = [Path(f"{dataset}.{suffix}")]
    return result


def scan_dataset_prefixed_files(dataset_dir: Path, dataset: str) -> Dict[str, List[Path]]:
    found: Dict[str, List[Path]] = {}
    prefix = dataset + "."
    try:
        entries = list(dataset_dir.iterdir())
    except OSError:
        return found
    for path in entries:
        if not path.is_file() or not path.name.startswith(prefix):
            continue
        rest = path.name[len(prefix) :]
        if not rest:
            continue
        if rest.endswith(".inter") and rest != "inter":
            # benchmark file such as dataset.train.inter; source is still inter
            suffix = "inter"
        else:
            suffix = rest
        found.setdefault(suffix, []).append(path)
    return found


def parse_header(path: Path, delimiter: str, encoding: str, report: Report) -> Optional[Dict[str, str]]:
    try:
        with path.open("r", encoding=encoding, newline="") as handle:
            raw_header = handle.readline()
    except UnicodeDecodeError as exc:
        report.error(f"{path.name}: cannot decode header with {encoding}: {exc}")
        return None
    except OSError as exc:
        report.error(f"{path.name}: cannot read file: {exc}")
        return None

    if raw_header == "":
        report.error(f"{path.name}: file is empty; expected a header line")
        return None

    header = raw_header.rstrip("\r\n")
    if not header:
        report.error(f"{path.name}: header line is blank")
        return None

    parts = header.split(delimiter)
    if len(parts) == 1 and delimiter == "\t" and " " in header:
        report.warn(
            f"{path.name}: header contains spaces but no tab delimiter. "
            "If this file is space-delimited, set field_separator consistently; "
            "otherwise rewrite the header/data rows as tab-delimited."
        )

    fields: Dict[str, str] = {}
    for index, cell in enumerate(parts, start=1):
        if cell == "":
            report.error(f"{path.name}: header column {index} is empty")
            continue
        if cell.count(":") != 1:
            suggestion = ""
            if " " in cell and ":" not in cell:
                suggestion = (
                    " Example remediation for a tiny rating file: "
                    "user_id:token<TAB>item_id:token<TAB>rating:float."
                )
            report.error(
                f"{path.name}: header column {index} ({cell!r}) must be field_name:field_type."
                + suggestion
            )
            continue
        field, field_type = cell.split(":", 1)
        if not field:
            report.error(f"{path.name}: header column {index} has an empty field name")
            continue
        if field_type not in SUPPORTED_TYPES:
            report.error(
                f"{path.name}: field {field!r} has unsupported type {field_type!r}; "
                f"supported types are {', '.join(sorted(SUPPORTED_TYPES))}"
            )
            continue
        if field in fields:
            report.error(f"{path.name}: duplicate field {field!r} in header")
            continue
        fields[field] = field_type

    if fields:
        report.info(
            f"{path.name}: {len(fields)} header field(s): "
            + ", ".join(f"{name}:{typ}" for name, typ in fields.items())
        )
    return fields if fields else None


def load_yaml_config(path: Path, report: Report) -> Optional[Mapping[str, Any]]:
    try:
        import yaml  # type: ignore
    except Exception:
        report.error("--config-yaml was provided but PyYAML is not installed; rerun without --config-yaml or install PyYAML")
        return None

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except OSError as exc:
        report.error(f"cannot read config YAML {path}: {exc}")
        return None
    except Exception as exc:
        report.error(f"cannot parse config YAML {path}: {exc}")
        return None

    if data is None:
        return {}
    if not isinstance(data, Mapping):
        report.error(f"config YAML {path} must contain a mapping at the top level")
        return None
    return data


def normalize_suffix_list(value: Any, key: str, report: Report) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        result: List[str] = []
        for item in value:
            if not isinstance(item, str):
                report.error(f"{key} entries must be strings; got {item!r}")
            else:
                result.append(item)
        return result
    report.error(f"{key} must be a string, list of strings, or null; got {type(value).__name__}")
    return []


def source_files_for_suffix(
    suffix: str,
    dataset: str,
    dataset_dir: Path,
    benchmark: Optional[Sequence[str]],
) -> List[Path]:
    if suffix == "inter" and benchmark:
        return [dataset_dir / f"{dataset}.{name}.inter" for name in benchmark]
    return [dataset_dir / f"{dataset}.{suffix}"]


def validate_field_list(
    suffix: str,
    value: Any,
    header_map: Mapping[Path, Optional[Dict[str, str]]],
    files: Sequence[Path],
    report: Report,
    setting_name: str,
) -> None:
    if value == "*":
        return
    if value is None:
        return
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        report.error(f"{setting_name}.{suffix} must be a list of field names, '*', or null; got {value!r}")
        return
    requested: List[str] = []
    for item in value:
        if not isinstance(item, str):
            report.error(f"{setting_name}.{suffix} contains non-string field {item!r}")
        else:
            requested.append(item)
    if not requested:
        report.warn(f"{setting_name}.{suffix} is an empty list; RecBole will load no columns from this source")
        return
    for path in files:
        fields = header_map.get(path)
        if fields is None:
            # Missing file/header errors are reported elsewhere.
            continue
        missing = [field for field in requested if field not in fields]
        if missing:
            report.error(
                f"{setting_name}.{suffix} requests missing field(s) {missing} in {path.name}; "
                f"available fields are {list(fields.keys())}"
            )


def validate_yaml_against_headers(
    config: Mapping[str, Any],
    dataset: str,
    dataset_dir: Path,
    required_suffixes: Sequence[str],
    benchmark: Optional[Sequence[str]],
    header_map: MutableMapping[Path, Optional[Dict[str, str]]],
    delimiter: str,
    encoding: str,
    report: Report,
) -> None:
    load_col = config.get("load_col", "__missing__")
    unload_col = config.get("unload_col")
    additional_suffixes = normalize_suffix_list(config.get("additional_feat_suffix"), "additional_feat_suffix", report)

    for suffix in additional_suffixes:
        if suffix in KNOWN_SUFFIXES:
            report.warn(f"additional_feat_suffix includes standard suffix {suffix!r}; this is usually unnecessary")
        files = source_files_for_suffix(suffix, dataset, dataset_dir, benchmark)
        for path in files:
            if not path.is_file():
                report.error(f"additional_feat_suffix {suffix!r} expects missing file {path.name}")
            elif path not in header_map:
                header_map[path] = parse_header(path, delimiter, encoding, report)

    if load_col == "__missing__":
        report.info("config YAML has no load_col; RecBole defaults/model-type configs may still supply one")
        return

    required_plus_extra = list(dict.fromkeys(list(required_suffixes) + additional_suffixes))

    if load_col is None:
        report.info("config YAML sets load_col: null; all loaded source columns are allowed")
    elif not isinstance(load_col, Mapping):
        report.error(f"load_col must be a mapping, null, or omitted; got {type(load_col).__name__}")
        return
    else:
        for suffix in required_plus_extra:
            if suffix not in load_col:
                report.error(
                    f"load_col omits required source {suffix!r}; when load_col is a dict, omitted sources are not loaded"
                )
        for suffix, value in load_col.items():
            if not isinstance(suffix, str):
                report.error(f"load_col key {suffix!r} is not a string suffix")
                continue
            if suffix not in KNOWN_SUFFIXES and suffix not in additional_suffixes:
                report.warn(
                    f"load_col has nonstandard suffix {suffix!r}; add it to additional_feat_suffix if it should be loaded"
                )
            files = source_files_for_suffix(suffix, dataset, dataset_dir, benchmark)
            for path in files:
                if not path.is_file():
                    report.error(f"load_col.{suffix} expects missing file {path.name}")
                elif path not in header_map:
                    header_map[path] = parse_header(path, delimiter, encoding, report)
            validate_field_list(suffix, value, header_map, files, report, "load_col")

    if unload_col is None:
        return
    if not isinstance(unload_col, Mapping):
        report.error(f"unload_col must be a mapping or null; got {type(unload_col).__name__}")
        return
    for suffix, value in unload_col.items():
        if not isinstance(suffix, str):
            report.error(f"unload_col key {suffix!r} is not a string suffix")
            continue
        if isinstance(load_col, Mapping) and suffix in load_col and load_col.get(suffix) not in (None, "*"):
            report.error(f"load_col and unload_col both configure source {suffix!r}; use only one strategy for that source")
        files = source_files_for_suffix(suffix, dataset, dataset_dir, benchmark)
        for path in files:
            if path.is_file() and path not in header_map:
                header_map[path] = parse_header(path, delimiter, encoding, report)
        validate_field_list(suffix, value, header_map, files, report, "unload_col")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = Report()

    dataset_dir = args.dataset_dir
    dataset = args.dataset or dataset_dir.name
    required_suffixes = TASK_REQUIRED[args.task_family]
    benchmark = args.benchmark_filename

    if not dataset_dir.exists():
        report.error(f"dataset directory does not exist: {dataset_dir}")
        return report.emit()
    if not dataset_dir.is_dir():
        report.error(f"dataset path is not a directory: {dataset_dir}")
        return report.emit()

    report.info(f"expected dataset name: {dataset}")
    report.info(f"task family: {args.task_family}; required sources: {', '.join(required_suffixes)}")
    if benchmark:
        report.info(f"benchmark interaction files: {', '.join(benchmark)}")

    prefixed = scan_dataset_prefixed_files(dataset_dir, dataset)
    if not prefixed:
        report.warn(f"no files starting with {dataset}. were found in {dataset_dir}")
    else:
        for suffix, paths in sorted(prefixed.items()):
            names = ", ".join(sorted(path.name for path in paths))
            report.info(f"found source {suffix}: {names}")

    expected = expected_files(dataset, required_suffixes, benchmark)
    header_map: Dict[Path, Optional[Dict[str, str]]] = {}
    for suffix, relative_paths in expected.items():
        for relative_path in relative_paths:
            path = dataset_dir / relative_path
            if not path.is_file():
                report.error(f"missing required {suffix} file: {relative_path}")
                continue
            header_map[path] = parse_header(path, args.delimiter, args.encoding, report)

    if args.config_yaml:
        config = load_yaml_config(args.config_yaml, report)
        if config is not None:
            validate_yaml_against_headers(
                config=config,
                dataset=dataset,
                dataset_dir=dataset_dir,
                required_suffixes=required_suffixes,
                benchmark=benchmark,
                header_map=header_map,
                delimiter=args.delimiter,
                encoding=args.encoding,
                report=report,
            )

    if args.strict_warnings and report.warnings:
        for warning in report.warnings:
            report.error(f"strict warning: {warning}")

    return report.emit()


if __name__ == "__main__":
    raise SystemExit(main())
