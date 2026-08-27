#!/usr/bin/env python
"""Validate LMFlow multimodal training data.

This checker inspects legacy multimodal JSON arrays that contain conversation
turns and optional image filenames. It does not download assets or start a
model job.

Examples:
  python scripts/validate_multimodal_dataset.py path/to/train.json --image-folder path/to/images
  python scripts/validate_multimodal_dataset.py path/to/dataset_dir --sep-style v1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

MESSAGE_KEYS = {"from", "value"}
ALLOWED_ROLES = {"human", "gpt", "user", "assistant", "system"}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def iter_json_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if target.is_dir():
        return sorted(p for p in target.glob("*.json") if p.is_file())
    return []


def validate_message(message: Any, path: Path, sample_index: int, message_index: int) -> list[str]:
    errors: list[str] = []
    if not isinstance(message, dict):
        return [f"{path}:{sample_index}:{message_index}: each conversation turn must be an object"]
    missing = sorted(MESSAGE_KEYS - set(message))
    if missing:
        errors.append(f"{path}:{sample_index}:{message_index}: missing keys {missing}")
        return errors
    role = message.get("from")
    value = message.get("value")
    if role not in ALLOWED_ROLES:
        errors.append(f"{path}:{sample_index}:{message_index}: unsupported role {role!r}")
    if not isinstance(value, str):
        errors.append(f"{path}:{sample_index}:{message_index}: value must be a string")
    return errors


def validate_sample(sample: Any, path: Path, sample_index: int, image_folder: Path | None, require_image: bool, sep_style: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(sample, dict):
        return [f"{path}:{sample_index}: each sample must be an object"]

    conversations = sample.get("conversations")
    if not isinstance(conversations, list) or not conversations:
        return [f"{path}:{sample_index}: conversations must be a non-empty list"]

    for message_index, message in enumerate(conversations):
        errors.extend(validate_message(message, path, sample_index, message_index))

    image_name = sample.get("image")
    if image_name is None:
        if require_image:
            errors.append(f"{path}:{sample_index}: image field is required")
    else:
        if not isinstance(image_name, str) or not image_name.strip():
            errors.append(f"{path}:{sample_index}: image must be a non-empty string when present")
        elif image_folder is not None and not (image_folder / image_name).is_file():
            errors.append(f"{path}:{sample_index}: missing image file {image_folder / image_name}")

    if sep_style == "plain":
        if len(conversations) != 2:
            errors.append(f"{path}:{sample_index}: plain style expects exactly 2 turns")
        elif "<image>" not in conversations[0].get("value", ""):
            errors.append(f"{path}:{sample_index}: plain style expects <image> in the first turn")
    elif sep_style == "v1":
        if len(conversations) < 2:
            errors.append(f"{path}:{sample_index}: v1 style expects at least 2 turns")
        elif conversations[0].get("from") not in {"human", "user"}:
            errors.append(f"{path}:{sample_index}: v1 style should start with a human/user turn")

    return errors


def validate_file(path: Path, image_folder: Path | None, require_image: bool, sep_style: str) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:  # noqa: BLE001
        return [f"{path}: invalid JSON: {exc}"]

    if not isinstance(payload, list):
        return [f"{path}: top-level value must be a list of multimodal samples"]

    errors: list[str] = []
    for idx, sample in enumerate(payload):
        errors.extend(validate_sample(sample, path, idx, image_folder, require_image, sep_style))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate LMFlow multimodal training datasets.")
    parser.add_argument("path", help="A JSON file or a directory containing JSON files.")
    parser.add_argument("--image-folder", default=None, help="Folder that contains referenced image files.")
    parser.add_argument("--require-image", action="store_true", help="Fail when a sample does not define image.")
    parser.add_argument("--sep-style", choices=["plain", "v1"], default="v1", help="Conversation separator style to validate.")
    args = parser.parse_args()

    target = Path(args.path)
    files = iter_json_files(target)
    if not files:
        print(f"No JSON files found at {target}")
        return 2

    image_folder = Path(args.image_folder) if args.image_folder else None
    if image_folder is not None and not image_folder.exists():
        print(f"{image_folder}: image folder does not exist")
        return 2

    errors: list[str] = []
    for file in files:
        errors.extend(validate_file(file, image_folder, args.require_image, args.sep_style))

    if errors:
        for error in errors:
            print(error)
        return 1

    print(f"OK: validated {len(files)} file(s) at {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
