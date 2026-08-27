#!/usr/bin/env python3
"""Validate an Otter/MIMIC-IT training data YAML without importing Otter.

Checks are intentionally local and bounded. Use --check-records to inspect
instruction JSON content and --check-image-links to sample image-id membership in
image parquet/JSON assets.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Iterable

VALID_GROUPS = ("IMAGE_TEXT", "TEXT_ONLY", "VIDEO_TEXT", "IMAGE_TEXT_IN_CONTEXT")
MULTIMODAL_GROUPS = {"IMAGE_TEXT", "VIDEO_TEXT", "IMAGE_TEXT_IN_CONTEXT"}
PATH_FIELDS = {"mimicit_path", "images_path", "train_config_path"}


class Reporter:
    def __init__(self) -> None:
        self.errors: list[dict[str, str]] = []
        self.warnings: list[dict[str, str]] = []
        self.notes: list[dict[str, str]] = []

    def error(self, where: str, message: str) -> None:
        self.errors.append({"where": where, "message": message})

    def warn(self, where: str, message: str) -> None:
        self.warnings.append({"where": where, "message": message})

    def note(self, where: str, message: str) -> None:
        self.notes.append({"where": where, "message": message})

    def as_dict(self) -> dict[str, Any]:
        return {"errors": self.errors, "warnings": self.warnings, "notes": self.notes}


def load_yaml(path: Path) -> Any:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("PyYAML is required: install pyyaml or run in an environment that provides yaml") from exc
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_json(path: Path) -> Any:
    raw = path.read_bytes()
    try:
        import orjson  # type: ignore

        return orjson.loads(raw)
    except Exception:
        return json.loads(raw.decode("utf-8"))


def resolve_path(value: Any, base_dir: Path) -> Path | None:
    if not isinstance(value, str) or value == "":
        return None
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = base_dir / p
    return p


def sample_items(mapping: dict[str, Any], limit: int, seed: int) -> list[tuple[str, Any]]:
    items = list(mapping.items())
    if limit <= 0 or len(items) <= limit:
        return items
    rng = random.Random(seed)
    idxs = sorted(rng.sample(range(len(items)), limit))
    return [items[i] for i in idxs]


def is_base64_like(value: Any) -> bool:
    if isinstance(value, list) and value:
        value = value[0]
    if not isinstance(value, str) or not value.strip():
        return False
    candidate = "".join(value.split())
    missing = (-len(candidate)) % 4
    candidate += "=" * missing
    try:
        base64.urlsafe_b64decode(candidate.encode("ascii"))
        return True
    except (ValueError, binascii.Error, UnicodeEncodeError):
        return False


def inspect_image_asset(path: Path, reporter: Reporter, where: str, validate_sample: int) -> set[str] | None:
    """Return known image ids when cheap enough, otherwise None."""
    if path.suffix.lower() == ".json":
        try:
            data = load_json(path)
        except Exception as exc:
            reporter.error(where, f"could not read image JSON: {exc}")
            return set()
        if not isinstance(data, dict):
            reporter.error(where, "image JSON must be an object mapping image id to base64 string")
            return set()
        if validate_sample:
            for key, value in sample_items(data, validate_sample, seed=17):
                if not is_base64_like(value):
                    reporter.error(f"{where}.{key}", "value is not a decodable base64-like string")
        return set(str(k) for k in data.keys())

    # Parquet file or parquet directory.
    try:
        import pyarrow.parquet as pq  # type: ignore
    except Exception as exc:
        reporter.error(where, f"pyarrow is required to inspect parquet schema: {exc}")
        return None

    parquet_probe: Path | None = None
    if path.is_dir():
        for candidate in sorted(path.rglob("*.parquet")):
            parquet_probe = candidate
            break
        if parquet_probe is None:
            reporter.error(where, "parquet directory contains no .parquet files")
            return None
    else:
        parquet_probe = path

    try:
        schema_names = set(pq.ParquetFile(parquet_probe).schema_arrow.names)
    except Exception as exc:
        reporter.error(where, f"could not inspect parquet schema: {exc}")
        return None
    if "base64" not in schema_names:
        reporter.error(where, "parquet schema must include a 'base64' column")
    else:
        reporter.note(where, "parquet schema includes 'base64' column")

    return None


def load_parquet_index(path: Path, reporter: Reporter, where: str) -> set[str] | None:
    try:
        import pandas as pd  # type: ignore
    except Exception as exc:
        reporter.error(where, f"pandas is required for parquet image-id link checks: {exc}")
        return None
    try:
        df = pd.read_parquet(path, columns=["base64"])
    except Exception as exc:
        reporter.error(where, f"could not read parquet for image-id link checks: {exc}")
        return None
    return set(str(x) for x in df.index.tolist())


def validate_record(record_id: str, record: Any, group: str, where: str, reporter: Reporter) -> list[str]:
    image_ids: list[str] = []
    if not isinstance(record, dict):
        reporter.error(where, "instruction record must be an object")
        return image_ids
    for key in ("instruction", "answer"):
        if key not in record:
            reporter.error(where, f"missing required key '{key}'")
        elif not isinstance(record[key], str):
            reporter.error(where, f"'{key}' must be a string")
    rel = record.get("rel_ins_ids", [])
    if rel is not None and not (isinstance(rel, list) and all(isinstance(x, str) for x in rel)):
        reporter.error(where, "'rel_ins_ids' must be a list of strings when present")
    raw_image_ids = record.get("image_ids", [])
    if raw_image_ids is None:
        raw_image_ids = []
    if not isinstance(raw_image_ids, list) or not all(isinstance(x, str) for x in raw_image_ids):
        reporter.error(where, "'image_ids' must be a list of strings when present")
    else:
        image_ids = raw_image_ids
    if group in MULTIMODAL_GROUPS and not image_ids:
        reporter.error(where, f"{group} records should provide one or more image_ids")
    return image_ids


def validate_train_config(path: Path, instruction_ids: set[str], reporter: Reporter, where: str) -> None:
    try:
        cfg = load_json(path)
    except Exception as exc:
        reporter.error(where, f"could not read train config JSON: {exc}")
        return
    if not isinstance(cfg, dict):
        reporter.error(where, "train config must be an object mapping instruction id to related id list")
        return
    for key, value in sample_items(cfg, 100, seed=29):
        if key not in instruction_ids:
            reporter.warn(f"{where}.{key}", "train config key is not present in instruction JSON sample/all ids")
        if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
            reporter.error(f"{where}.{key}", "train config value must be a list of related instruction ids")
            continue
        missing = [x for x in value if x not in instruction_ids]
        if missing:
            reporter.warn(f"{where}.{key}", f"related ids not found in instruction JSON: {missing[:5]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an Otter/MIMIC-IT training data YAML.")
    parser.add_argument("yaml_path", help="Path to MIMIC-IT training YAML")
    parser.add_argument("--base-dir", default=None, help="Resolve relative paths against this directory; default is current working directory")
    parser.add_argument("--allow-missing-groups", action="store_true", help="Do not error when one of the four recognized groups is absent")
    parser.add_argument("--check-paths", action="store_true", help="Require path fields to exist")
    parser.add_argument("--check-records", action="store_true", help="Read instruction JSON files and validate sampled records")
    parser.add_argument("--check-image-links", action="store_true", help="Check sampled instruction image_ids against image JSON/parquet indexes when possible")
    parser.add_argument("--sample-records", type=int, default=50, help="Records per dataset to inspect; 0 means all records")
    parser.add_argument("--validate-base64-sample", type=int, default=0, help="Number of image JSON payloads to base64-check per image JSON asset")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON report")
    args = parser.parse_args(argv)

    reporter = Reporter()
    yaml_path = Path(args.yaml_path).expanduser()
    if not yaml_path.exists():
        reporter.error("yaml", f"file does not exist: {yaml_path}")
        report = reporter.as_dict()
        print(json.dumps(report, indent=2) if args.json else f"ERROR: {reporter.errors[0]['message']}")
        return 2

    base_dir = Path(args.base_dir).expanduser() if args.base_dir else Path.cwd()
    try:
        yaml_data = load_yaml(yaml_path)
    except Exception as exc:
        reporter.error("yaml", f"could not parse YAML: {exc}")
        yaml_data = None

    if not isinstance(yaml_data, dict):
        reporter.error("yaml", "top-level YAML value must be a mapping")
    else:
        present_groups = set(str(k) for k in yaml_data.keys())
        unexpected = sorted(present_groups - set(VALID_GROUPS))
        for group in unexpected:
            reporter.error(group, f"unexpected group; expected one of {list(VALID_GROUPS)}")
        if not args.allow_missing_groups:
            for group in VALID_GROUPS:
                if group not in present_groups:
                    reporter.error(group, "missing group; use GROUP: {} for an intentionally empty group")

        for group, datasets in yaml_data.items():
            group = str(group)
            where_group = group
            if group not in VALID_GROUPS:
                continue
            if datasets is None:
                reporter.error(where_group, "empty group must be written as {} rather than blank/null")
                continue
            if not isinstance(datasets, dict):
                reporter.error(where_group, "group value must be a mapping of dataset name to dataset fields")
                continue
            for dataset_name, fields in datasets.items():
                where = f"{group}.{dataset_name}"
                if not isinstance(fields, dict):
                    reporter.error(where, "dataset entry must be a mapping")
                    continue
                if "mimicit_path" not in fields:
                    reporter.error(where, "missing required mimicit_path")
                if group in MULTIMODAL_GROUPS and not fields.get("images_path"):
                    reporter.error(where, f"{group} dataset should provide images_path")
                if "num_samples" in fields and not isinstance(fields["num_samples"], int):
                    reporter.error(where, "num_samples must be an integer")
                elif "num_samples" not in fields:
                    reporter.warn(where, "num_samples omitted; set -1 to make use-all behavior explicit")
                if "task_description" in fields:
                    td = fields["task_description"]
                    if isinstance(td, str):
                        reporter.warn(where, "task_description is a string; use a list of strings to avoid character-level random choice")
                    elif not (isinstance(td, list) and all(isinstance(x, str) for x in td)):
                        reporter.error(where, "task_description must be a string or list of strings")

                resolved: dict[str, Path] = {}
                for field_name, value in fields.items():
                    if field_name.endswith("_path"):
                        path = resolve_path(value, base_dir)
                        if path is None:
                            reporter.error(f"{where}.{field_name}", "path value must be a non-empty string; omit optional empty paths")
                            continue
                        resolved[field_name] = path
                        if args.check_paths and not path.exists():
                            reporter.error(f"{where}.{field_name}", f"path does not exist after resolution: {path}")

                instruction_ids: set[str] = set()
                sampled_image_ids: list[str] = []
                mimicit_path = resolved.get("mimicit_path")
                instruction_data: dict[str, Any] | None = None
                if args.check_records and mimicit_path and mimicit_path.exists():
                    try:
                        mimicit = load_json(mimicit_path)
                    except Exception as exc:
                        reporter.error(f"{where}.mimicit_path", f"could not read instruction JSON: {exc}")
                        mimicit = None
                    if not isinstance(mimicit, dict) or not isinstance(mimicit.get("data"), dict):
                        reporter.error(f"{where}.mimicit_path", "instruction JSON must contain a top-level object key named 'data'")
                    else:
                        instruction_data = mimicit["data"]
                        instruction_ids = set(str(k) for k in instruction_data.keys())
                        for record_id, record in sample_items(instruction_data, args.sample_records, seed=11):
                            sampled_image_ids.extend(validate_record(str(record_id), record, group, f"{where}.data.{record_id}", reporter))

                train_config_path = resolved.get("train_config_path")
                if args.check_records and train_config_path and train_config_path.exists() and instruction_ids:
                    validate_train_config(train_config_path, instruction_ids, reporter, f"{where}.train_config_path")

                images_path = resolved.get("images_path")
                image_ids_known: set[str] | None = None
                if images_path and images_path.exists():
                    if images_path.suffix.lower() not in {".parquet", ".json"} and not images_path.is_dir():
                        reporter.error(f"{where}.images_path", "images_path must be .parquet, .json, or a parquet directory")
                    image_ids_known = inspect_image_asset(images_path, reporter, f"{where}.images_path", args.validate_base64_sample)
                    if args.check_image_links and images_path.suffix.lower() == ".parquet" or (args.check_image_links and images_path.is_dir()):
                        image_ids_known = load_parquet_index(images_path, reporter, f"{where}.images_path")
                if args.check_image_links and sampled_image_ids and image_ids_known is not None:
                    missing = sorted({img for img in sampled_image_ids if img not in image_ids_known})
                    if missing:
                        reporter.error(f"{where}.images_path", f"sampled instruction image_ids missing from image asset: {missing[:10]}")

    if args.json:
        print(json.dumps(reporter.as_dict(), indent=2))
    else:
        for item in reporter.errors:
            print(f"ERROR [{item['where']}]: {item['message']}")
        for item in reporter.warnings:
            print(f"WARN  [{item['where']}]: {item['message']}")
        for item in reporter.notes:
            print(f"NOTE  [{item['where']}]: {item['message']}")
        if not reporter.errors:
            print(f"OK: validation completed with {len(reporter.warnings)} warning(s)")
    return 1 if reporter.errors else 0


if __name__ == "__main__":
    sys.exit(main())
