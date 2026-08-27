#!/usr/bin/env python3
"""Validate a LLaVA training JSON list.

The script checks the basic schema for custom training data without launching
training or touching GPU state.

Example:
    python scripts/validate_training_json.py data.json --image-folder images
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


VALID_SPEAKERS = {"human", "gpt"}


def validate_sample(sample: dict[str, Any], image_folder: Path | None, require_image_token: bool) -> list[str]:
    errors: list[str] = []
    if not isinstance(sample, dict):
        return ["sample is not an object"]
    if "id" not in sample:
        errors.append("missing id")
    if "conversations" not in sample:
        errors.append("missing conversations")
        return errors
    if not isinstance(sample["conversations"], list) or not sample["conversations"]:
        errors.append("conversations must be a non-empty list")
        return errors

    prev_from = None
    for idx, turn in enumerate(sample["conversations"]):
        if not isinstance(turn, dict):
            errors.append(f"turn {idx} is not an object")
            continue
        speaker = turn.get("from")
        value = turn.get("value")
        if speaker not in VALID_SPEAKERS:
            errors.append(f"turn {idx} has invalid from={speaker!r}")
        if not isinstance(value, str):
            errors.append(f"turn {idx} missing string value")
        if prev_from == speaker and speaker in VALID_SPEAKERS:
            errors.append(f"turn {idx} repeats speaker {speaker!r} instead of alternating")
        prev_from = speaker
        if speaker == "human" and require_image_token and "image" in sample and "<image>" not in value:
            errors.append("multimodal sample is missing <image> in the human prompt")

    if "image" in sample and image_folder is not None:
        image_path = image_folder / str(sample["image"])
        if not image_path.exists():
            errors.append(f"image path does not exist: {image_path}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a LLaVA training JSON list.")
    parser.add_argument("json_file", type=Path, help="Path to a JSON file containing a list of samples")
    parser.add_argument("--image-folder", type=Path, help="Optional folder that sample image paths should resolve against")
    parser.add_argument("--allow-missing-image-token", action="store_true", help="Do not require <image> in multimodal human prompts")
    args = parser.parse_args()

    try:
        data = json.loads(args.json_file.read_text())
    except Exception as exc:  # noqa: BLE001
        print(f"INVALID: cannot parse JSON: {exc}")
        return 1

    if not isinstance(data, list):
        print("INVALID: top-level JSON must be a list")
        return 1

    all_errors: list[str] = []
    for idx, sample in enumerate(data):
        errors = validate_sample(sample, args.image_folder, not args.allow_missing_image_token)
        if errors:
            all_errors.append(f"sample {idx}: " + "; ".join(errors))

    if all_errors:
        print("INVALID")
        for err in all_errors:
            print(err)
        return 1

    print(f"VALID: {len(data)} samples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
