#!/usr/bin/env python3
"""Validate NeMo speaker diarization, recognition, VAD, and forced-alignment manifests.

The checker is intentionally local-only and dependency-free. It does not import NeMo,
read audio contents, download models, run training, or write output files.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

AUDIO_FIELDS = ("audio_filepath",)
RTTM_FIELDS = ("rttm_filepath", "hyp_rttm_filepath")
CTM_FIELDS = ("ctm_filepath", "ref_ctm_filepath", "hyp_ctm_filepath")
UEM_FIELDS = ("uem_filepath",)
TEXT_FIELDS = ("text",)
LABEL_FIELDS = ("label",)
SPEAKER_FIELDS = ("speaker",)
PATH_FIELDS = AUDIO_FIELDS + RTTM_FIELDS + CTM_FIELDS + UEM_FIELDS + ("output_filepath", "output_manifest_filepath")

DEFAULT_AUDIO_EXTENSIONS = (".wav", ".flac", ".ogg", ".mp3", ".m4a", ".opus")
RTTM_EXTENSION = ".rttm"
CTM_EXTENSION = ".ctm"
UEM_EXTENSION = ".uem"
JSON_EXTENSIONS = (".json", ".jsonl")


@dataclass
class Issue:
    level: str
    line: int | None
    message: str


@dataclass
class ManifestEntry:
    line_number: int
    raw: dict[str, Any]
    audio_path: str | None = None
    audio_basename: str | None = None
    uniq_id: str | None = None
    rttm_speakers: set[str] = field(default_factory=set)
    ctm_speakers: set[str] = field(default_factory=set)
    rttm_recording_ids: set[str] = field(default_factory=set)
    ctm_recording_ids: set[str] = field(default_factory=set)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a NeMo speaker JSONL manifest for diarization, speaker recognition, VAD, "
            "ASR+diarization, or forced alignment without importing NeMo."
        )
    )
    parser.add_argument("manifest", type=Path, help="Path to the JSONL manifest to validate.")
    parser.add_argument(
        "--task",
        choices=(
            "generic",
            "diarization",
            "diarization-eval",
            "recognition",
            "forced-alignment",
            "asr-diarization",
            "vad",
        ),
        default="generic",
        help="Task preset that enables common required-field checks.",
    )
    parser.add_argument(
        "--path-base",
        choices=("cwd", "manifest-dir"),
        default="cwd",
        help="Base directory for relative path existence checks. NeMo runtime commonly uses cwd.",
    )
    parser.add_argument(
        "--allowed-audio-ext",
        nargs="+",
        default=list(DEFAULT_AUDIO_EXTENSIONS),
        help="Allowed audio filename extensions for extension sanity checks.",
    )
    parser.add_argument(
        "--align-using-pred-text",
        action="store_true",
        help="Do not require text for forced alignment.",
    )
    parser.add_argument(
        "--require-existing-files",
        action="store_true",
        help="Require referenced input files to exist.",
    )
    parser.add_argument("--require-rttm", action="store_true", help="Require rttm_filepath in every manifest line.")
    parser.add_argument("--require-ctm", action="store_true", help="Require ctm_filepath in every manifest line.")
    parser.add_argument("--require-uem", action="store_true", help="Require uem_filepath in every manifest line.")
    parser.add_argument("--require-label", action="store_true", help="Require label in every manifest line.")
    parser.add_argument("--require-text", action="store_true", help="Require text in every manifest line.")
    parser.add_argument(
        "--require-offset-duration", action="store_true", help="Require offset and duration in every manifest line."
    )
    parser.add_argument(
        "--require-matching-basename",
        action="store_true",
        help="Require audio, RTTM, UEM, and CTM basenames in each line to match.",
    )
    parser.add_argument(
        "--require-unique-audio-basename",
        action="store_true",
        help="Fail if two manifest lines share the same audio basename without distinct uniq_id values.",
    )
    parser.add_argument("--check-rttm-speakers", action="store_true", help="Parse RTTM files and collect speaker IDs.")
    parser.add_argument("--check-ctm-speakers", action="store_true", help="Parse CTM files and collect speaker IDs.")
    parser.add_argument(
        "--speaker-consistency",
        choices=("off", "warn", "strict"),
        default="warn",
        help="Compare manifest speaker, RTTM speakers, and CTM speakers when available.",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=0,
        help="Validate only the first N non-empty lines. Default 0 validates all lines.",
    )
    parser.add_argument("--quiet", action="store_true", help="Only print errors and final status.")
    return parser.parse_args()


def add_issue(issues: list[Issue], level: str, line: int | None, message: str) -> None:
    issues.append(Issue(level=level, line=line, message=message))


def is_missing(value: Any) -> bool:
    return value is None or value == ""


def numeric_or_none(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("boolean is not a valid numeric value")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"", "none", "null"}:
            return None
        return float(lowered)
    raise ValueError(f"unsupported numeric type {type(value).__name__}")


def normalize_extensions(values: list[str]) -> set[str]:
    extensions = set()
    for value in values:
        normalized = value.lower().strip()
        if not normalized:
            continue
        extensions.add(normalized if normalized.startswith(".") else f".{normalized}")
    return extensions


def resolve_path(path_value: str, manifest_path: Path, path_base: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    if path_base == "manifest-dir":
        return manifest_path.parent / path
    return Path.cwd() / path


def path_suffix(path_value: str) -> str:
    return Path(path_value).suffix.lower()


def basename_stem(path_value: str) -> str:
    return Path(path_value).stem


def get_recording_id(entry: ManifestEntry) -> str | None:
    if entry.uniq_id:
        return entry.uniq_id
    if entry.audio_path:
        return basename_stem(entry.audio_path)
    return None


def load_manifest(manifest_path: Path, max_lines: int, issues: list[Issue]) -> list[ManifestEntry]:
    entries: list[ManifestEntry] = []
    try:
        with manifest_path.open("r", encoding="utf-8") as manifest_file:
            for line_number, raw_line in enumerate(manifest_file, start=1):
                stripped = raw_line.strip()
                if not stripped:
                    continue
                if max_lines and len(entries) >= max_lines:
                    break
                try:
                    parsed = json.loads(stripped)
                except json.JSONDecodeError as error:
                    add_issue(issues, "error", line_number, f"invalid JSON: {error}")
                    continue
                if not isinstance(parsed, dict):
                    add_issue(issues, "error", line_number, "manifest line must be a JSON object")
                    continue
                audio_path = parsed.get("audio_filepath")
                audio_basename = basename_stem(audio_path) if isinstance(audio_path, str) and audio_path else None
                uniq_id = parsed.get("uniq_id")
                if uniq_id is not None and not isinstance(uniq_id, str):
                    add_issue(issues, "warning", line_number, "uniq_id should be a string when provided")
                    uniq_id = str(uniq_id)
                entries.append(
                    ManifestEntry(
                        line_number=line_number,
                        raw=parsed,
                        audio_path=audio_path if isinstance(audio_path, str) else None,
                        audio_basename=audio_basename,
                        uniq_id=uniq_id,
                    )
                )
    except FileNotFoundError:
        add_issue(issues, "error", None, f"manifest not found: {manifest_path}")
    except OSError as error:
        add_issue(issues, "error", None, f"could not read manifest: {error}")
    return entries


def apply_task_requirements(args: argparse.Namespace) -> None:
    if args.task in {"diarization", "diarization-eval", "asr-diarization", "vad"}:
        args.require_offset_duration = True
    if args.task == "diarization-eval":
        args.require_rttm = True
    if args.task == "recognition":
        args.require_label = True
    if args.task == "forced-alignment" and not args.align_using_pred_text:
        args.require_text = True
    if args.task == "asr-diarization":
        args.require_rttm = True
        args.require_ctm = True


def validate_required_fields(entry: ManifestEntry, args: argparse.Namespace, issues: list[Issue]) -> None:
    raw = entry.raw
    line = entry.line_number
    if is_missing(raw.get("audio_filepath")):
        add_issue(issues, "error", line, "missing required audio_filepath")
    if args.require_rttm and is_missing(raw.get("rttm_filepath")):
        add_issue(issues, "error", line, "missing required rttm_filepath")
    if args.require_ctm and is_missing(raw.get("ctm_filepath")):
        add_issue(issues, "error", line, "missing required ctm_filepath")
    if args.require_uem and is_missing(raw.get("uem_filepath")):
        add_issue(issues, "error", line, "missing required uem_filepath")
    if args.require_label and is_missing(raw.get("label")):
        add_issue(issues, "error", line, "missing required label")
    if args.require_text and is_missing(raw.get("text")):
        add_issue(issues, "error", line, "missing required text")
    if args.require_offset_duration:
        if "offset" not in raw:
            add_issue(issues, "error", line, "missing required offset")
        if "duration" not in raw:
            add_issue(issues, "error", line, "missing required duration")


def validate_types_and_values(entry: ManifestEntry, args: argparse.Namespace, issues: list[Issue]) -> None:
    raw = entry.raw
    line = entry.line_number

    for field_name in PATH_FIELDS:
        if field_name in raw and raw[field_name] is not None and not isinstance(raw[field_name], str):
            add_issue(issues, "error", line, f"{field_name} must be a string path or null")

    for field_name in TEXT_FIELDS + LABEL_FIELDS + SPEAKER_FIELDS:
        if field_name in raw and raw[field_name] is not None and not isinstance(raw[field_name], str):
            add_issue(issues, "error", line, f"{field_name} must be a string or null")

    for field_name in ("offset", "duration"):
        if field_name not in raw:
            continue
        try:
            numeric_value = numeric_or_none(raw[field_name])
        except ValueError as error:
            add_issue(issues, "error", line, f"{field_name} is not numeric/null: {error}")
            continue
        if field_name == "offset" and numeric_value is not None and numeric_value < 0:
            add_issue(issues, "error", line, "offset must be >= 0")
        if field_name == "duration" and numeric_value is not None and numeric_value <= 0:
            add_issue(issues, "error", line, "duration must be > 0 when provided")

    if "num_speakers" in raw and raw["num_speakers"] is not None:
        try:
            speaker_count = numeric_or_none(raw["num_speakers"])
        except ValueError as error:
            add_issue(issues, "error", line, f"num_speakers is not numeric/null: {error}")
        else:
            if speaker_count is not None and (speaker_count < 1 or int(speaker_count) != speaker_count):
                add_issue(issues, "error", line, "num_speakers must be a positive integer when provided")

    if args.align_using_pred_text and "pred_text" in raw and raw["pred_text"] is not None:
        add_issue(
            issues,
            "error",
            line,
            "pred_text is already present while --align-using-pred-text is set; remove pred_text from input",
        )


def validate_extensions(entry: ManifestEntry, allowed_audio_extensions: set[str], issues: list[Issue]) -> None:
    raw = entry.raw
    line = entry.line_number

    audio_path = raw.get("audio_filepath")
    if isinstance(audio_path, str) and audio_path:
        suffix = path_suffix(audio_path)
        if suffix and suffix not in allowed_audio_extensions:
            add_issue(
                issues,
                "warning",
                line,
                f"audio_filepath extension {suffix!r} is not in allowed set {sorted(allowed_audio_extensions)}",
            )

    for field_name in RTTM_FIELDS:
        path_value = raw.get(field_name)
        if isinstance(path_value, str) and path_value and path_suffix(path_value) != RTTM_EXTENSION:
            add_issue(issues, "warning", line, f"{field_name} should usually end with {RTTM_EXTENSION}")

    for field_name in CTM_FIELDS:
        path_value = raw.get(field_name)
        if isinstance(path_value, str) and path_value and path_suffix(path_value) != CTM_EXTENSION:
            add_issue(issues, "warning", line, f"{field_name} should usually end with {CTM_EXTENSION}")

    for field_name in UEM_FIELDS:
        path_value = raw.get(field_name)
        if isinstance(path_value, str) and path_value and path_suffix(path_value) != UEM_EXTENSION:
            add_issue(issues, "warning", line, f"{field_name} should usually end with {UEM_EXTENSION}")

    output_manifest = raw.get("output_manifest_filepath")
    if isinstance(output_manifest, str) and output_manifest and path_suffix(output_manifest) not in JSON_EXTENSIONS:
        add_issue(issues, "warning", line, "output_manifest_filepath should usually end with .json or .jsonl")


def validate_existing_paths(
    entry: ManifestEntry, manifest_path: Path, args: argparse.Namespace, issues: list[Issue]
) -> None:
    if not args.require_existing_files:
        return
    for field_name in AUDIO_FIELDS + RTTM_FIELDS + CTM_FIELDS + UEM_FIELDS:
        path_value = entry.raw.get(field_name)
        if not isinstance(path_value, str) or not path_value:
            continue
        resolved = resolve_path(path_value, manifest_path, args.path_base)
        if not resolved.exists():
            add_issue(issues, "error", entry.line_number, f"{field_name} does not exist: {path_value}")
        elif not resolved.is_file():
            add_issue(issues, "error", entry.line_number, f"{field_name} is not a file: {path_value}")


def validate_matching_basenames(entry: ManifestEntry, issues: list[Issue]) -> None:
    stems: dict[str, str] = {}
    for field_name in AUDIO_FIELDS + RTTM_FIELDS + CTM_FIELDS + UEM_FIELDS:
        path_value = entry.raw.get(field_name)
        if isinstance(path_value, str) and path_value:
            stems[field_name] = basename_stem(path_value)
    if len(set(stems.values())) > 1:
        add_issue(issues, "error", entry.line_number, f"path basenames do not match: {stems}")


def validate_unique_audio_basenames(entries: list[ManifestEntry], issues: list[Issue]) -> None:
    seen: dict[str, ManifestEntry] = {}
    for entry in entries:
        if not entry.audio_basename:
            continue
        previous = seen.get(entry.audio_basename)
        if previous is None:
            seen[entry.audio_basename] = entry
            continue
        if previous.uniq_id and entry.uniq_id and previous.uniq_id != entry.uniq_id:
            continue
        add_issue(
            issues,
            "error",
            entry.line_number,
            f"duplicate audio basename {entry.audio_basename!r}; add distinct uniq_id values or disambiguate paths",
        )


def parse_rttm_file(path: Path) -> tuple[set[str], set[str], list[str]]:
    speakers: set[str] = set()
    recording_ids: set[str] = set()
    errors: list[str] = []
    try:
        with path.open("r", encoding="utf-8") as rttm_file:
            for rttm_line_number, raw_line in enumerate(rttm_file, start=1):
                stripped = raw_line.strip()
                if not stripped:
                    continue
                parts = stripped.split()
                if len(parts) < 9 or parts[0] != "SPEAKER":
                    errors.append(f"line {rttm_line_number}: expected SPEAKER line with at least 9 fields")
                    continue
                recording_ids.add(parts[1])
                try:
                    start = float(parts[3])
                    duration = float(parts[4])
                except ValueError:
                    errors.append(f"line {rttm_line_number}: start/duration must be numeric")
                    continue
                if start < 0:
                    errors.append(f"line {rttm_line_number}: start must be >= 0")
                if duration <= 0:
                    errors.append(f"line {rttm_line_number}: duration must be > 0")
                speakers.add(parts[7])
    except OSError as error:
        errors.append(str(error))
    return speakers, recording_ids, errors


def parse_ctm_file(path: Path) -> tuple[set[str], set[str], list[str]]:
    speakers: set[str] = set()
    recording_ids: set[str] = set()
    errors: list[str] = []
    try:
        with path.open("r", encoding="utf-8") as ctm_file:
            for ctm_line_number, raw_line in enumerate(ctm_file, start=1):
                stripped = raw_line.strip()
                if not stripped:
                    continue
                parts = stripped.split()
                if len(parts) < 8:
                    errors.append(f"line {ctm_line_number}: expected at least 8 CTM fields")
                    continue
                recording_ids.add(parts[0])
                try:
                    start = float(parts[2])
                    duration = float(parts[3])
                except ValueError:
                    errors.append(f"line {ctm_line_number}: start/duration must be numeric")
                    continue
                if start < 0:
                    errors.append(f"line {ctm_line_number}: start must be >= 0")
                if duration <= 0:
                    errors.append(f"line {ctm_line_number}: duration must be > 0")
                speakers.add(parts[7])
    except OSError as error:
        errors.append(str(error))
    return speakers, recording_ids, errors


def parse_referenced_speaker_files(
    entries: list[ManifestEntry], manifest_path: Path, args: argparse.Namespace, issues: list[Issue]
) -> None:
    rttm_cache: dict[Path, tuple[set[str], set[str], list[str]]] = {}
    ctm_cache: dict[Path, tuple[set[str], set[str], list[str]]] = {}

    for entry in entries:
        if args.check_rttm_speakers:
            path_value = entry.raw.get("rttm_filepath")
            if isinstance(path_value, str) and path_value:
                resolved = resolve_path(path_value, manifest_path, args.path_base)
                if resolved not in rttm_cache:
                    rttm_cache[resolved] = parse_rttm_file(resolved)
                speakers, recording_ids, parse_errors = rttm_cache[resolved]
                entry.rttm_speakers = set(speakers)
                entry.rttm_recording_ids = set(recording_ids)
                for parse_error in parse_errors:
                    add_issue(issues, "error", entry.line_number, f"RTTM {path_value}: {parse_error}")

        if args.check_ctm_speakers:
            path_value = entry.raw.get("ctm_filepath")
            if isinstance(path_value, str) and path_value:
                resolved = resolve_path(path_value, manifest_path, args.path_base)
                if resolved not in ctm_cache:
                    ctm_cache[resolved] = parse_ctm_file(resolved)
                speakers, recording_ids, parse_errors = ctm_cache[resolved]
                entry.ctm_speakers = set(speakers)
                entry.ctm_recording_ids = set(recording_ids)
                for parse_error in parse_errors:
                    add_issue(issues, "error", entry.line_number, f"CTM {path_value}: {parse_error}")


def is_placeholder_speaker_label(value: str) -> bool:
    return value.strip().lower() in {"", "-", "infer", "unknown", "na", "<na>", "null", "none"}


def compare_speaker_sets(entries: list[ManifestEntry], mode: str, issues: list[Issue]) -> None:
    if mode == "off":
        return
    issue_level = "error" if mode == "strict" else "warning"
    for entry in entries:
        manifest_speaker = entry.raw.get("speaker")
        manifest_label = entry.raw.get("label")
        manifest_speakers = {value for value in (manifest_speaker,) if isinstance(value, str) and value}
        if isinstance(manifest_label, str) and not is_placeholder_speaker_label(manifest_label):
            manifest_speakers.add(manifest_label)
        if manifest_speakers and entry.rttm_speakers and not manifest_speakers.issubset(entry.rttm_speakers):
            message = (
                f"manifest speaker/label {sorted(manifest_speakers)} not found in "
                f"RTTM speakers {sorted(entry.rttm_speakers)}"
            )
            add_issue(issues, issue_level, entry.line_number, message)
        if manifest_speakers and entry.ctm_speakers and not manifest_speakers.issubset(entry.ctm_speakers):
            message = (
                f"manifest speaker/label {sorted(manifest_speakers)} not found in "
                f"CTM speakers {sorted(entry.ctm_speakers)}"
            )
            add_issue(issues, issue_level, entry.line_number, message)
        if entry.rttm_speakers and entry.ctm_speakers and entry.rttm_speakers != entry.ctm_speakers:
            add_issue(
                issues,
                issue_level,
                entry.line_number,
                f"RTTM speakers {sorted(entry.rttm_speakers)} differ from CTM speakers {sorted(entry.ctm_speakers)}",
            )


def compare_recording_ids(entries: list[ManifestEntry], issues: list[Issue]) -> None:
    for entry in entries:
        expected_id = get_recording_id(entry)
        if not expected_id:
            continue
        if entry.rttm_recording_ids and expected_id not in entry.rttm_recording_ids:
            add_issue(
                issues,
                "warning",
                entry.line_number,
                f"manifest id {expected_id!r} not present in RTTM recording IDs {sorted(entry.rttm_recording_ids)}",
            )
        if entry.ctm_recording_ids and expected_id not in entry.ctm_recording_ids:
            add_issue(
                issues,
                "warning",
                entry.line_number,
                f"manifest id {expected_id!r} not present in CTM source IDs {sorted(entry.ctm_recording_ids)}",
            )


def print_issues(issues: list[Issue], quiet: bool) -> None:
    for issue in issues:
        if quiet and issue.level == "warning":
            continue
        prefix = issue.level.upper()
        location = f"line {issue.line}: " if issue.line is not None else ""
        stream = sys.stderr if issue.level == "error" else sys.stdout
        print(f"{prefix}: {location}{issue.message}", file=stream)


def main() -> int:
    args = parse_args()
    apply_task_requirements(args)

    issues: list[Issue] = []
    manifest_path = args.manifest.expanduser()
    allowed_audio_extensions = normalize_extensions(args.allowed_audio_ext)

    if path_suffix(str(manifest_path)) and path_suffix(str(manifest_path)) not in JSON_EXTENSIONS:
        add_issue(issues, "warning", None, "manifest filename should usually end with .json or .jsonl")

    entries = load_manifest(manifest_path, args.max_lines, issues)
    if not entries and not any(issue.level == "error" for issue in issues):
        add_issue(issues, "error", None, "manifest has no non-empty JSON lines")

    for entry in entries:
        validate_required_fields(entry, args, issues)
        validate_types_and_values(entry, args, issues)
        validate_extensions(entry, allowed_audio_extensions, issues)
        validate_existing_paths(entry, manifest_path, args, issues)
        if args.require_matching_basename:
            validate_matching_basenames(entry, issues)

    if args.require_unique_audio_basename:
        validate_unique_audio_basenames(entries, issues)

    if args.check_rttm_speakers or args.check_ctm_speakers:
        parse_referenced_speaker_files(entries, manifest_path, args, issues)
        compare_recording_ids(entries, issues)

    compare_speaker_sets(entries, args.speaker_consistency, issues)
    print_issues(issues, args.quiet)

    error_count = sum(1 for issue in issues if issue.level == "error")
    warning_count = sum(1 for issue in issues if issue.level == "warning")
    if error_count:
        print(
            f"FAILED: {error_count} error(s), {warning_count} warning(s), {len(entries)} line(s) checked",
            file=sys.stderr,
        )
        return 1
    print(f"OK: {len(entries)} line(s) checked, {warning_count} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
