#!/usr/bin/env python3
"""Validate the repo's JSON dataset shapes without loading model weights."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

IMAGE_KEYS = ("image", "images")
VIDEO_KEYS = ("video", "videos")


def load_json(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError("dataset root must be a JSON array")
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("each dataset item must be a JSON object")
    return data


def detect_mode(sample: dict[str, Any]) -> str:
    if "conversations" in sample:
        return "sft"
    if {"prompt", "chosen", "rejected"}.issubset(sample):
        return "dpo"
    if "label" in sample:
        return "cls"
    return "unknown"


def iter_media_paths(sample: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for key in IMAGE_KEYS + VIDEO_KEYS:
        value = sample.get(key)
        if isinstance(value, str):
            paths.append(value)
        elif isinstance(value, list):
            paths.extend([str(item) for item in value])
    return paths


def infer_sample_kind(sample: dict[str, Any]) -> str:
    for key in IMAGE_KEYS:
        if key in sample:
            return "image"
    for key in VIDEO_KEYS:
        if key in sample:
            return "video"
    return "text"


def validate_sft_like(sample: dict[str, Any], *, mode: str, model_type: str | None, enable_reasoning: bool) -> list[str]:
    issues: list[str] = []
    convs = sample.get("conversations")
    if not isinstance(convs, list) or not convs:
        return ["missing or invalid conversations"]
    if mode == "grpo" and len(convs) != 2:
        issues.append("GRPO samples are expected to contain exactly one user/assistant exchange")
    if len(convs) % 2 != 0:
        issues.append("conversation list should alternate human/gpt turns")
    for idx, turn in enumerate(convs):
        if not isinstance(turn, dict):
            issues.append(f"turn {idx} is not an object")
            continue
        if idx % 2 == 0:
            if turn.get("from") != "human":
                issues.append(f"turn {idx} should be from human")
        else:
            if turn.get("from") != "gpt":
                issues.append(f"turn {idx} should be from gpt")
    if enable_reasoning and model_type and model_type in {"qwen3_vl_thinking"}:
        for idx, turn in enumerate(convs[1::2], start=1):
            if not isinstance(turn.get("reasoning"), str) or not turn["reasoning"].strip():
                issues.append(f"assistant turn {idx} needs non-empty reasoning")
    return issues


def validate_dpo(sample: dict[str, Any], *, model_type: str | None, enable_reasoning: bool) -> list[str]:
    issues: list[str] = []
    for key in ("prompt", "chosen", "rejected"):
        if not isinstance(sample.get(key), str) or not sample[key].strip():
            issues.append(f"missing or empty {key}")
    chosen_reasoning = sample.get("chosen_reasoning")
    rejected_reasoning = sample.get("rejected_reasoning")
    has_chosen = isinstance(chosen_reasoning, str) and chosen_reasoning.strip()
    has_rejected = isinstance(rejected_reasoning, str) and rejected_reasoning.strip()
    if has_chosen != has_rejected:
        issues.append("chosen_reasoning and rejected_reasoning must appear together")
    if enable_reasoning and model_type and model_type in {"qwen3_vl_thinking"} and not has_chosen:
        issues.append("reasoning-enabled Qwen3-VL Thinking DPO data needs paired reasoning fields")
    return issues


def validate_cls(sample: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if "label" not in sample:
        issues.append("missing label")
    else:
        if not isinstance(sample["label"], str):
            issues.append("label should be a string such as 'A' or 'B'")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--mode", choices=["auto", "sft", "grpo", "dpo", "cls"], default="auto")
    parser.add_argument("--model-type", default=None, help="Optional Qwen model_type such as qwen3_5")
    parser.add_argument("--image-folder", type=Path, default=None)
    parser.add_argument("--enable-reasoning", action="store_true")
    parser.add_argument("--check-media-paths", action="store_true", help="Check that relative media paths exist")
    args = parser.parse_args()

    data = load_json(args.dataset)
    issues: list[str] = []

    for index, sample in enumerate(data):
        if not isinstance(sample.get("id", index), (str, int)):
            issues.append(f"sample {index}: id should be a scalar value")

        mode = args.mode
        if mode == "auto":
            mode = detect_mode(sample)
        if mode == "sft":
            issues.extend(f"sample {index}: {msg}" for msg in validate_sft_like(sample, mode="sft", model_type=args.model_type, enable_reasoning=args.enable_reasoning))
        elif mode == "grpo":
            issues.extend(f"sample {index}: {msg}" for msg in validate_sft_like(sample, mode="grpo", model_type=args.model_type, enable_reasoning=args.enable_reasoning))
        elif mode == "dpo":
            issues.extend(f"sample {index}: {msg}" for msg in validate_dpo(sample, model_type=args.model_type, enable_reasoning=args.enable_reasoning))
        elif mode == "cls":
            issues.extend(f"sample {index}: {msg}" for msg in validate_cls(sample))
        else:
            issues.append(f"sample {index}: could not infer dataset mode")

        if args.check_media_paths and args.image_folder is not None:
            for media_path in iter_media_paths(sample):
                p = Path(media_path)
                if not p.exists() and not media_path.startswith("http"):
                    candidate = args.image_folder / media_path
                    if not candidate.exists():
                        issues.append(f"sample {index}: missing media path {media_path!r}")

        sample_kind = infer_sample_kind(sample)
        if mode in {"sft", "grpo", "dpo"} and sample_kind == "text":
            continue

    if issues:
        for issue in issues:
            print(issue)
        return 1

    print(f"ok: validated {len(data)} samples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
