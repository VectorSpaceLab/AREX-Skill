"""Validate LMOps experiential-learning inputs without importing repo code.

Checks experience-list text files, system-prompt text/files, and expected data-root
contents. The script never loads models, starts services, downloads data, or calls
external APIs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


PROFILE_FILES: Dict[str, List[str]] = {
    "opcd-math": [
        "dapo_train.parquet",
        "dapo_validation.parquet",
        "dapo_test.parquet",
    ],
    "opcd-sys-medmcqa": [
        "sys_medmcqa_train.parquet",
        "sys_medmcqa_test.parquet",
    ],
    "opcd-sys-safety": [
        "sys_safety_train.parquet",
        "sys_safety_test.parquet",
    ],
    "coach": [
        "wildchat-if_rubric-4o_train.parquet",
        "wildchat-if_rubric-4o_val.parquet",
        "tulu-3-sft-mixture-filtered.parquet",
        "alpacaeval2/alpaca_eval_gpt4_baseline.json",
        "wildbench/v2.json",
        "arena_hard_v2/prompts.json",
        "creativewritingv3/creative_writing_prompts_v3.json",
    ],
    "gad": [
        "lmsys_gpt5_chat_filtered_train.parquet",
        "lmsys_gpt5_chat_filtered_test.parquet",
    ],
}


@dataclass
class CheckResult:
    ok: bool = True
    checked: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)
        self.ok = False

    def note(self, message: str) -> None:
        self.checked.append(message)

    def to_dict(self) -> Dict[str, object]:
        return {
            "ok": self.ok,
            "checked": self.checked,
            "warnings": self.warnings,
            "errors": self.errors,
        }


def is_probably_remote(entry: str) -> bool:
    return "://" in entry or entry.startswith("hf:")


def check_nonempty_file(path: Path, result: CheckResult, label: str) -> bool:
    if not path.exists():
        result.error(f"Missing {label}: {path}")
        return False
    if not path.is_file():
        result.error(f"Expected {label} to be a file: {path}")
        return False
    try:
        size = path.stat().st_size
    except OSError as exc:
        result.error(f"Cannot stat {label} {path}: {exc}")
        return False
    if size <= 0:
        result.error(f"Empty {label}: {path}")
        return False
    result.note(f"Found {label}: {path} ({size} bytes)")
    return True


def check_experience_list(args: argparse.Namespace, result: CheckResult) -> None:
    if not args.experience_list:
        return
    list_path = Path(args.experience_list)
    if not check_nonempty_file(list_path, result, "experience list"):
        return
    try:
        raw_lines = list_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        result.error(f"Experience list is not UTF-8 text: {list_path}")
        return
    except OSError as exc:
        result.error(f"Cannot read experience list {list_path}: {exc}")
        return

    nonempty = [line.strip() for line in raw_lines if line.strip()]
    empty_count = len(raw_lines) - len(nonempty)
    if empty_count:
        msg = f"Experience list contains {empty_count} empty line(s)."
        if args.strict:
            result.error(msg)
        else:
            result.warn(msg)
    if len(nonempty) < args.min_lines:
        result.error(f"Experience list has {len(nonempty)} nonempty line(s), expected at least {args.min_lines}.")
    else:
        result.note(f"Experience list has {len(nonempty)} nonempty line(s).")

    seen = set()
    for idx, entry in enumerate(nonempty, start=1):
        if entry in seen:
            msg = f"Duplicate experience-list entry at line {idx}: {entry}"
            if args.strict:
                result.error(msg)
            else:
                result.warn(msg)
        seen.add(entry)

        if is_probably_remote(entry):
            result.warn(f"Line {idx} looks remote rather than a local staged experience file: {entry}")
            continue

        entry_path = Path(entry)
        if args.warn_absolute_lines and entry_path.is_absolute():
            result.warn(f"Line {idx} is absolute; prefer target-host placeholders in plans: {entry}")

        if args.require_listed_files:
            candidate = entry_path if entry_path.is_absolute() else (list_path.parent / entry_path)
            check_nonempty_file(candidate, result, f"experience entry line {idx}")


def read_prompt(args: argparse.Namespace, result: CheckResult) -> str | None:
    prompt_parts: List[str] = []
    if args.system_prompt_text:
        prompt_parts.append(args.system_prompt_text)
        result.note("Read system prompt from --system-prompt-text.")
    if args.system_prompt_file:
        prompt_path = Path(args.system_prompt_file)
        if check_nonempty_file(prompt_path, result, "system prompt file"):
            try:
                prompt_parts.append(prompt_path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                result.error(f"System prompt file is not UTF-8 text: {prompt_path}")
            except OSError as exc:
                result.error(f"Cannot read system prompt file {prompt_path}: {exc}")
    if not prompt_parts:
        return None
    return "\n".join(prompt_parts).strip()


def check_system_prompt(args: argparse.Namespace, result: CheckResult) -> None:
    prompt = read_prompt(args, result)
    if prompt is None:
        return
    if len(prompt) < args.min_prompt_chars:
        result.error(f"System prompt is too short: {len(prompt)} characters, expected at least {args.min_prompt_chars}.")
        return
    result.note(f"System prompt length: {len(prompt)} characters.")

    lowered = prompt.lower()
    prompt_type = args.prompt_type
    if prompt_type == "safety":
        if "answer" not in lowered or ("yes" not in lowered and "no" not in lowered):
            msg = "Safety prompt usually specifies an answer format with yes/no; review the prompt before training."
            if args.strict:
                result.error(msg)
            else:
                result.warn(msg)
    elif prompt_type == "medmcqa":
        if "medical" not in lowered and "medicine" not in lowered and "clinical" not in lowered:
            msg = "MedMCQA prompt does not mention medical/clinical context; review prompt type alignment."
            if args.strict:
                result.error(msg)
            else:
                result.warn(msg)
    elif prompt_type == "custom":
        result.warn("Custom prompt type selected; confirm matching OPCD data files and evaluation labels manually.")


def parquet_shape_hint(path: Path, result: CheckResult) -> None:
    if path.suffix != ".parquet" or not path.exists() or not path.is_file():
        return
    try:
        with path.open("rb") as handle:
            head = handle.read(4)
            try:
                handle.seek(-4, os.SEEK_END)
                tail = handle.read(4)
            except OSError:
                tail = b""
    except OSError as exc:
        result.warn(f"Could not inspect parquet magic bytes for {path}: {exc}")
        return
    if head != b"PAR1" or tail != b"PAR1":
        result.warn(f"File has .parquet suffix but missing PAR1 magic bytes at one end: {path}")


def check_data_root(args: argparse.Namespace, result: CheckResult) -> None:
    if not args.data_root:
        return
    root = Path(args.data_root)
    if not root.exists():
        result.error(f"Data root does not exist: {root}")
        return
    if not root.is_dir():
        result.error(f"Data root is not a directory: {root}")
        return
    result.note(f"Found data root: {root}")

    expected: List[str] = []
    for profile in args.profile or []:
        expected.extend(PROFILE_FILES[profile])
    expected.extend(args.expect_file or [])

    for rel in expected:
        if Path(rel).is_absolute():
            result.error(f"Expected-file entry must be relative to the data root, not absolute: {rel}")
            continue
        candidate = root / rel
        if check_nonempty_file(candidate, result, f"expected data file {rel}"):
            parquet_shape_hint(candidate, result)

    for rel in args.expect_dir or []:
        if Path(rel).is_absolute():
            result.error(f"Expected-dir entry must be relative to the data root, not absolute: {rel}")
            continue
        candidate = root / rel
        if not candidate.exists():
            result.error(f"Missing expected data directory {rel}: {candidate}")
        elif not candidate.is_dir():
            result.error(f"Expected data directory is not a directory {rel}: {candidate}")
        else:
            result.note(f"Found expected data directory {rel}: {candidate}")

    if not expected and not args.expect_dir:
        result.warn("Data root exists, but no --profile, --expect-file, or --expect-dir was supplied.")


def render_text(result: CheckResult) -> str:
    lines: List[str] = []
    lines.append("# Experience input validation")
    lines.append("")
    lines.append("Result: " + ("PASS" if result.ok else "FAIL"))
    if result.checked:
        lines.append("")
        lines.append("## Checked")
        for item in result.checked:
            lines.append(f"- {item}")
    if result.warnings:
        lines.append("")
        lines.append("## Warnings")
        for item in result.warnings:
            lines.append(f"- {item}")
    if result.errors:
        lines.append("")
        lines.append("## Errors")
        for item in result.errors:
            lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate experience lists, system prompts, and staged data roots without importing LMOps code.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--experience-list", help="Text file containing one experience path per nonempty line.")
    parser.add_argument("--min-lines", type=int, default=1, help="Minimum nonempty lines required in --experience-list.")
    parser.add_argument("--require-listed-files", action="store_true", help="Require every experience-list entry to exist as a local file.")
    parser.add_argument("--warn-absolute-lines", action="store_true", help="Warn when experience-list entries are absolute target-host paths.")
    parser.add_argument("--system-prompt-file", help="System prompt text file to validate.")
    parser.add_argument("--system-prompt-text", help="Inline system prompt text to validate.")
    parser.add_argument("--prompt-type", choices=["medmcqa", "safety", "custom"], default="custom", help="Prompt type for lightweight content checks.")
    parser.add_argument("--min-prompt-chars", type=int, default=40, help="Minimum system prompt length.")
    parser.add_argument("--data-root", help="Root directory containing staged data files.")
    parser.add_argument("--profile", action="append", choices=sorted(PROFILE_FILES), help="Expected data-file profile; may be repeated.")
    parser.add_argument("--expect-file", action="append", help="Additional expected file path relative to --data-root; may be repeated.")
    parser.add_argument("--expect-dir", action="append", help="Expected directory path relative to --data-root; may be repeated.")
    parser.add_argument("--strict", action="store_true", help="Promote selected warnings to errors.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown text.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not any([args.experience_list, args.system_prompt_file, args.system_prompt_text, args.data_root]):
        parser.error("provide at least one of --experience-list, --system-prompt-file, --system-prompt-text, or --data-root")

    result = CheckResult()
    check_experience_list(args, result)
    check_system_prompt(args, result)
    check_data_root(args, result)

    if args.strict and result.warnings:
        for warning in list(result.warnings):
            result.error(f"Strict mode warning promoted to error: {warning}")

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        sys.stdout.write(render_text(result))
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
