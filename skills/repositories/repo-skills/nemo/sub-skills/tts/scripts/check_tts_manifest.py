#!/usr/bin/env python3
"""Validate NeMo TTS and G2P JSONL manifests without importing NeMo.

The checker is intentionally read-only: it parses JSON Lines, validates fields,
optionally checks path existence, and prints a summary. It does not open audio
contents, download models, train, or write output files.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import string
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

AUDIO_EXTENSIONS = (".wav", ".flac", ".mp3", ".ogg", ".opus", ".m4a", ".aif", ".aiff")
CODE_EXTENSIONS = (".pt", ".pth", ".npy", ".npz")
TEXT_FIELDS = ("text", "normalized_text")
SPEAKER_FIELDS = ("speaker", "speaker_id")
CONTEXT_AUDIO_FIELDS = ("context_audio_filepath", "context_audio")
CONTEXT_TEXT_FIELDS = ("context_text", "context_normalized_text")
CODE_PATH_FIELDS = ("target_audio_codes_path", "context_audio_codes_path", "audio_codes_path")
LEGACY_OR_CONTEXT_FIELDS = (
    "context_audio_filepath",
    "context_audio_duration",
    "context_text",
    "context_audio_codes_path",
    "target_audio_codes_path",
    "legacy_text_conditioning",
    "legacy_codebooks",
    "forced_num_all_tokens_per_codebook",
    "forced_audio_bos_id",
    "forced_audio_eos_id",
    "forced_context_audio_bos_id",
    "forced_context_audio_eos_id",
)
PHONEME_HINT_FIELDS = ("phonemes", "phoneme", "ipa", "arpabet", "text_phonemes")
GRAPHEME_HINT_FIELDS = ("text_graphemes", "graphemes", "text_raw")


class Issue:
    def __init__(self, severity: str, line: int | None, code: str, message: str):
        self.severity = severity
        self.line = line
        self.code = code
        self.message = message

    def as_dict(self) -> dict[str, Any]:
        return {"severity": self.severity, "line": self.line, "code": self.code, "message": self.message}

    def format(self) -> str:
        where = f"line {self.line}: " if self.line is not None else ""
        return f"[{self.severity}] {where}{self.code}: {self.message}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate NeMo TTS/MagpieTTS/G2P JSONL manifests without importing NeMo or opening audio contents."
    )
    parser.add_argument("manifest", type=Path, help="Path to the JSONL manifest to validate.")
    parser.add_argument(
        "--mode",
        choices=("tts", "magpie", "g2p", "auto"),
        default="auto",
        help="Validation profile. auto infers extra checks from fields but keeps TTS-safe defaults.",
    )
    parser.add_argument("--id-key", default="id", help="Optional record ID key used for duplicate detection.")
    parser.add_argument("--audio-key", default="audio_filepath", help="Manifest key for target/training audio paths.")
    parser.add_argument("--duration-key", default="duration", help="Manifest key for duration in seconds.")
    parser.add_argument("--text-field", default="text", help="Primary TTS transcript field.")
    parser.add_argument(
        "--normalized-text-field",
        default="normalized_text",
        help="Optional normalized transcript field.",
    )
    parser.add_argument("--grapheme-field", default="text_graphemes", help="G2P grapheme input field.")
    parser.add_argument("--phoneme-field", default="text", help="G2P phoneme/label field.")
    parser.add_argument(
        "--require-audio",
        action="store_true",
        help="Require audio-key to be present and non-empty, as for TTS training/evaluation.",
    )
    parser.add_argument(
        "--allow-missing-audio",
        action="store_true",
        help="Allow missing audio even when mode would normally require it.",
    )
    parser.add_argument(
        "--require-context",
        action="store_true",
        help="Require Magpie-style context audio or context text fields.",
    )
    parser.add_argument(
        "--allow-empty-text",
        action="store_true",
        help="Allow empty primary text fields. Use only for unusual inference manifests.",
    )
    parser.add_argument(
        "--allow-missing-phonemes",
        action="store_true",
        help="For G2P mode, allow missing phoneme labels as in inference-only manifests.",
    )
    parser.add_argument(
        "--allow-blank-lines",
        action="store_true",
        help="Allow and skip blank lines. Regular NeMo manifests should not use this.",
    )
    parser.add_argument("--check-files", action="store_true", help="Check that referenced audio/code files exist.")
    parser.add_argument(
        "--audio-base-dir",
        type=Path,
        default=None,
        help="Base directory for resolving relative audio/context paths. Defaults to manifest parent.",
    )
    parser.add_argument(
        "--feature-base-dir",
        type=Path,
        default=None,
        help="Base directory for resolving relative codec/code paths. Defaults to audio-base-dir.",
    )
    parser.add_argument("--min-duration", type=float, default=None, help="Warn for durations below this many seconds.")
    parser.add_argument("--max-duration", type=float, default=None, help="Warn for durations above this many seconds.")
    parser.add_argument("--max-lines", type=int, default=None, help="Validate at most this many manifest records.")
    parser.add_argument(
        "--strict-audio-extension",
        action="store_true",
        help="Warn when audio paths do not use a common audio extension.",
    )
    parser.add_argument(
        "--style-summary",
        action="store_true",
        help="Print text style, speaker, language, tokenizer, context, and field summaries.",
    )
    parser.add_argument("--json-summary", action="store_true", help="Emit a machine-readable JSON summary.")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-issue text output; summary is still printed.",
    )
    parser.add_argument("--max-examples", type=int, default=10, help="Maximum issues to print per issue code.")
    return parser.parse_args()


def add_issue(issues: list[Issue], severity: str, line: int | None, code: str, message: str) -> None:
    issues.append(Issue(severity, line, code, message))


def is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def as_path(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None


def resolve_path(path_text: str, base_dir: Path) -> Path:
    path = Path(path_text).expanduser()
    if path.is_absolute():
        return path
    return base_dir / path


def contains_phoneme_markers(text: str) -> bool:
    if not text:
        return False
    ipa_markers = set("ˈˌəɪʊɔæɑɒɛɜɡɫɹʃʒθðŋʔɲʎçøœɯɤɨʂʐɕʑ")
    arpabet_markers = {
        "AA",
        "AE",
        "AH",
        "AO",
        "AW",
        "AY",
        "CH",
        "DH",
        "EH",
        "ER",
        "EY",
        "IH",
        "IY",
        "NG",
        "OW",
        "OY",
        "SH",
        "TH",
        "UH",
        "UW",
        "ZH",
    }
    upper_tokens = {token.strip("{}[]<>/|") for token in text.split() if token.isupper()}
    return (
        any(char in ipa_markers for char in text)
        or bool(arpabet_markers & upper_tokens)
        or "<" in text
        and ">" in text
    )


def contains_grapheme_markers(text: str) -> bool:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return False
    ascii_letters = sum(1 for char in letters if char in string.ascii_letters)
    return ascii_letters >= max(1, len(letters) // 2) and not contains_phoneme_markers(text)


def text_style(text: str) -> dict[str, bool]:
    return {
        "empty": text == "",
        "whitespace_only": text.strip() == "",
        "edge_space": text != text.strip(),
        "repeated_space": "  " in text,
        "has_digit": any(char.isdigit() for char in text),
        "has_ascii_punctuation": any(char in string.punctuation for char in text),
        "has_ipa_or_arpabet_hint": contains_phoneme_markers(text),
        "looks_graphemic": contains_grapheme_markers(text),
    }


def validate_path_field(
    record: dict[str, Any],
    key: str,
    label: str,
    line_no: int,
    base_dir: Path,
    args: argparse.Namespace,
    issues: list[Issue],
    required: bool,
    expected_extensions: tuple[str, ...],
    seen_paths: Counter[str],
) -> str | None:
    if key not in record or record[key] in (None, ""):
        if required:
            add_issue(issues, "error", line_no, f"missing_{key}", f"missing required {label} field {key!r}")
        return None

    path_text = as_path(record[key])
    if path_text is None:
        add_issue(issues, "error", line_no, f"bad_{key}", f"{label} field {key!r} must be a non-empty string")
        return None

    path = resolve_path(path_text, base_dir)
    seen_paths[str(path.resolve(strict=False))] += 1
    if args.strict_audio_extension and expected_extensions and path.suffix.lower() not in expected_extensions:
        add_issue(
            issues,
            "warning",
            line_no,
            f"unusual_{key}_extension",
            f"{label} path {path_text!r} does not end with one of {', '.join(expected_extensions)}",
        )
    if args.check_files and not path.is_file():
        add_issue(
            issues,
            "error",
            line_no,
            f"missing_{key}_file",
            f"{label} file does not exist: {path_text!r}",
        )
    return path_text


def validate_duration(
    record: dict[str, Any],
    line_no: int,
    args: argparse.Namespace,
    issues: list[Issue],
) -> float | None:
    if args.duration_key not in record:
        add_issue(issues, "warning", line_no, "missing_duration", f"missing duration field {args.duration_key!r}")
        return None
    value = record[args.duration_key]
    if not is_finite_number(value):
        add_issue(
            issues,
            "error",
            line_no,
            "bad_duration",
            f"duration field {args.duration_key!r} must be a finite number",
        )
        return None
    duration = float(value)
    if duration <= 0:
        add_issue(issues, "error", line_no, "nonpositive_duration", f"duration must be positive, got {duration:g}")
    if args.min_duration is not None and duration < args.min_duration:
        add_issue(
            issues,
            "warning",
            line_no,
            "below_min_duration",
            f"duration {duration:g}s is below --min-duration {args.min_duration:g}s",
        )
    if args.max_duration is not None and duration > args.max_duration:
        add_issue(
            issues,
            "warning",
            line_no,
            "above_max_duration",
            f"duration {duration:g}s is above --max-duration {args.max_duration:g}s",
        )
    return duration


def validate_text(
    record: dict[str, Any],
    line_no: int,
    args: argparse.Namespace,
    issues: list[Issue],
) -> str | None:
    text = record.get(args.text_field)
    normalized = record.get(args.normalized_text_field)

    if text is None and normalized is None and args.mode != "g2p":
        add_issue(
            issues,
            "error",
            line_no,
            "missing_text",
            f"missing {args.text_field!r} or {args.normalized_text_field!r}",
        )
        return None

    if text is not None and not isinstance(text, str):
        add_issue(issues, "error", line_no, "bad_text", f"{args.text_field!r} must be a string")
        text = None
    if normalized is not None and not isinstance(normalized, str):
        add_issue(issues, "error", line_no, "bad_normalized_text", f"{args.normalized_text_field!r} must be a string")
        normalized = None

    primary = text if isinstance(text, str) else normalized if isinstance(normalized, str) else None
    if primary is not None:
        if primary.strip() == "" and not args.allow_empty_text:
            add_issue(issues, "error", line_no, "empty_text", "text is empty or whitespace-only")
        elif primary != primary.strip():
            add_issue(issues, "warning", line_no, "text_edge_whitespace", "text has leading or trailing whitespace")
        if "  " in primary:
            add_issue(issues, "warning", line_no, "text_repeated_spaces", "text contains repeated spaces")

    if isinstance(text, str) and isinstance(normalized, str):
        if text.strip() and normalized.strip() and text.strip() != normalized.strip():
            if contains_phoneme_markers(text) != contains_phoneme_markers(normalized):
                add_issue(
                    issues,
                    "warning",
                    line_no,
                    "text_normalized_style_mismatch",
                    "text and normalized_text appear to use different grapheme/phoneme styles",
                )
    return primary


def validate_g2p(
    record: dict[str, Any],
    line_no: int,
    args: argparse.Namespace,
    issues: list[Issue],
) -> None:
    graphemes = record.get(args.grapheme_field)
    phonemes = record.get(args.phoneme_field)

    if not isinstance(graphemes, str) or not graphemes.strip():
        add_issue(
            issues,
            "error",
            line_no,
            "missing_graphemes",
            f"missing non-empty grapheme field {args.grapheme_field!r}",
        )
    if not args.allow_missing_phonemes:
        if not isinstance(phonemes, str) or not phonemes.strip():
            add_issue(
                issues,
                "error",
                line_no,
                "missing_phonemes",
                f"missing non-empty phoneme field {args.phoneme_field!r}",
            )
    elif phonemes is not None and not isinstance(phonemes, str):
        add_issue(
            issues,
            "error",
            line_no,
            "bad_phonemes",
            f"phoneme field {args.phoneme_field!r} must be a string when present",
        )

    if isinstance(graphemes, str) and contains_phoneme_markers(graphemes):
        add_issue(
            issues,
            "warning",
            line_no,
            "graphemes_look_phonemic",
            f"{args.grapheme_field!r} appears to contain phoneme markers",
        )
    phonemes_look_graphemic = (
        isinstance(phonemes, str)
        and phonemes.strip()
        and contains_grapheme_markers(phonemes)
        and not contains_phoneme_markers(phonemes)
    )
    if phonemes_look_graphemic:
        add_issue(
            issues,
            "warning",
            line_no,
            "phonemes_look_graphemic",
            f"{args.phoneme_field!r} may contain graphemes rather than phonemes",
        )


def validate_context(
    record: dict[str, Any],
    line_no: int,
    args: argparse.Namespace,
    issues: list[Issue],
) -> None:
    has_context_audio = any(non_empty_string(record.get(field)) for field in CONTEXT_AUDIO_FIELDS)
    has_context_text = any(non_empty_string(record.get(field)) for field in CONTEXT_TEXT_FIELDS)
    if args.require_context and not (has_context_audio or has_context_text):
        add_issue(issues, "error", line_no, "missing_context", "missing Magpie context audio or context text")

    context_duration = record.get("context_audio_duration")
    if context_duration is not None:
        if not is_finite_number(context_duration):
            add_issue(issues, "error", line_no, "bad_context_audio_duration", "context_audio_duration must be numeric")
        elif float(context_duration) <= 0:
            add_issue(
                issues,
                "error",
                line_no,
                "nonpositive_context_audio_duration",
                "context_audio_duration must be positive",
            )
        elif float(context_duration) < 1.0:
            add_issue(
                issues,
                "warning",
                line_no,
                "short_context_audio",
                "context_audio_duration is very short for voice conditioning",
            )

    if has_context_audio and not has_context_text:
        add_issue(issues, "warning", line_no, "missing_context_text", "context audio is present without context_text")
    if has_context_text and not has_context_audio:
        add_issue(issues, "warning", line_no, "missing_context_audio", "context text is present without context audio")


def validate_speaker_language(
    record: dict[str, Any],
    line_no: int,
    args: argparse.Namespace,
    issues: list[Issue],
) -> None:
    speaker_values = [record.get(field) for field in SPEAKER_FIELDS if field in record]
    if args.mode == "magpie" and not speaker_values:
        add_issue(
            issues,
            "warning",
            line_no,
            "missing_speaker",
            "Magpie or multispeaker data often needs a stable speaker field",
        )
    for value in speaker_values:
        if isinstance(value, bool) or value in (None, ""):
            add_issue(issues, "warning", line_no, "bad_speaker", f"speaker value {value!r} is not useful")
        elif not isinstance(value, (str, int)):
            add_issue(
                issues,
                "warning",
                line_no,
                "bad_speaker_type",
                f"speaker value has unusual type {type(value).__name__}",
            )

    language = record.get("language") or record.get("lang")
    if language is not None and (not isinstance(language, str) or not language.strip()):
        add_issue(
            issues,
            "warning",
            line_no,
            "bad_language",
            "language/lang should be a non-empty string when present",
        )

    tokenizer_names = record.get("tokenizer_names")
    bad_tokenizer_names = (
        tokenizer_names is not None
        and (
            not isinstance(tokenizer_names, list)
            or not tokenizer_names
            or not all(isinstance(item, str) and item for item in tokenizer_names)
        )
    )
    if bad_tokenizer_names:
        add_issue(
            issues,
            "warning",
            line_no,
            "bad_tokenizer_names",
            "tokenizer_names should be a non-empty list of strings",
        )


def validate_record(
    record: Any,
    line_no: int,
    args: argparse.Namespace,
    audio_base_dir: Path,
    feature_base_dir: Path,
    issues: list[Issue],
    counters: dict[str, Counter[Any]],
    seen_audio_paths: Counter[str],
    seen_context_paths: Counter[str],
    seen_code_paths: Counter[str],
) -> tuple[float | None, str | None, dict[str, Any] | None]:
    if not isinstance(record, dict):
        add_issue(issues, "error", line_no, "not_object", "record is not a JSON object")
        return None, None, None

    counters["field"].update(record.keys())

    mode = args.mode
    require_audio = args.require_audio or mode in {"tts", "magpie"}
    if args.allow_missing_audio or mode == "g2p":
        require_audio = False

    validate_path_field(
        record,
        args.audio_key,
        "audio",
        line_no,
        audio_base_dir,
        args,
        issues,
        required=require_audio,
        expected_extensions=AUDIO_EXTENSIONS,
        seen_paths=seen_audio_paths,
    )

    for context_key in CONTEXT_AUDIO_FIELDS:
        if context_key in record:
            validate_path_field(
                record,
                context_key,
                "context audio",
                line_no,
                audio_base_dir,
                args,
                issues,
                required=False,
                expected_extensions=AUDIO_EXTENSIONS,
                seen_paths=seen_context_paths,
            )

    for code_key in CODE_PATH_FIELDS:
        if code_key in record:
            validate_path_field(
                record,
                code_key,
                "codec/code",
                line_no,
                feature_base_dir,
                args,
                issues,
                required=False,
                expected_extensions=CODE_EXTENSIONS,
                seen_paths=seen_code_paths,
            )

    duration = validate_duration(record, line_no, args, issues) if mode != "g2p" else None
    text = validate_text(record, line_no, args, issues)

    if mode == "g2p" or (mode == "auto" and args.grapheme_field in record):
        validate_g2p(record, line_no, args, issues)

    if mode == "magpie" or mode == "auto" and any(field in record for field in LEGACY_OR_CONTEXT_FIELDS):
        validate_context(record, line_no, args, issues)

    validate_speaker_language(record, line_no, args, issues)

    if args.id_key in record:
        identifier = record[args.id_key]
        if isinstance(identifier, (str, int)) and str(identifier).strip():
            counters["id"][str(identifier)] += 1
        else:
            add_issue(
                issues,
                "warning",
                line_no,
                "bad_id",
                f"id field {args.id_key!r} is present but not a useful string/int",
            )

    for field in PHONEME_HINT_FIELDS:
        if field in record:
            counters["phoneme_field"][field] += 1
    for field in GRAPHEME_HINT_FIELDS:
        if field in record:
            counters["grapheme_field"][field] += 1

    language = record.get("language") or record.get("lang")
    if isinstance(language, str) and language.strip():
        counters["language"][language.strip()] += 1
    for speaker_field in SPEAKER_FIELDS:
        speaker = record.get(speaker_field)
        if speaker not in (None, ""):
            counters["speaker"][str(speaker)] += 1
    for tokenizer in record.get("tokenizer_names", []) if isinstance(record.get("tokenizer_names"), list) else []:
        counters["tokenizer"][str(tokenizer)] += 1

    style = text_style(text) if isinstance(text, str) else None
    return duration, text, {"record": record, "style": style}


def percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return float("nan")
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * pct
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def duplicate_items(counter: Counter[str]) -> list[tuple[str, int]]:
    return [(key, count) for key, count in counter.items() if count > 1]


def print_counter(title: str, counter: Counter[Any], limit: int = 12) -> None:
    if not counter:
        return
    print(f"{title}:")
    for key, count in counter.most_common(limit):
        print(f"  {key!r}: {count}")
    if len(counter) > limit:
        print(f"  ... {len(counter) - limit} more")


def summarize_style(records: list[dict[str, Any]], counters: dict[str, Counter[Any]]) -> None:
    style_counts: Counter[str] = Counter()
    text_lengths: list[int] = []
    context_records = 0
    legacy_records = 0
    code_records = 0

    for item in records:
        record = item["record"]
        style = item["style"]
        if style:
            for key, value in style.items():
                if value:
                    style_counts[key] += 1
        text = record.get("text") or record.get("normalized_text")
        if isinstance(text, str):
            text_lengths.append(len(text))
        if any(field in record for field in CONTEXT_AUDIO_FIELDS + CONTEXT_TEXT_FIELDS):
            context_records += 1
        has_legacy_field = any(
            field in record
            for field in LEGACY_OR_CONTEXT_FIELDS
            if field.startswith("legacy") or field.startswith("forced")
        )
        if has_legacy_field:
            legacy_records += 1
        if any(field in record for field in CODE_PATH_FIELDS):
            code_records += 1

    print_counter("Field counts", counters["field"])
    print_counter("Languages", counters["language"])
    print_counter("Speakers", counters["speaker"])
    print_counter("Tokenizer names", counters["tokenizer"])
    print_counter("Phoneme-like fields", counters["phoneme_field"])
    print_counter("Grapheme-like fields", counters["grapheme_field"])
    print_counter("Text style flags", style_counts)
    if text_lengths:
        sorted_lengths = sorted(text_lengths)
        print(
            "Text chars: "
            f"min={sorted_lengths[0]} "
            f"p50={percentile(sorted_lengths, 0.50):.1f} "
            f"p95={percentile(sorted_lengths, 0.95):.1f} "
            f"max={sorted_lengths[-1]} "
            f"mean={statistics.fmean(sorted_lengths):.1f}"
        )
    print(f"Records with context fields: {context_records}")
    print(f"Records with cached code fields: {code_records}")
    print(f"Records with explicit legacy checkpoint fields: {legacy_records}")


def validate_manifest(args: argparse.Namespace) -> dict[str, Any]:
    issues: list[Issue] = []
    if not args.manifest.is_file():
        add_issue(issues, "error", None, "missing_manifest", f"manifest file does not exist: {args.manifest}")
        return {"ok": False, "issues": issues, "records": [], "durations": []}

    audio_base_dir = (args.audio_base_dir or args.manifest.parent).resolve(strict=False)
    feature_base_dir = (args.feature_base_dir or audio_base_dir).resolve(strict=False)
    counters: dict[str, Counter[Any]] = defaultdict(Counter)
    seen_audio_paths: Counter[str] = Counter()
    seen_context_paths: Counter[str] = Counter()
    seen_code_paths: Counter[str] = Counter()
    records: list[dict[str, Any]] = []
    durations: list[float] = []
    num_lines = 0
    num_records = 0

    with args.manifest.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            num_lines = line_no
            if args.max_lines is not None and num_records >= args.max_lines:
                break
            if not line.strip():
                if not args.allow_blank_lines:
                    add_issue(
                        issues,
                        "error",
                        line_no,
                        "blank_line",
                        "blank lines are invalid in regular NeMo manifests",
                    )
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                add_issue(issues, "error", line_no, "invalid_json", f"invalid JSON: {exc.msg}")
                continue
            num_records += 1
            duration, _text, record_summary = validate_record(
                record,
                line_no,
                args,
                audio_base_dir,
                feature_base_dir,
                issues,
                counters,
                seen_audio_paths,
                seen_context_paths,
                seen_code_paths,
            )
            if duration is not None:
                durations.append(duration)
            if record_summary is not None:
                records.append(record_summary)

    for duplicate_id, count in duplicate_items(counters["id"]):
        add_issue(issues, "error", None, "duplicate_id", f"id {duplicate_id!r} appears {count} times")
    for duplicate_path, count in duplicate_items(seen_audio_paths):
        add_issue(
            issues,
            "warning",
            None,
            "duplicate_audio_path",
            f"audio path appears {count} times: {duplicate_path}",
        )
    for duplicate_path, count in duplicate_items(seen_context_paths):
        add_issue(
            issues,
            "warning",
            None,
            "duplicate_context_audio_path",
            f"context audio path appears {count} times: {duplicate_path}",
        )

    errors = sum(1 for issue in issues if issue.severity == "error")
    warnings = sum(1 for issue in issues if issue.severity == "warning")
    return {
        "ok": errors == 0,
        "issues": issues,
        "records": records,
        "durations": durations,
        "num_lines": num_lines,
        "num_records": num_records,
        "audio_base_dir": str(audio_base_dir),
        "feature_base_dir": str(feature_base_dir),
        "counters": counters,
        "errors": errors,
        "warnings": warnings,
    }


def print_summary(result: dict[str, Any], args: argparse.Namespace) -> None:
    issues: list[Issue] = result["issues"]
    if not args.quiet:
        printed_by_code: Counter[str] = Counter()
        for issue in issues:
            if printed_by_code[issue.code] < args.max_examples:
                print(issue.format(), file=sys.stderr)
            elif printed_by_code[issue.code] == args.max_examples:
                print(f"[{issue.severity}] {issue.code}: ...", file=sys.stderr)
            printed_by_code[issue.code] += 1

    durations: list[float] = result.get("durations", [])
    print(f"Manifest: {args.manifest}")
    print(f"Mode: {args.mode}")
    print(f"Records: {result.get('num_records', 0)}")
    print(f"Errors: {result.get('errors', 0)}")
    print(f"Warnings: {result.get('warnings', 0)}")
    if durations:
        sorted_durations = sorted(durations)
        print(
            "Durations seconds: "
            f"min={sorted_durations[0]:.3f} "
            f"p50={percentile(sorted_durations, 0.50):.3f} "
            f"p95={percentile(sorted_durations, 0.95):.3f} "
            f"max={sorted_durations[-1]:.3f} "
            f"mean={statistics.fmean(sorted_durations):.3f} "
            f"total={sum(sorted_durations):.3f}"
        )
    if args.style_summary and result.get("records"):
        summarize_style(result["records"], result["counters"])


def json_safe_result(result: dict[str, Any]) -> dict[str, Any]:
    counters = result.get("counters", {})
    return {
        "ok": result.get("ok", False),
        "num_records": result.get("num_records", 0),
        "errors": result.get("errors", 0),
        "warnings": result.get("warnings", 0),
        "audio_base_dir": result.get("audio_base_dir"),
        "feature_base_dir": result.get("feature_base_dir"),
        "duration_count": len(result.get("durations", [])),
        "issues": [issue.as_dict() for issue in result.get("issues", [])],
        "counters": {name: dict(counter) for name, counter in counters.items()},
    }


def main() -> int:
    args = parse_args()
    result = validate_manifest(args)
    if args.json_summary:
        print(json.dumps(json_safe_result(result), indent=2, sort_keys=True))
    else:
        print_summary(result, args)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
