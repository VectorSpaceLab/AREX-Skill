#!/usr/bin/env python3
"""Validate VLM-R1 JSONL datasets and optional image-root mappings.

Examples:
  python scripts/validate_jsonl_dataset.py --data-file-paths data.jsonl --image-roots images
  python scripts/validate_jsonl_dataset.py --data-file-paths a.jsonl:b.jsonl --image-roots root-a:root-b
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

KNOWN_REWARD_METHODS = {
    "default",
    "mcq",
    "yes_no",
    "llm",
    "map",
    "math",
    "weighted_sum",
    "od_ap",
    "od_ap50",
    "odLength",
    "all_match",
}


@dataclass
class Summary:
    rows: int = 0
    image_rows: int = 0
    single_image_rows: int = 0
    multi_image_rows: int = 0
    text_only_rows: int = 0
    errors: int = 0
    warnings: int = 0


@dataclass
class Issue:
    level: str
    file: str
    line: int | None
    message: str


def split_colon_list(value: str | None) -> list[str]:
    if value is None:
        return []
    parts = [segment.strip() for segment in value.split(":")]
    if any(part == "" for part in parts):
        raise ValueError("Empty entry found in a colon-separated list")
    return parts


def add_issue(
    issues: list[Issue],
    summary: Summary,
    level: str,
    file_label: str,
    line_no: int | None,
    message: str,
    strict: bool,
) -> None:
    effective_level = "error" if strict and level == "warning" else level
    issues.append(Issue(effective_level, file_label, line_no, message))
    if effective_level == "error":
        summary.errors += 1
    else:
        summary.warnings += 1


def normalize_images(value: Any) -> list[str]:
    if isinstance(value, str):
        images = [value]
    elif isinstance(value, list):
        images = value
    else:
        raise ValueError(f"image must be a string or a list of strings, got {type(value).__name__}")

    if not images:
        raise ValueError("image must not be empty")

    normalized: list[str] = []
    for index, item in enumerate(images):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"image[{index}] must be a non-empty string")
        normalized.append(item)
    return normalized


def count_image_tokens(text: Any) -> int:
    return text.count("<image>") if isinstance(text, str) else 0


def validate_row(
    row: dict[str, Any],
    file_label: str,
    line_no: int,
    image_root: Path | None,
    summary: Summary,
    issues: list[Issue],
    strict: bool,
) -> None:
    image_value = row.get("image")
    images: list[str] = []

    if image_value is None:
        summary.text_only_rows += 1
    else:
        try:
            images = normalize_images(image_value)
        except ValueError as exc:
            add_issue(issues, summary, "error", file_label, line_no, f"invalid image field: {exc}", strict)
            return

        summary.image_rows += 1
        if len(images) == 1:
            summary.single_image_rows += 1
        else:
            summary.multi_image_rows += 1

        for rel_image in images:
            if os.path.isabs(rel_image):
                add_issue(
                    issues,
                    summary,
                    "error",
                    file_label,
                    line_no,
                    f"image path must be relative, got absolute path {rel_image!r}",
                    strict,
                )
            if image_root is not None:
                candidate = image_root / rel_image
                if not candidate.exists():
                    add_issue(
                        issues,
                        summary,
                        "error",
                        file_label,
                        line_no,
                        f"missing image file after join: {candidate}",
                        strict,
                    )

    conversations = row.get("conversations")
    if not isinstance(conversations, list):
        add_issue(issues, summary, "error", file_label, line_no, "conversations must be a list", strict)
        return

    if len(conversations) < 2:
        add_issue(
            issues,
            summary,
            "error",
            file_label,
            line_no,
            "conversations must contain at least two turns",
            strict,
        )
        return

    if len(conversations) > 2:
        add_issue(
            issues,
            summary,
            "warning",
            file_label,
            line_no,
            "only the first two conversation turns are consumed by the current loader",
            strict,
        )

    first = conversations[0]
    second = conversations[1]

    if not isinstance(first, dict):
        add_issue(issues, summary, "error", file_label, line_no, "conversations[0] must be an object", strict)
    else:
        first_role = first.get("from")
        if first_role not in {"human", "user"}:
            add_issue(
                issues,
                summary,
                "warning",
                file_label,
                line_no,
                f"conversations[0].from is usually human/user, got {first_role!r}",
                strict,
            )
        prompt = first.get("value")
        if not isinstance(prompt, str):
            add_issue(
                issues,
                summary,
                "error",
                file_label,
                line_no,
                "conversations[0].value must be a string",
                strict,
            )
        else:
            token_count = count_image_tokens(prompt)
            if image_value is None and token_count > 0:
                add_issue(
                    issues,
                    summary,
                    "warning",
                    file_label,
                    line_no,
                    "prompt contains <image> tokens but the row has no image field; the loader strips the tokens",
                    strict,
                )
            elif image_value is not None and token_count not in {0, len(images)}:
                add_issue(
                    issues,
                    summary,
                    "warning",
                    file_label,
                    line_no,
                    f"prompt has {token_count} <image> token(s) but image field has {len(images)} image(s); use zero tokens or one token per image",
                    strict,
                )

    if not isinstance(second, dict):
        add_issue(issues, summary, "error", file_label, line_no, "conversations[1] must be an object", strict)
    else:
        second_role = second.get("from")
        if second_role not in {"gpt", "assistant"}:
            add_issue(
                issues,
                summary,
                "warning",
                file_label,
                line_no,
                f"conversations[1].from is usually gpt/assistant, got {second_role!r}",
                strict,
            )
        if "value" not in second:
            add_issue(
                issues,
                summary,
                "error",
                file_label,
                line_no,
                "conversations[1] is missing value",
                strict,
            )
        else:
            answer_value = second["value"]
            if answer_value is None:
                add_issue(
                    issues,
                    summary,
                    "error",
                    file_label,
                    line_no,
                    "conversations[1].value is missing",
                    strict,
                )
            elif isinstance(answer_value, str):
                if not answer_value.strip():
                    add_issue(
                        issues,
                        summary,
                        "error",
                        file_label,
                        line_no,
                        "conversations[1].value is empty",
                        strict,
                    )
            elif not isinstance(answer_value, (int, float, bool)):
                add_issue(
                    issues,
                    summary,
                    "warning",
                    file_label,
                    line_no,
                    "conversations[1].value is non-scalar and will be stringified by the loader",
                    strict,
                )

    reward_method = row.get("accu_reward_method")
    if reward_method is not None:
        if not isinstance(reward_method, str):
            add_issue(
                issues,
                summary,
                "warning",
                file_label,
                line_no,
                "accu_reward_method should be a string",
                strict,
            )
        elif reward_method not in KNOWN_REWARD_METHODS:
            add_issue(
                issues,
                summary,
                "warning",
                file_label,
                line_no,
                f"unknown accu_reward_method {reward_method!r}",
                strict,
            )


def validate_file(path: Path, image_root: Path | None, strict: bool) -> tuple[Summary, list[Issue]]:
    summary = Summary()
    issues: list[Issue] = []

    if not path.exists():
        add_issue(issues, summary, "error", str(path), None, "dataset file does not exist", strict)
        return summary, issues

    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, 1):
            if not raw_line.strip():
                continue
            summary.rows += 1
            try:
                row = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                add_issue(
                    issues,
                    summary,
                    "error",
                    str(path),
                    line_no,
                    f"invalid JSON: {exc.msg}",
                    strict,
                )
                continue

            if not isinstance(row, dict):
                add_issue(issues, summary, "error", str(path), line_no, "each JSONL row must be an object", strict)
                continue

            validate_row(row, str(path), line_no, image_root, summary, issues, strict)

    return summary, issues


def format_summary(path: Path, summary: Summary) -> str:
    return (
        f"{path}: rows={summary.rows} image_rows={summary.image_rows} "
        f"single={summary.single_image_rows} multi={summary.multi_image_rows} "
        f"text_only={summary.text_only_rows} errors={summary.errors} warnings={summary.warnings}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate VLM-R1 JSONL datasets and optional image-root mappings.",
    )
    parser.add_argument(
        "--data-file-paths",
        required=True,
        help="Colon-separated JSONL file paths to validate.",
    )
    parser.add_argument(
        "--image-roots",
        default=None,
        help="Optional colon-separated image roots, one per JSONL file.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        data_files = split_colon_list(args.data_file_paths)
        image_roots = split_colon_list(args.image_roots) if args.image_roots else []
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not data_files:
        print("ERROR: --data-file-paths must not be empty", file=sys.stderr)
        return 2

    if image_roots and len(image_roots) != len(data_files):
        print(
            f"ERROR: expected the same number of image roots as data files ({len(image_roots)} != {len(data_files)})",
            file=sys.stderr,
        )
        return 2

    if not image_roots:
        image_roots = [None] * len(data_files)

    total_errors = 0
    total_warnings = 0

    for data_file, image_root in zip(data_files, image_roots):
        root_path = Path(image_root) if image_root else None
        summary, issues = validate_file(Path(data_file), root_path, args.strict)
        print(format_summary(Path(data_file), summary))
        for issue in issues:
            location = f":{issue.line}" if issue.line is not None else ""
            print(f"[{issue.level.upper()}] {issue.file}{location}: {issue.message}")
        total_errors += summary.errors
        total_warnings += summary.warnings

    print(f"TOTAL: errors={total_errors} warnings={total_warnings}")
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
