#!/usr/bin/env python3
"""Validate raw or processed HunyuanVideo-I2V dataset layouts.

Raw mode checks a meta_file.list and every referenced JSON. Processed mode
checks the json_path directory consumed by LoRA training.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            value = json.load(handle)
        if not isinstance(value, dict):
            return None, "top-level JSON is not an object"
        return value, None
    except Exception as exc:  # pragma: no cover - diagnostic path
        return None, f"{type(exc).__name__}: {exc}"


def _resolve_candidate(path_text: str, base_dir: Path, list_parent: Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    from_base = (base_dir / path).resolve()
    if from_base.exists():
        return from_base
    return (list_parent / path).resolve()


def check_raw(meta_file_list: Path, base_dir: Path) -> list[str]:
    errors: list[str] = []
    if not meta_file_list.exists():
        return [f"meta_file.list not found: {meta_file_list}"]
    list_parent = meta_file_list.parent
    for line_no, raw in enumerate(meta_file_list.read_text(encoding="utf-8").splitlines(), start=1):
        item = raw.strip()
        if not item:
            continue
        path = _resolve_candidate(item, base_dir, list_parent)
        if not path.exists():
            errors.append(f"line {line_no}: listed JSON not found: {path}")
            continue
        data, err = _load_json(path)
        if err:
            errors.append(f"line {line_no}: invalid JSON {path}: {err}")
            continue
        assert data is not None
        if not data.get("video_path"):
            errors.append(f"line {line_no}: missing video_path in {path}")
        raw_caption = data.get("raw_caption")
        if not isinstance(raw_caption, dict) or not raw_caption.get("long caption"):
            errors.append(f"line {line_no}: missing raw_caption.long caption in {path}")
    return errors


def check_processed(json_dir: Path, require_npy: bool) -> list[str]:
    errors: list[str] = []
    if not json_dir.exists():
        return [f"processed json directory not found: {json_dir}"]
    files = sorted(json_dir.glob("*.json"))
    if not files:
        errors.append(f"no processed JSON files found in {json_dir}")
    for path in files:
        data, err = _load_json(path)
        if err:
            errors.append(f"invalid JSON {path}: {err}")
            continue
        assert data is not None
        for key in ["video_id", "latent_shape", "prompt", "npy_save_path"]:
            if key not in data:
                errors.append(f"{path}: missing {key}")
        latent_shape = data.get("latent_shape")
        if not isinstance(latent_shape, list) or len(latent_shape) < 5:
            errors.append(f"{path}: latent_shape must be a list with at least 5 dimensions")
        # The training loader derives height and width from latent_shape, so height/width
        # fields are useful but not required in the processed JSON itself.
        npy_path = data.get("npy_save_path")
        if require_npy and npy_path:
            npy = Path(str(npy_path))
            if not npy.is_absolute():
                npy = (json_dir / npy).resolve()
            if not npy.exists():
                errors.append(f"{path}: npy_save_path does not exist: {npy}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate HunyuanVideo-I2V raw or processed dataset layouts")
    parser.add_argument("--mode", choices=["raw", "processed"], required=True)
    parser.add_argument("--meta-file-list", default=None, help="Raw meta_file.list path")
    parser.add_argument("--base-dir", default=".", help="Base directory for relative raw JSON paths, usually the repo root")
    parser.add_argument("--json-dir", default=None, help="Processed json_path directory")
    parser.add_argument("--no-require-npy", action="store_true", help="Do not require npy_save_path files to exist in processed mode")
    args = parser.parse_args()

    if args.mode == "raw":
        if not args.meta_file_list:
            parser.error("--meta-file-list is required in raw mode")
        errors = check_raw(Path(args.meta_file_list).expanduser().resolve(), Path(args.base_dir).expanduser().resolve())
    else:
        if not args.json_dir:
            parser.error("--json-dir is required in processed mode")
        errors = check_processed(Path(args.json_dir).expanduser().resolve(), require_npy=not args.no_require_npy)

    if errors:
        print("Dataset layout errors:")
        for err in errors:
            print(f"- {err}")
        return 1
    print("Dataset layout OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
