#!/usr/bin/env python3
"""Validate NeMo audio-to-audio JSONL manifests without importing NeMo.

The checker is intentionally read-only: it parses manifests, optionally checks referenced file existence, and validates
output path choices. It does not open audio contents, download models, train, or write output files.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

AUDIO_EXTENSIONS = (".wav", ".flac", ".mp3", ".ogg", ".opus", ".m4a", ".aif", ".aiff")
EMBEDDING_EXTENSIONS = (".npy",)


class Issue:
    def __init__(self, severity: str, line: int | None, message: str):
        self.severity = severity
        self.line = line
        self.message = message

    def as_dict(self) -> dict[str, Any]:
        return {"severity": self.severity, "line": self.line, "message": self.message}

    def format(self) -> str:
        where = f"line {self.line}: " if self.line is not None else ""
        return f"[{self.severity}] {where}{self.message}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a NeMo audio-to-audio JSONL manifest without importing NeMo or touching audio contents."
    )
    parser.add_argument("manifest", type=Path, help="Path to the JSONL manifest to validate.")
    parser.add_argument("--input-key", default="input_filepath", help="Manifest key for input audio paths.")
    parser.add_argument("--target-key", default="target_filepath", help="Manifest key for target audio paths.")
    parser.add_argument("--reference-key", default=None, help="Optional manifest key for reference audio paths.")
    parser.add_argument("--embedding-key", default=None, help="Optional manifest key for .npy embedding paths.")
    parser.add_argument("--duration-key", default="duration", help="Manifest key for duration in seconds.")
    parser.add_argument("--offset-key", default="offset", help="Manifest key for optional offset in seconds.")
    parser.add_argument("--require-target", action="store_true", help="Require target_key to be present and non-empty.")
    parser.add_argument("--allow-blank-lines", action="store_true", help="Allow and skip blank lines.")
    parser.add_argument("--check-files", action="store_true", help="Check that referenced input/target files exist.")
    parser.add_argument(
        "--manifest-base-dir",
        type=Path,
        default=None,
        help="Base directory for resolving relative paths. Defaults to the manifest parent directory.",
    )
    parser.add_argument("--min-duration", type=float, default=None, help="Warn for durations below this many seconds.")
    parser.add_argument("--max-duration", type=float, default=None, help="Warn for durations above this many seconds.")
    parser.add_argument("--max-lines", type=int, default=None, help="Validate at most this many manifest lines.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Planned processing output directory to sanity-check.")
    parser.add_argument("--output-manifest", type=Path, default=None, help="Planned processing output manifest to sanity-check.")
    parser.add_argument(
        "--allow-output-inside-input-tree",
        action="store_true",
        help="Allow output_dir to live under a common input-file directory.",
    )
    parser.add_argument(
        "--allow-output-overwrite",
        action="store_true",
        help="Do not error if output_dir or output_manifest already exists.",
    )
    parser.add_argument(
        "--strict-audio-extension",
        action="store_true",
        help="Warn when audio paths do not use a common audio extension.",
    )
    parser.add_argument("--json-summary", action="store_true", help="Emit a machine-readable JSON summary.")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-issue text output; summary is still printed.")
    return parser.parse_args()


def add_issue(issues: list[Issue], severity: str, line: int | None, message: str) -> None:
    issues.append(Issue(severity=severity, line=line, message=message))


def as_path_list(value: Any) -> list[str] | None:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and value and all(isinstance(item, str) for item in value):
        return value
    return None


def resolve_path(path_text: str, base_dir: Path) -> Path:
    candidate = Path(path_text).expanduser()
    if candidate.is_absolute():
        return candidate
    return base_dir / candidate


def is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def common_parent(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    try:
        common = os.path.commonpath([str(path.resolve(strict=False)) for path in paths])
    except ValueError:
        return None
    common_path = Path(common)
    return common_path if common_path.is_dir() else common_path.parent


def validate_duration(item: dict[str, Any], line_no: int, args: argparse.Namespace, issues: list[Issue]) -> float | None:
    if args.duration_key not in item:
        add_issue(issues, "error", line_no, f"missing duration key {args.duration_key!r}")
        return None
    duration = item[args.duration_key]
    if isinstance(duration, bool) or not isinstance(duration, (int, float)):
        add_issue(issues, "error", line_no, f"duration key {args.duration_key!r} must be numeric")
        return None
    if duration <= 0:
        add_issue(issues, "error", line_no, f"duration must be positive, got {duration!r}")
        return float(duration)
    if args.min_duration is not None and duration < args.min_duration:
        add_issue(issues, "warning", line_no, f"duration {duration:g}s is below --min-duration {args.min_duration:g}s")
    if args.max_duration is not None and duration > args.max_duration:
        add_issue(issues, "warning", line_no, f"duration {duration:g}s is above --max-duration {args.max_duration:g}s")
    return float(duration)


def validate_offset(item: dict[str, Any], line_no: int, args: argparse.Namespace, issues: list[Issue]) -> None:
    if args.offset_key not in item:
        return
    offset = item[args.offset_key]
    if isinstance(offset, bool) or not isinstance(offset, (int, float)):
        add_issue(issues, "error", line_no, f"offset key {args.offset_key!r} must be numeric when present")
    elif offset < 0:
        add_issue(issues, "error", line_no, f"offset must be non-negative, got {offset!r}")


def validate_channel_selector(value: Any, key: str, line_no: int, issues: list[Issue]) -> None:
    if value is None:
        return
    if isinstance(value, bool):
        add_issue(issues, "error", line_no, f"channel selector {key!r} must be an int, list of ints, or 'average'")
        return
    if isinstance(value, int):
        if value < 0:
            add_issue(issues, "error", line_no, f"channel selector {key!r} must be non-negative")
        return
    if isinstance(value, str):
        if value != "average":
            add_issue(issues, "warning", line_no, f"string channel selector {key!r} is not 'average': {value!r}")
        return
    if isinstance(value, list) and value and all(isinstance(item, int) and item >= 0 for item in value):
        return
    add_issue(issues, "error", line_no, f"channel selector {key!r} must be an int, non-empty int list, or 'average'")


def validate_path_field(
    item: dict[str, Any],
    key: str,
    label: str,
    line_no: int,
    base_dir: Path,
    args: argparse.Namespace,
    issues: list[Issue],
    required: bool,
    expected_extensions: tuple[str, ...],
    resolved_paths: list[Path],
) -> None:
    if key not in item or item[key] in (None, ""):
        if required:
            add_issue(issues, "error", line_no, f"missing required {label} key {key!r}")
        return

    path_values = as_path_list(item[key])
    if path_values is None:
        add_issue(issues, "error", line_no, f"{label} key {key!r} must be a string or non-empty list of strings")
        return

    for path_text in path_values:
        if not path_text.strip():
            add_issue(issues, "error", line_no, f"{label} path under key {key!r} is empty")
            continue
        path = resolve_path(path_text, base_dir)
        resolved_paths.append(path)
        if args.strict_audio_extension and expected_extensions and path.suffix.lower() not in expected_extensions:
            joined = ", ".join(expected_extensions)
            add_issue(issues, "warning", line_no, f"{label} path {path_text!r} does not use extension in {joined}")
        if args.check_files and not path.is_file():
            add_issue(issues, "error", line_no, f"{label} file does not exist: {path_text!r}")


def validate_output_paths(
    args: argparse.Namespace,
    base_dir: Path,
    input_paths: list[Path],
    issues: list[Issue],
) -> None:
    manifest = args.manifest.resolve(strict=False)
    output_paths: list[tuple[str, Path]] = []

    if args.output_dir is not None:
        output_dir = resolve_path(str(args.output_dir), Path.cwd())
        output_paths.append(("output_dir", output_dir))
        if output_dir.exists() and not args.allow_output_overwrite:
            add_issue(issues, "error", None, f"output_dir already exists; use a new directory or --allow-output-overwrite")
        if output_dir.resolve(strict=False) == base_dir.resolve(strict=False):
            add_issue(issues, "error", None, "output_dir is the manifest base directory; choose a dedicated output directory")

    if args.output_manifest is not None:
        output_manifest = resolve_path(str(args.output_manifest), Path.cwd())
        output_paths.append(("output_manifest", output_manifest))
        if output_manifest.exists() and not args.allow_output_overwrite:
            add_issue(issues, "error", None, "output_manifest already exists; use a new path or --allow-output-overwrite")
        if output_manifest.resolve(strict=False) == manifest:
            add_issue(issues, "error", None, "output_manifest is the same path as the input manifest")

    input_root = common_parent(input_paths)
    if input_root is not None and args.output_dir is not None and not args.allow_output_inside_input_tree:
        output_dir = resolve_path(str(args.output_dir), Path.cwd())
        if is_relative_to(output_dir, input_root):
            add_issue(
                issues,
                "warning",
                None,
                "output_dir appears to be inside the input audio tree; pass --allow-output-inside-input-tree if intentional",
            )

    for label, output_path in output_paths:
        for input_path in input_paths:
            if output_path.resolve(strict=False) == input_path.resolve(strict=False):
                add_issue(issues, "error", None, f"{label} matches an input audio path")


def validate_manifest(args: argparse.Namespace) -> dict[str, Any]:
    issues: list[Issue] = []
    manifest = args.manifest
    if not manifest.is_file():
        add_issue(issues, "error", None, f"manifest file does not exist: {manifest}")
        return {"ok": False, "issues": issues, "num_items": 0}

    base_dir = (args.manifest_base_dir or manifest.parent).resolve(strict=False)
    input_paths: list[Path] = []
    target_paths: list[Path] = []
    reference_paths: list[Path] = []
    embedding_paths: list[Path] = []
    duration_values: list[float] = []
    key_counter: Counter[str] = Counter()
    num_items = 0
    saw_target = 0
    saw_reference = 0
    saw_embedding = 0

    with manifest.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            if args.max_lines is not None and num_items >= args.max_lines:
                break
            line = raw_line.rstrip("\n")
            if not line.strip():
                if not args.allow_blank_lines:
                    add_issue(issues, "error", line_no, "blank lines are invalid in NeMo audio manifests")
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                add_issue(issues, "error", line_no, f"invalid JSON: {exc.msg}")
                continue
            if not isinstance(item, dict):
                add_issue(issues, "error", line_no, "manifest line must be a JSON object")
                continue

            num_items += 1
            key_counter.update(item.keys())
            duration = validate_duration(item, line_no, args, issues)
            if duration is not None:
                duration_values.append(duration)
            validate_offset(item, line_no, args, issues)

            validate_path_field(
                item,
                args.input_key,
                "input",
                line_no,
                base_dir,
                args,
                issues,
                required=True,
                expected_extensions=AUDIO_EXTENSIONS,
                resolved_paths=input_paths,
            )
            validate_path_field(
                item,
                args.target_key,
                "target",
                line_no,
                base_dir,
                args,
                issues,
                required=args.require_target,
                expected_extensions=AUDIO_EXTENSIONS,
                resolved_paths=target_paths,
            )
            if args.target_key in item and item.get(args.target_key) not in (None, ""):
                saw_target += 1

            if args.reference_key:
                validate_path_field(
                    item,
                    args.reference_key,
                    "reference",
                    line_no,
                    base_dir,
                    args,
                    issues,
                    required=False,
                    expected_extensions=AUDIO_EXTENSIONS,
                    resolved_paths=reference_paths,
                )
                if args.reference_key in item and item.get(args.reference_key) not in (None, ""):
                    saw_reference += 1

            if args.embedding_key:
                validate_path_field(
                    item,
                    args.embedding_key,
                    "embedding",
                    line_no,
                    base_dir,
                    args,
                    issues,
                    required=False,
                    expected_extensions=EMBEDDING_EXTENSIONS,
                    resolved_paths=embedding_paths,
                )
                if args.embedding_key in item and item.get(args.embedding_key) not in (None, ""):
                    saw_embedding += 1

            for key in ("input_channel_selector", "target_channel_selector", "reference_channel_selector"):
                if key in item:
                    validate_channel_selector(item[key], key, line_no, issues)

    if num_items == 0:
        add_issue(issues, "error", None, "manifest has no valid JSON object entries")
    if args.require_target and saw_target != num_items:
        add_issue(issues, "error", None, f"target key {args.target_key!r} is required for every entry")
    if args.reference_key and 0 < saw_reference < num_items:
        add_issue(issues, "warning", None, f"reference key {args.reference_key!r} is present for only some entries")
    if args.embedding_key and 0 < saw_embedding < num_items:
        add_issue(issues, "warning", None, f"embedding key {args.embedding_key!r} is present for only some entries")

    validate_output_paths(args, base_dir, input_paths, issues)

    errors = sum(1 for issue in issues if issue.severity == "error")
    warnings = sum(1 for issue in issues if issue.severity == "warning")
    duration_summary = None
    if duration_values:
        duration_summary = {
            "min": min(duration_values),
            "max": max(duration_values),
            "total": sum(duration_values),
            "mean": sum(duration_values) / len(duration_values),
        }

    return {
        "ok": errors == 0,
        "manifest": str(manifest),
        "base_dir": str(base_dir),
        "num_items": num_items,
        "num_input_paths": len(input_paths),
        "num_target_paths": len(target_paths),
        "num_reference_paths": len(reference_paths),
        "num_embedding_paths": len(embedding_paths),
        "duration": duration_summary,
        "keys": dict(sorted(key_counter.items())),
        "errors": errors,
        "warnings": warnings,
        "issues": issues,
    }


def main() -> int:
    args = parse_args()
    summary = validate_manifest(args)

    if args.json_summary:
        printable = dict(summary)
        printable["issues"] = [issue.as_dict() for issue in summary["issues"]]
        print(json.dumps(printable, indent=2, sort_keys=True))
    else:
        if not args.quiet:
            for issue in summary["issues"]:
                print(issue.format(), file=sys.stderr if issue.severity == "error" else sys.stdout)
        duration = summary.get("duration")
        duration_text = "duration=unavailable"
        if duration:
            duration_text = (
                f"duration=min {duration['min']:.3f}s, max {duration['max']:.3f}s, "
                f"mean {duration['mean']:.3f}s, total {duration['total']:.3f}s"
            )
        status = "PASS" if summary["ok"] else "FAIL"
        print(
            f"{status}: {summary['num_items']} entries, errors={summary['errors']}, "
            f"warnings={summary['warnings']}, {duration_text}"
        )

    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
