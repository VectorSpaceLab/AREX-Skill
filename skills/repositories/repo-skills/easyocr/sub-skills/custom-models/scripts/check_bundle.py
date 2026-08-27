#!/usr/bin/env python3
"""Validate an EasyOCR custom recognition bundle triad."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import yaml

REQUIRED_KEYS = ("lang_list", "character_list")
OPTIONAL_KEYS = ("imgH", "network_params")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an EasyOCR custom recognition bundle.")
    parser.add_argument("bundle", help="Bundle stem or directory containing stem.{pth,yaml,py}.")
    return parser.parse_args()


def resolve_bundle(path_text: str) -> tuple[Path, str]:
    path = Path(path_text).expanduser()
    if path.is_dir():
        stems = {p.stem for p in path.iterdir() if p.suffix in {".pth", ".yaml", ".py"}}
        if len(stems) != 1:
            raise SystemExit(f"Expected exactly one bundle stem in {path}, found: {sorted(stems)}")
        return path, stems.pop()
    if path.suffix:
        return path.parent, path.stem
    return path.parent if path.parent != Path('.') else Path.cwd(), path.name


def file_lines(paths: Iterable[Path]) -> str:
    return ", ".join(str(path.name) for path in paths)


def main() -> int:
    args = parse_args()
    bundle_dir, stem = resolve_bundle(args.bundle)
    pth = bundle_dir / f"{stem}.pth"
    yaml_path = bundle_dir / f"{stem}.yaml"
    py_path = bundle_dir / f"{stem}.py"

    missing = [path.name for path in (pth, yaml_path, py_path) if not path.exists()]
    if missing:
        raise SystemExit(f"Missing bundle files for stem '{stem}': {', '.join(missing)}")

    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"YAML file {yaml_path} did not parse to a mapping.")

    missing_keys = [key for key in REQUIRED_KEYS if key not in data]
    if missing_keys:
        raise SystemExit(f"YAML file {yaml_path} is missing keys: {', '.join(missing_keys)}")

    print(f"bundle_dir: {bundle_dir}")
    print(f"stem: {stem}")
    print(f"files: {file_lines((pth, yaml_path, py_path))}")
    for key in REQUIRED_KEYS + OPTIONAL_KEYS:
        if key in data:
            print(f"{key}: {data[key]!r}")

    print(f"suggested Reader call: easyocr.Reader([...], recog_network='{stem}', user_network_directory='{bundle_dir}', model_storage_directory='<weights-dir>')")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
