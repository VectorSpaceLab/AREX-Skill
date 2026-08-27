#!/usr/bin/env python3
"""Validate a local/offline ModelScope dataset recipe.

The validator is intentionally static and safe: it does not import ModelScope,
does not contact Hugging Face or ModelScope Hubs, does not download data, and
does not write files. It checks that a JSON/YAML recipe has the fields needed
for a local `MsDataset.load(...)` call and that referenced local paths exist.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple
from urllib.parse import urlparse

LOCAL_BUILDERS = {
    "csv",
    "json",
    "parquet",
    "text",
    "imagefolder",
    "audiofolder",
}
SINGLE_FILE_EXTENSIONS = {
    ".csv": "csv",
    ".tsv": "csv",
    ".json": "json",
    ".jsonl": "json",
    ".parquet": "parquet",
    ".txt": "text",
}
CONFIG_EXTENSIONS = {".json", ".yaml", ".yml", ".py"}
FILEIO_EXTENSIONS = {".json", ".yaml", ".yml"}
VALID_DOWNLOAD_MODES = {
    "reuse_dataset_if_exists",
    "force_redownload",
    "REUSE_DATASET_IF_EXISTS",
    "FORCE_REDOWNLOAD",
}
REMOTE_SCHEMES = {"http", "https", "oss", "s3", "gs", "hf", "modelscope"}
REMOTE_SOURCES = {"hf", "huggingface", "modelscope", "remote"}


class ValidationResult:

    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.checked_paths: List[str] = []
        self.discovered_columns: Dict[str, List[str]] = {}

    @property
    def ok(self) -> bool:
        return not self.errors

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def add_info(self, msg: str) -> None:
        self.info.append(msg)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "checked_paths": self.checked_paths,
            "discovered_columns": self.discovered_columns,
        }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Statically validate a JSON/YAML ModelScope dataset recipe for "
            "local/offline MsDataset.load arguments. No network or downloads "
            "are performed."
        )
    )
    parser.add_argument("recipe", help="Path to a JSON, YAML, or YML recipe file.")
    parser.add_argument(
        "--base-dir",
        help=(
            "Directory used to resolve relative local paths. Defaults to the "
            "recipe file's parent directory."
        ),
    )
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help=(
            "Permit recipes marked as remote/Hugging Face/ModelScope for static "
            "argument checks. Remote paths are not contacted and are not proved."
        ),
    )
    parser.add_argument(
        "--strict-columns",
        action="store_true",
        help=(
            "Require target, column_mapping sources, and expected_columns to be "
            "verifiable from local CSV/TSV/JSON/JSONL headers or samples."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text diagnostics.",
    )
    return parser.parse_args(argv)


def is_remote_uri(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme and parsed.scheme.lower() in REMOTE_SCHEMES)


def load_recipe(path: Path) -> Any:
    suffix = path.suffix.lower()
    with path.open("r", encoding="utf-8") as handle:
        if suffix == ".json":
            return json.load(handle)
        if suffix in {".yaml", ".yml"}:
            try:
                import yaml  # type: ignore
            except Exception as exc:  # pragma: no cover - depends on environment
                raise RuntimeError(
                    "YAML recipe parsing requires PyYAML to be installed. "
                    "Use JSON or install PyYAML."
                ) from exc
            return yaml.safe_load(handle)
    raise ValueError("Recipe extension must be .json, .yaml, or .yml")


def flatten_load_args(recipe: Mapping[str, Any]) -> Dict[str, Any]:
    """Accept either top-level load args or a nested load_args mapping."""
    if isinstance(recipe.get("load_args"), Mapping):
        merged = dict(recipe.get("load_args", {}))
        for key, value in recipe.items():
            if key != "load_args" and key not in merged:
                merged[key] = value
        return merged
    return dict(recipe)


def resolve_local_path(raw: str, base_dir: Path) -> Path:
    expanded = os.path.expandvars(os.path.expanduser(raw))
    path = Path(expanded)
    if not path.is_absolute():
        path = base_dir / path
    return path


def has_glob_magic(value: str) -> bool:
    return any(ch in value for ch in "*?[")


def iter_data_file_values(data_files: Any) -> Iterable[Tuple[str, str]]:
    if isinstance(data_files, str):
        yield "data_files", data_files
    elif isinstance(data_files, Sequence) and not isinstance(data_files, (bytes, bytearray, str)):
        for idx, item in enumerate(data_files):
            if isinstance(item, str):
                yield f"data_files[{idx}]", item
            else:
                yield f"data_files[{idx}]", ""
    elif isinstance(data_files, Mapping):
        for split, value in data_files.items():
            label = f"data_files[{split!r}]"
            if isinstance(value, str):
                yield label, value
            elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
                for idx, item in enumerate(value):
                    if isinstance(item, str):
                        yield f"{label}[{idx}]", item
                    else:
                        yield f"{label}[{idx}]", ""
            else:
                yield label, ""


def validate_non_empty_data_files(data_files: Any, result: ValidationResult) -> None:
    if data_files is None:
        return
    if data_files == "" or data_files == [] or data_files == {}:
        result.add_error("data_files must be non-empty when provided.")
        return
    if isinstance(data_files, Mapping):
        for split, value in data_files.items():
            if not split:
                result.add_error("data_files contains an empty split key.")
            if value == "" or value == [] or value == {} or value is None:
                result.add_error(f"data_files[{split!r}] must be non-empty.")
    elif isinstance(data_files, Sequence) and not isinstance(data_files, (str, bytes, bytearray)):
        for idx, value in enumerate(data_files):
            if not isinstance(value, str) or not value:
                result.add_error(f"data_files[{idx}] must be a non-empty string path or glob.")
    elif not isinstance(data_files, str):
        result.add_error("data_files must be a string, list of strings, or split mapping.")


def check_path(
    label: str,
    raw: str,
    base_dir: Path,
    result: ValidationResult,
    *,
    must_be_dir: bool = False,
    must_be_file: bool = False,
    allow_remote: bool = False,
) -> List[Path]:
    if not raw:
        result.add_error(f"{label} is empty.")
        return []
    if is_remote_uri(raw):
        if allow_remote:
            result.add_warning(f"{label} is remote ({raw}); not checked by this offline validator.")
        else:
            result.add_error(f"{label} is remote ({raw}); pass --allow-remote only for static remote checks.")
        return []

    resolved = resolve_local_path(raw, base_dir)
    matches: List[Path]
    if has_glob_magic(str(resolved)):
        matches = [Path(p) for p in sorted(glob.glob(str(resolved)))]
        if not matches:
            result.add_error(f"{label} glob matched no files: {raw}")
            return []
    else:
        matches = [resolved]
        if not resolved.exists():
            result.add_error(f"{label} path does not exist: {raw} -> {resolved}")
            return []

    for match in matches:
        result.checked_paths.append(str(match))
        if must_be_dir and not match.is_dir():
            result.add_error(f"{label} must be a directory: {match}")
        if must_be_file and not match.is_file():
            result.add_error(f"{label} must be a file: {match}")
    return matches


def infer_columns_from_file(path: Path) -> Optional[List[str]]:
    suffix = path.suffix.lower()
    try:
        if suffix in {".csv", ".tsv"}:
            delimiter = "\t" if suffix == ".tsv" else ","
            with path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.reader(handle, delimiter=delimiter)
                header = next(reader, None)
            if header:
                return [str(col) for col in header]
        if suffix == ".jsonl":
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    if isinstance(obj, Mapping):
                        return [str(key) for key in obj.keys()]
                    return None
        if suffix == ".json":
            with path.open("r", encoding="utf-8") as handle:
                obj = json.load(handle)
            if isinstance(obj, Mapping):
                return [str(key) for key in obj.keys()]
            if isinstance(obj, list) and obj and isinstance(obj[0], Mapping):
                return [str(key) for key in obj[0].keys()]
    except Exception:
        return None
    return None


def collect_inferred_columns(paths: Iterable[Path], result: ValidationResult) -> Set[str]:
    columns: Set[str] = set()
    for path in paths:
        if not path.is_file():
            continue
        inferred = infer_columns_from_file(path)
        if inferred is not None:
            result.discovered_columns[str(path)] = inferred
            columns.update(inferred)
    return columns


def validate_columns(args: Mapping[str, Any], columns: Set[str], result: ValidationResult, strict: bool) -> None:
    expected = args.get("expected_columns")
    if expected is not None:
        if not isinstance(expected, Sequence) or isinstance(expected, (str, bytes, bytearray)):
            result.add_error("expected_columns must be a list of column names.")
        else:
            expected_set = {str(col) for col in expected}
            if columns:
                missing = sorted(expected_set - columns)
                if missing:
                    result.add_error(f"expected_columns missing from inferred columns: {missing}")
            elif strict:
                result.add_error("--strict-columns set but expected_columns could not be verified from local files.")
            else:
                result.add_warning("expected_columns could not be verified from local files.")

    target = args.get("target")
    if target:
        if columns and str(target) not in columns:
            result.add_error(f"target column {target!r} was not found in inferred columns: {sorted(columns)}")
        elif strict and not columns:
            result.add_error("--strict-columns set but target could not be verified from local files.")
        elif not columns:
            result.add_warning("target column could not be verified from local files.")

    mapping = args.get("column_mapping")
    if mapping is not None:
        if not isinstance(mapping, Mapping):
            result.add_error("column_mapping must be a mapping from source column to destination column.")
            return
        sources = {str(key) for key in mapping.keys()}
        if columns:
            missing = sorted(sources - columns)
            if missing:
                result.add_error(f"column_mapping source columns missing from inferred columns: {missing}")
        elif strict:
            result.add_error("--strict-columns set but column_mapping sources could not be verified from local files.")
        else:
            result.add_warning("column_mapping sources could not be verified from local files.")


def validate_recipe(args: Mapping[str, Any], base_dir: Path, allow_remote: bool, strict_columns: bool) -> ValidationResult:
    result = ValidationResult()

    dataset_name = args.get("dataset_name")
    if not dataset_name:
        result.add_error("Missing required field: dataset_name")
        return result
    if not isinstance(dataset_name, str):
        result.add_error("dataset_name must be a string for recipe validation.")
        return result

    if "streaming" in args:
        result.add_error("Use use_streaming for MsDataset.load recipes; do not pass streaming.")

    use_streaming = args.get("use_streaming")
    if use_streaming is not None and not isinstance(use_streaming, bool):
        result.add_error("use_streaming must be true or false when provided.")

    dataset_info_only = args.get("dataset_info_only")
    if dataset_info_only is not None and not isinstance(dataset_info_only, bool):
        result.add_error("dataset_info_only must be true or false when provided.")

    trust_remote_code = bool(args.get("trust_remote_code", False))
    if args.get("trust_remote_code") not in (None, True, False):
        result.add_error("trust_remote_code must be true or false when provided.")

    download_mode = args.get("download_mode")
    if download_mode is not None and str(download_mode) not in VALID_DOWNLOAD_MODES:
        result.add_warning(
            "download_mode is not one of the common ModelScope values: "
            "reuse_dataset_if_exists or force_redownload."
        )

    hub = args.get("hub")
    if hub is not None and str(hub).lower() not in {"modelscope", "huggingface", "hf"}:
        result.add_warning("hub is unusual; expected modelscope or huggingface/hf.")

    source = str(args.get("source", "")).lower().strip()
    remote_source = source in REMOTE_SOURCES or str(hub).lower() in {"huggingface", "hf"} or is_remote_uri(dataset_name)
    if remote_source and not allow_remote:
        result.add_error(
            "Recipe appears to target a remote source; this validator is offline. "
            "Use --allow-remote only for static argument checks, not proof of availability."
        )

    dataset_paths: List[Path] = []
    dataset_is_builder = dataset_name in LOCAL_BUILDERS
    if dataset_name.endswith(".py") and not trust_remote_code:
        result.add_error("Python dataset scripts execute code; set trust_remote_code: true only if the script is trusted.")

    if remote_source:
        result.add_warning("Remote dataset availability, credentials, and split metadata were not checked.")
    elif dataset_is_builder:
        result.add_info(f"dataset_name {dataset_name!r} treated as a local packaged builder.")
    else:
        dataset_paths = check_path("dataset_name", dataset_name, base_dir, result, allow_remote=allow_remote)
        for path in dataset_paths:
            if path.is_file() and path.suffix.lower() not in SINGLE_FILE_EXTENSIONS and path.suffix.lower() != ".py":
                result.add_warning(
                    f"dataset_name file extension {path.suffix!r} is not a known direct MsDataset single-file extension."
                )

    data_dir = args.get("data_dir")
    if data_dir is not None:
        if not isinstance(data_dir, str):
            result.add_error("data_dir must be a string path.")
        else:
            check_path("data_dir", data_dir, base_dir, result, must_be_dir=True, allow_remote=allow_remote)

    data_files = args.get("data_files")
    validate_non_empty_data_files(data_files, result)
    data_file_paths: List[Path] = []
    if data_files is not None:
        for label, value in iter_data_file_values(data_files):
            if not value:
                # A type/empty error was already emitted by validate_non_empty_data_files.
                continue
            data_file_paths.extend(check_path(label, value, base_dir, result, must_be_file=True, allow_remote=allow_remote))

    if dataset_is_builder and data_dir is None and data_files is None and dataset_name not in {"imagefolder", "audiofolder"}:
        result.add_error(f"Packaged builder {dataset_name!r} requires non-empty data_files for local/offline loading.")
    if dataset_name in {"imagefolder", "audiofolder"} and data_dir is None and data_files is None:
        result.add_error(f"Builder {dataset_name!r} usually requires data_dir or data_files for local/offline loading.")

    split = args.get("split")
    if split and isinstance(data_files, Mapping) and split not in data_files:
        result.add_warning(f"split {split!r} is not a key in data_files; verify this is intentional.")

    config_path = args.get("config") or args.get("custom_cfg")
    if config_path is not None:
        if not isinstance(config_path, str):
            result.add_error("config/custom_cfg must be a string path when provided in a static recipe.")
        else:
            config_matches = check_path("config", config_path, base_dir, result, must_be_file=True, allow_remote=allow_remote)
            for path in config_matches:
                suffix = path.suffix.lower()
                if suffix not in CONFIG_EXTENSIONS:
                    result.add_error(f"Config file extension must be one of {sorted(CONFIG_EXTENSIONS)}: {path}")
                if suffix == ".py" and not trust_remote_code:
                    result.add_error("Python config files execute code; set trust_remote_code: true only if trusted.")
                if suffix in {".json", ".yaml", ".yml"} and path.suffix.lower() not in FILEIO_EXTENSIONS:
                    result.add_error(f"Unsupported fileio config extension: {path.suffix}")

    inferred_paths = data_file_paths or [p for p in dataset_paths if p.is_file()]
    inferred_columns = collect_inferred_columns(inferred_paths, result)
    validate_columns(args, inferred_columns, result, strict_columns)

    return result


def emit_text(result: ValidationResult) -> None:
    if result.ok:
        print("OK: recipe passed static local/offline validation.")
    else:
        print("FAILED: recipe did not pass validation.")

    if result.errors:
        print("\nErrors:")
        for msg in result.errors:
            print(f"  - {msg}")
    if result.warnings:
        print("\nWarnings:")
        for msg in result.warnings:
            print(f"  - {msg}")
    if result.info:
        print("\nInfo:")
        for msg in result.info:
            print(f"  - {msg}")
    if result.checked_paths:
        print("\nChecked paths:")
        for path in result.checked_paths:
            print(f"  - {path}")
    if result.discovered_columns:
        print("\nDiscovered columns:")
        for path, columns in result.discovered_columns.items():
            print(f"  - {path}: {columns}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    ns = parse_args(argv)
    recipe_path = Path(os.path.expanduser(os.path.expandvars(ns.recipe))).resolve()
    result = ValidationResult()

    if not recipe_path.exists():
        result.add_error(f"Recipe file does not exist: {recipe_path}")
    elif not recipe_path.is_file():
        result.add_error(f"Recipe path is not a file: {recipe_path}")
    else:
        try:
            recipe = load_recipe(recipe_path)
            if not isinstance(recipe, Mapping):
                result.add_error("Recipe top level must be a JSON/YAML mapping/object.")
            else:
                base_dir = Path(ns.base_dir).expanduser().resolve() if ns.base_dir else recipe_path.parent
                load_args = flatten_load_args(recipe)
                result = validate_recipe(load_args, base_dir, ns.allow_remote, ns.strict_columns)
        except Exception as exc:
            result.add_error(f"Could not parse or validate recipe: {exc}")

    if ns.json:
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        emit_text(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
