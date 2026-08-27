#!/usr/bin/env python3
"""Read-only preflight checks for sd-scripts dataset configs and metadata."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".PNG",
    ".JPG",
    ".JPEG",
    ".WEBP",
    ".BMP",
    ".avif",
    ".AVIF",
    ".jxl",
    ".JXL",
}
LATENT_CACHE_SUFFIX_HINTS = (".npz",)

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - fallback for older Python
    tomllib = None


class Finding:
    def __init__(self, level: str, location: str, message: str):
        self.level = level
        self.location = location
        self.message = message

    def __str__(self) -> str:
        return f"[{self.level}] {self.location}: {self.message}"


def add(finding_list: list[Finding], level: str, location: str, message: str) -> None:
    finding_list.append(Finding(level, location, message))


def load_config(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    elif suffix == ".toml":
        if tomllib is None:
            raise RuntimeError("TOML config requires Python 3.11+ tomllib or use JSON config")
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    else:
        raise RuntimeError("dataset config must end with .toml or .json")
    if not isinstance(data, dict):
        raise RuntimeError("dataset config root must be an object/table")
    return data


def resolve_config_path(value: Any, base: Path) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return base / path


def is_supported_image(path: Path) -> bool:
    return path.suffix in IMAGE_EXTENSIONS


def glob_same_basename(path: Path) -> list[Path]:
    parent = path.parent if str(path.parent) else Path(".")
    stem = path.stem if path.suffix else path.name
    if not parent.exists():
        return []
    matches: list[Path] = []
    for extension in IMAGE_EXTENSIONS:
        matches.extend(parent.glob(stem + extension))
    return matches


def has_latent_cache_candidate(path: Path) -> bool:
    parent = path.parent if str(path.parent) else Path(".")
    stem = path.stem if path.suffix else path.name
    if not parent.exists():
        return False
    return any(parent.glob(stem + "*.npz"))


def load_metadata(path: Path) -> tuple[Any, list[Finding]]:
    findings: list[Finding] = []
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        entries: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for line_no, raw_line in enumerate(handle, 1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError as exc:
                    add(findings, "ERROR", f"{path}:{line_no}", f"invalid JSONL line: {exc}")
                    continue
                if not isinstance(item, dict):
                    add(findings, "ERROR", f"{path}:{line_no}", "JSONL line must be an object")
                    continue
                entries.append(item)
        return entries, findings
    with path.open("r", encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError as exc:
            add(findings, "ERROR", str(path), f"invalid JSON: {exc}")
            return None, findings
    return data, findings


def validate_image_size(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(item, int) and item > 0 for item in value)
    )


def check_metadata_entries(
    metadata: Any,
    metadata_path: Path,
    image_dir: Path | None,
    metadata_root: Path,
    findings: list[Finding],
) -> None:
    entries: list[tuple[str, dict[str, Any], str]] = []
    if isinstance(metadata, dict):
        if not metadata:
            add(findings, "WARN", str(metadata_path), "metadata object has no entries; sd-scripts skips empty subsets")
        for image_key, value in metadata.items():
            if not isinstance(image_key, str) or not image_key:
                add(findings, "ERROR", str(metadata_path), "metadata JSON keys must be non-empty image path strings")
                continue
            if not isinstance(value, dict):
                add(findings, "ERROR", f"{metadata_path}:{image_key}", "metadata value must be an object")
                continue
            entries.append((image_key, value, f"{metadata_path}:{image_key}"))
    elif isinstance(metadata, list):
        if not metadata:
            add(findings, "WARN", str(metadata_path), "metadata JSONL has no entries; sd-scripts skips empty subsets")
        for index, value in enumerate(metadata, 1):
            location = f"{metadata_path}:{index}"
            image_key = value.get("image_path") if isinstance(value, dict) else None
            if not isinstance(image_key, str) or not image_key:
                add(findings, "ERROR", location, "JSONL entry requires non-empty string image_path")
                continue
            entries.append((image_key, value, location))
    else:
        add(findings, "ERROR", str(metadata_path), "metadata must be a JSON object or JSONL object stream")
        return

    missing_count = 0
    unsupported_count = 0
    no_size_missing_count = 0
    sample_missing: list[str] = []
    for image_key, item, location in entries:
        caption = item.get("caption")
        tags = item.get("tags")
        image_size = item.get("image_size")
        if caption is not None and not isinstance(caption, str):
            add(findings, "ERROR", location, "caption must be a string when present")
        if tags is not None and not isinstance(tags, str):
            add(findings, "ERROR", location, "tags must be a string when present")
        if image_size is not None and not validate_image_size(image_size):
            add(findings, "ERROR", location, "image_size must be [positive_width, positive_height]")
        if "width" in item or "height" in item:
            if not (isinstance(item.get("width"), int) and isinstance(item.get("height"), int)):
                add(findings, "ERROR", location, "width and height must both be integers when used")

        raw_path = Path(image_key).expanduser()
        if raw_path.is_absolute():
            resolved = raw_path
        elif image_dir is not None:
            resolved = image_dir / raw_path
        else:
            add(findings, "ERROR", location, "relative metadata image_path requires subset image_dir")
            resolved = metadata_root / raw_path

        image_exists = resolved.exists() or bool(glob_same_basename(resolved))
        cache_exists = has_latent_cache_candidate(resolved)
        if resolved.suffix and resolved.suffix not in IMAGE_EXTENSIONS and not resolved.suffix.lower() == ".npz":
            unsupported_count += 1
        if not image_exists and not cache_exists:
            missing_count += 1
            if len(sample_missing) < 5:
                sample_missing.append(image_key)
            if image_size is None:
                no_size_missing_count += 1

    if unsupported_count:
        add(findings, "WARN", str(metadata_path), f"{unsupported_count} metadata paths use unsupported image suffixes")
    if missing_count:
        add(findings, "WARN", str(metadata_path), f"{missing_count} metadata entries have no image/cache candidate; examples: {sample_missing}")
    if no_size_missing_count:
        add(findings, "ERROR", str(metadata_path), f"{no_size_missing_count} missing image/cache entries also lack image_size")


def check_subset(
    subset: dict[str, Any],
    location: str,
    config_base: Path,
    metadata_root: Path,
    findings: list[Finding],
) -> str:
    has_metadata = "metadata_file" in subset
    has_conditioning = "conditioning_data_dir" in subset
    image_dir = resolve_config_path(subset.get("image_dir"), config_base)

    if has_conditioning:
        mode = "controlnet"
    elif has_metadata:
        mode = "fine-tuning"
    else:
        mode = "dreambooth"

    if image_dir is not None and not image_dir.is_dir():
        level = "WARN" if has_metadata else "ERROR"
        add(findings, level, f"{location}.image_dir", f"directory not found: {image_dir}")
    elif image_dir is not None:
        images = [path for path in image_dir.iterdir() if path.is_file() and is_supported_image(path)]
        if not images and mode in {"dreambooth", "controlnet"}:
            add(findings, "WARN", f"{location}.image_dir", "no supported image files directly under directory")

    num_repeats = subset.get("num_repeats", 1)
    if "num_repeats" in subset and not isinstance(num_repeats, int):
        add(findings, "ERROR", f"{location}.num_repeats", "num_repeats must be an integer")
    elif isinstance(num_repeats, int) and num_repeats < 1:
        add(findings, "WARN", f"{location}.num_repeats", "subset is ignored when num_repeats < 1")

    if mode == "dreambooth":
        if image_dir is None:
            add(findings, "ERROR", location, "DreamBooth subset requires image_dir")
        return mode

    if mode == "controlnet":
        if image_dir is None:
            add(findings, "ERROR", location, "ControlNet subset requires image_dir")
        conditioning_dir = resolve_config_path(subset.get("conditioning_data_dir"), config_base)
        if conditioning_dir is None or not conditioning_dir.is_dir():
            add(findings, "ERROR", f"{location}.conditioning_data_dir", f"conditioning directory not found: {conditioning_dir}")
        elif image_dir is not None and image_dir.is_dir():
            image_stems = {path.stem for path in image_dir.iterdir() if path.is_file() and is_supported_image(path)}
            conditioning_stems = {path.stem for path in conditioning_dir.iterdir() if path.is_file() and is_supported_image(path)}
            missing = sorted(image_stems - conditioning_stems)
            extra = sorted(conditioning_stems - image_stems)
            if missing:
                add(findings, "ERROR", location, f"missing conditioning images for {len(missing)} source images; examples: {missing[:5]}")
            if extra:
                add(findings, "WARN", location, f"extra conditioning images without source pair: {extra[:5]}")
        if subset.get("random_crop") is True:
            add(findings, "ERROR", f"{location}.random_crop", "random_crop is not supported for ControlNet datasets")
        return mode

    metadata_file = resolve_config_path(subset.get("metadata_file"), config_base)
    if metadata_file is None:
        add(findings, "ERROR", location, "fine-tuning subset requires metadata_file")
        return mode
    if not metadata_file.is_file():
        add(findings, "ERROR", f"{location}.metadata_file", f"metadata file not found: {metadata_file}")
        return mode
    metadata, metadata_findings = load_metadata(metadata_file)
    findings.extend(metadata_findings)
    if not any(item.level == "ERROR" for item in metadata_findings):
        check_metadata_entries(metadata, metadata_file, image_dir, metadata_root, findings)
    return mode


def check_dataset_config(config: dict[str, Any], config_base: Path, metadata_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    datasets = config.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        add(findings, "ERROR", "datasets", "config must contain a non-empty datasets array")
        return findings
    if "general" in config and not isinstance(config["general"], dict):
        add(findings, "ERROR", "general", "general must be a table/object when present")

    for dataset_index, dataset in enumerate(datasets):
        dataset_location = f"datasets[{dataset_index}]"
        if not isinstance(dataset, dict):
            add(findings, "ERROR", dataset_location, "dataset entry must be a table/object")
            continue
        subsets = dataset.get("subsets")
        if not isinstance(subsets, list) or not subsets:
            add(findings, "ERROR", f"{dataset_location}.subsets", "dataset must contain at least one subset")
            continue
        resolution = dataset.get("resolution", config.get("general", {}).get("resolution"))
        if resolution is None:
            add(findings, "WARN", dataset_location, "resolution is not set in dataset or general config")
        elif not (
            isinstance(resolution, int)
            or (isinstance(resolution, list) and len(resolution) == 2 and all(isinstance(item, int) for item in resolution))
        ):
            add(findings, "WARN", dataset_location, "resolution is usually an integer or [width, height] in dataset configs")
        validation_split = dataset.get("validation_split", config.get("general", {}).get("validation_split", 0.0))
        if validation_split is not None and not isinstance(validation_split, (int, float)):
            add(findings, "ERROR", f"{dataset_location}.validation_split", "validation_split must be numeric")
        elif isinstance(validation_split, (int, float)) and not 0.0 <= float(validation_split) <= 1.0:
            add(findings, "WARN", f"{dataset_location}.validation_split", "validation_split outside [0.0, 1.0] is ignored")
        subset_modes: list[str] = []
        for subset_index, subset in enumerate(subsets):
            subset_location = f"{dataset_location}.subsets[{subset_index}]"
            if not isinstance(subset, dict):
                add(findings, "ERROR", subset_location, "subset entry must be a table/object")
                continue
            subset_modes.append(check_subset(subset, subset_location, config_base, metadata_root, findings))
        if len(set(subset_modes)) > 1:
            add(findings, "ERROR", dataset_location, f"mixed subset modes in one dataset: {sorted(set(subset_modes))}")
        if any(isinstance(subset, dict) and "validation_split" in subset for subset in subsets):
            add(findings, "WARN", dataset_location, "subset-level validation_split may not create validation data; prefer dataset-level validation_split")
    return findings


def print_summary(findings: Iterable[Finding]) -> tuple[int, int]:
    errors = 0
    warnings = 0
    for finding in findings:
        print(finding)
        if finding.level == "ERROR":
            errors += 1
        elif finding.level == "WARN":
            warnings += 1
    print(f"Summary: {errors} error(s), {warnings} warning(s)")
    return errors, warnings


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only preflight validation for sd-scripts dataset TOML/JSON and metadata.")
    parser.add_argument("--dataset-config", required=True, type=Path, help="Path to sd-scripts dataset .toml or .json config")
    parser.add_argument(
        "--config-base",
        type=Path,
        default=Path.cwd(),
        help="Base directory for relative paths in the config. Default: current working directory, matching sd-scripts behavior.",
    )
    parser.add_argument(
        "--metadata-root",
        type=Path,
        default=None,
        help="Fallback base for relative metadata image paths when image_dir is absent. Default: config base.",
    )
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when warnings are present")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    config_path = args.dataset_config.expanduser()
    if not config_path.is_file():
        print(f"[ERROR] dataset config not found: {config_path}", file=sys.stderr)
        return 2
    config_base = args.config_base.expanduser().resolve()
    metadata_root = (args.metadata_root.expanduser().resolve() if args.metadata_root else config_base)
    try:
        config = load_config(config_path)
    except Exception as exc:
        print(f"[ERROR] {config_path}: {exc}", file=sys.stderr)
        return 2
    findings = check_dataset_config(config, config_base, metadata_root)
    errors, warnings = print_summary(findings)
    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
