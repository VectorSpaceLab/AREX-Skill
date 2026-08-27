#!/usr/bin/env python3
"""Validate DreamOmni2 model-path inputs without downloading weights."""

from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_BASE_MODEL = "black-forest-labs/FLUX.1-Kontext-dev"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check DreamOmni2 model paths.")
    parser.add_argument("--vlm-path", default="models/vlm-model", help="VLM checkpoint directory or hub id.")
    parser.add_argument(
        "--edit-lora-path",
        default="models/edit_lora",
        help="Editing LoRA directory or hub id.",
    )
    parser.add_argument(
        "--gen-lora-path",
        default="models/gen_lora",
        help="Generation LoRA directory or hub id.",
    )
    parser.add_argument(
        "--base-model-path",
        default=DEFAULT_BASE_MODEL,
        help="Base DreamOmni2 model directory or hub id.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with a non-zero status if a local path is missing.",
    )
    return parser.parse_args()


def classify_path(value: str) -> str:
    path = Path(value).expanduser()
    if path.exists():
        return "local-ok"
    if value == DEFAULT_BASE_MODEL:
        return "hub-id"
    if "/" in value or value.startswith(("./", "../", "/", "~")):
        return "local-missing"
    if path.suffix:
        return "local-missing"
    return "hub-or-remote"


def main() -> int:
    args = parse_args()
    rows = [
        ("vlm_path", args.vlm_path),
        ("edit_lora_path", args.edit_lora_path),
        ("gen_lora_path", args.gen_lora_path),
        ("base_model_path", args.base_model_path),
    ]

    failures = 0
    for label, value in rows:
        status = classify_path(value)
        print(f"{label}: {value} -> {status}")
        if status == "local-missing":
            failures += 1

    if args.strict and failures:
        print("One or more local model paths are missing.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
