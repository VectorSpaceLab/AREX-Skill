#!/usr/bin/env python3
"""Validate MOSS-TTS fine-tuning JSONL manifests without model imports."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

TASK_CHOICES = (
    "auto",
    "moss-tts",
    "ttsd",
    "soundeffect-v1",
    "voice-generator",
    "realtime",
    "local-v15",
)

DEFAULT_EXPECTED_N_VQ = {
    "ttsd": 16,
    "realtime": 16,
    "local-v15": 12,
}

TEXT_TASKS = {"moss-tts", "ttsd", "local-v15"}
OPTIONAL_USER_FIELDS = ("language", "tokens", "quality", "sound_event")


@dataclass
class Issue:
    level: str
    line: int
    row_id: str
    message: str


@dataclass
class Counters:
    rows: int = 0
    blank_lines: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    errors: int = 0
    warnings: int = 0
    audio_paths_checked: int = 0
    missing_audio_paths: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate MOSS-TTS fine-tuning JSONL rows for raw preprocessing "
            "or prepared SFT training. No torch/model imports are used."
        )
    )
    parser.add_argument("jsonl", type=Path, help="JSONL manifest to validate.")
    parser.add_argument(
        "--task",
        choices=TASK_CHOICES,
        default="auto",
        help="Task schema to enforce. Use auto to infer per row. Default: auto.",
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "raw", "prepared"),
        default="auto",
        help=(
            "raw requires audio/wav path fields, prepared requires *_codes fields, "
            "auto accepts either where appropriate. Default: auto."
        ),
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=None,
        help="Base directory for local audio path existence checks. Default: JSONL parent.",
    )
    parser.add_argument(
        "--no-exists-check",
        action="store_true",
        help="Do not check whether local audio paths exist; validate only schema and shapes.",
    )
    parser.add_argument(
        "--expected-n-vq",
        type=int,
        default=None,
        help=(
            "Expected RVQ depth for coded fields. Overrides task defaults "
            "(TTSD=16, Realtime=16, Local v1.5=12)."
        ),
    )
    parser.add_argument(
        "--no-default-n-vq",
        action="store_true",
        help="Disable task default RVQ-depth checks unless --expected-n-vq is provided.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Summary output format. Default: text.",
    )
    parser.add_argument(
        "--max-issues",
        type=int,
        default=80,
        help="Maximum issues to print or include in JSON. Default: 80.",
    )
    return parser.parse_args()


def add_issue(issues: List[Issue], counters: Counters, level: str, line: int, row_id: Any, message: str) -> None:
    row_id_str = str(row_id) if row_id not in (None, "") else f"line-{line}"
    issues.append(Issue(level=level, line=line, row_id=row_id_str, message=message))
    if level == "error":
        counters.errors += 1
    else:
        counters.warnings += 1


def is_uri(path: str) -> bool:
    return "://" in path or path.startswith("hf://")


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def resolve_audio_path(path: str, base_dir: Path) -> Path:
    path_obj = Path(path).expanduser()
    if path_obj.is_absolute():
        return path_obj
    return base_dir / path_obj


def check_path_field(
    value: Any,
    field_name: str,
    line: int,
    row_id: Any,
    issues: List[Issue],
    counters: Counters,
    base_dir: Path,
    exists_check: bool,
) -> bool:
    if not nonempty_string(value):
        add_issue(issues, counters, "error", line, row_id, f"`{field_name}` must be a non-empty string path.")
        return False
    stripped = value.strip()
    if is_uri(stripped):
        return True
    if exists_check:
        counters.audio_paths_checked += 1
        resolved = resolve_audio_path(stripped, base_dir)
        if not resolved.exists():
            counters.missing_audio_paths += 1
            add_issue(
                issues,
                counters,
                "error",
                line,
                row_id,
                f"`{field_name}` path does not exist from base dir: {stripped}",
            )
            return False
    return True


def first_non_none(values: Iterable[Any]) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def looks_like_number_row(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, int) and not isinstance(item, bool) for item in value)


def matrix_shape(value: Any) -> Optional[Tuple[int, int, str]]:
    """Return (rows, cols, error). error is empty when valid."""
    if not isinstance(value, list) or not value:
        return None
    if not all(isinstance(row, list) for row in value):
        return None
    rows = len(value)
    if rows == 0:
        return None
    first_row = value[0]
    if not isinstance(first_row, list) or not first_row:
        return (rows, 0, "matrix rows must be non-empty lists")
    if not all(not isinstance(item, list) for item in first_row):
        return None
    cols = len(first_row)
    for r_index, row in enumerate(value):
        if not isinstance(row, list) or len(row) != cols:
            return (rows, cols, f"matrix rows must be rectangular; row {r_index} has length {len(row) if isinstance(row, list) else 'non-list'}")
        for c_index, item in enumerate(row):
            if not isinstance(item, int) or isinstance(item, bool):
                return (rows, cols, f"matrix values must be integers; found {type(item).__name__} at [{r_index}][{c_index}]")
    return (rows, cols, "")


def validate_code_matrix(
    value: Any,
    field_name: str,
    line: int,
    row_id: Any,
    issues: List[Issue],
    counters: Counters,
    expected_n_vq: Optional[int],
    realtime_orientation_ok: bool = False,
) -> Optional[int]:
    shape = matrix_shape(value)
    if shape is None:
        add_issue(issues, counters, "error", line, row_id, f"`{field_name}` must be a 2-D integer list shaped [time][n_vq].")
        return None
    rows, cols, err = shape
    if err:
        add_issue(issues, counters, "error", line, row_id, f"`{field_name}` invalid: {err}.")
        return None
    if expected_n_vq is not None:
        if cols == expected_n_vq:
            return cols
        if realtime_orientation_ok and rows == expected_n_vq:
            add_issue(
                issues,
                counters,
                "warning",
                line,
                row_id,
                f"`{field_name}` appears transposed as [n_vq][time]; prefer [time][{expected_n_vq}].",
            )
            return rows
        add_issue(
            issues,
            counters,
            "error",
            line,
            row_id,
            f"`{field_name}` has n_vq={cols}; expected {expected_n_vq}.",
        )
        return None
    return cols


def is_matrix(value: Any) -> bool:
    shape = matrix_shape(value)
    return shape is not None and not shape[2]


def validate_code_list_or_matrix(
    value: Any,
    field_name: str,
    line: int,
    row_id: Any,
    issues: List[Issue],
    counters: Counters,
    expected_n_vq: Optional[int],
    allow_none_items: bool,
) -> List[int]:
    depths: List[int] = []
    if value in (None, "", []):
        return depths
    if is_matrix(value):
        depth = validate_code_matrix(value, field_name, line, row_id, issues, counters, expected_n_vq)
        if depth is not None:
            depths.append(depth)
        return depths
    if not isinstance(value, list):
        add_issue(issues, counters, "error", line, row_id, f"`{field_name}` must be a code matrix or list of code matrices.")
        return depths
    for index, item in enumerate(value):
        item_field = f"{field_name}[{index}]"
        if item is None:
            if allow_none_items:
                continue
            add_issue(issues, counters, "error", line, row_id, f"`{item_field}` must not be null for this task/field.")
            continue
        depth = validate_code_matrix(item, item_field, line, row_id, issues, counters, expected_n_vq)
        if depth is not None:
            depths.append(depth)
    return depths


def validate_reference_path_field(
    record: Dict[str, Any],
    field_name: str,
    task: str,
    line: int,
    row_id: Any,
    issues: List[Issue],
    counters: Counters,
    base_dir: Path,
    exists_check: bool,
) -> None:
    if field_name not in record or record.get(field_name) in (None, "", []):
        return
    value = record.get(field_name)
    allow_null = field_name == "reference" and task == "ttsd"
    if field_name == "ref_audio":
        if isinstance(value, list):
            if len(value) != 1:
                add_issue(issues, counters, "error", line, row_id, "`ref_audio` supports exactly one path, not a multi-reference list.")
                return
            value = value[0] if value else None
        check_path_field(value, field_name, line, row_id, issues, counters, base_dir, exists_check)
        return
    if isinstance(value, str):
        check_path_field(value, field_name, line, row_id, issues, counters, base_dir, exists_check)
        return
    if not isinstance(value, list):
        add_issue(issues, counters, "error", line, row_id, f"`{field_name}` must be a string or list of strings.")
        return
    if not value:
        return
    for index, item in enumerate(value):
        item_name = f"{field_name}[{index}]"
        if item is None:
            if allow_null:
                continue
            add_issue(issues, counters, "error", line, row_id, f"`{item_name}` is null; null reference placeholders are only valid for TTSD `reference` lists.")
            continue
        check_path_field(item, item_name, line, row_id, issues, counters, base_dir, exists_check)


def infer_task(record: Dict[str, Any]) -> str:
    if isinstance(record.get("conversations"), list):
        return "realtime"
    if record.get("ambient_sound") is not None and record.get("instruction") is None:
        return "soundeffect-v1"
    if record.get("instruction") is not None:
        return "voice-generator"
    reference = record.get("reference")
    if isinstance(reference, list) and (any(item is None for item in reference) or len(reference) > 1):
        return "ttsd"
    return "moss-tts"


def expected_n_vq_for_task(args: argparse.Namespace, task: str) -> Optional[int]:
    if args.expected_n_vq is not None:
        return args.expected_n_vq
    if args.no_default_n_vq:
        return None
    return DEFAULT_EXPECTED_N_VQ.get(task)


def require_path_or_codes(
    record: Dict[str, Any],
    field_name: str,
    code_field: str,
    line: int,
    row_id: Any,
    issues: List[Issue],
    counters: Counters,
    mode: str,
) -> None:
    has_path = nonempty_string(record.get(field_name))
    has_codes = record.get(code_field) not in (None, "", [])
    if mode == "raw" and not has_path:
        add_issue(issues, counters, "error", line, row_id, f"raw mode requires `{field_name}`.")
    elif mode == "prepared" and not has_codes:
        add_issue(issues, counters, "error", line, row_id, f"prepared mode requires `{code_field}`.")
    elif mode == "auto" and not (has_path or has_codes):
        add_issue(issues, counters, "error", line, row_id, f"row needs either raw `{field_name}` or prepared `{code_field}`.")


def validate_optional_fields(
    record: Dict[str, Any],
    line: int,
    row_id: Any,
    issues: List[Issue],
    counters: Counters,
) -> None:
    if "language" in record and record.get("language") is not None and not nonempty_string(record.get("language")):
        add_issue(issues, counters, "error", line, row_id, "`language` must be a non-empty string when present.")
    if "tokens" in record and record.get("tokens") is not None and not is_positive_int(record.get("tokens")):
        add_issue(issues, counters, "error", line, row_id, "`tokens` must be a positive integer when present.")
    for field in ("quality", "sound_event"):
        if field in record and record.get(field) is not None and not nonempty_string(record.get(field)):
            add_issue(issues, counters, "warning", line, row_id, f"`{field}` is present but not a non-empty string.")


def validate_nonrealtime(
    record: Dict[str, Any],
    task: str,
    line: int,
    args: argparse.Namespace,
    base_dir: Path,
    exists_check: bool,
    issues: List[Issue],
    counters: Counters,
) -> None:
    row_id = record.get("id", line)
    expected_n_vq = expected_n_vq_for_task(args, task)

    require_path_or_codes(record, "audio", "audio_codes", line, row_id, issues, counters, args.mode)
    if record.get("audio") not in (None, ""):
        check_path_field(record.get("audio"), "audio", line, row_id, issues, counters, base_dir, exists_check)

    if task in TEXT_TASKS:
        if not nonempty_string(record.get("text")):
            add_issue(issues, counters, "error", line, row_id, f"`{task}` rows require non-empty `text`.")
    elif task == "soundeffect-v1":
        if not nonempty_string(record.get("ambient_sound")):
            add_issue(issues, counters, "error", line, row_id, "`soundeffect-v1` rows require non-empty `ambient_sound`.")
    elif task == "voice-generator":
        if not nonempty_string(record.get("text")):
            add_issue(issues, counters, "error", line, row_id, "`voice-generator` rows require non-empty `text`.")
        if not nonempty_string(record.get("instruction")):
            add_issue(issues, counters, "error", line, row_id, "`voice-generator` rows require non-empty `instruction`.")

    if task == "local-v15":
        if isinstance(record.get("ref_audio"), list):
            add_issue(issues, counters, "error", line, row_id, "Local v1.5 `ref_audio` must be a single string, not a list.")
        reference = record.get("reference")
        if isinstance(reference, list) and (len(reference) > 1 or any(item is None for item in reference)):
            add_issue(
                issues,
                counters,
                "warning",
                line,
                row_id,
                "Local v1.5 public fine-tuning documents single-reference training; multi-reference/null `reference` lists should be routed to TTSD unless separately justified.",
            )

    for field_name in ("ref_audio", "reference_audio", "reference"):
        validate_reference_path_field(record, field_name, task, line, row_id, issues, counters, base_dir, exists_check)

    depths: List[Tuple[str, int]] = []
    if record.get("audio_codes") not in (None, "", []):
        depth = validate_code_matrix(record.get("audio_codes"), "audio_codes", line, row_id, issues, counters, expected_n_vq)
        if depth is not None:
            depths.append(("audio_codes", depth))
    if record.get("ref_audio_codes") not in (None, "", []):
        depth = validate_code_matrix(record.get("ref_audio_codes"), "ref_audio_codes", line, row_id, issues, counters, expected_n_vq)
        if depth is not None:
            depths.append(("ref_audio_codes", depth))
    if record.get("reference_audio_codes") not in (None, "", []):
        allow_none = task == "ttsd"
        ref_depths = validate_code_list_or_matrix(
            record.get("reference_audio_codes"),
            "reference_audio_codes",
            line,
            row_id,
            issues,
            counters,
            expected_n_vq,
            allow_none_items=allow_none,
        )
        depths.extend(("reference_audio_codes", depth) for depth in ref_depths)

    if depths:
        target_depth = first_non_none(depth for field, depth in depths if field == "audio_codes")
        if target_depth is not None:
            for field, depth in depths:
                if depth != target_depth:
                    add_issue(
                        issues,
                        counters,
                        "error",
                        line,
                        row_id,
                        f"`{field}` n_vq={depth} does not match target audio_codes n_vq={target_depth}.",
                    )

    if args.mode == "prepared":
        for path_field, code_field in (("ref_audio", "ref_audio_codes"), ("reference_audio", "reference_audio_codes"), ("reference", "reference_audio_codes")):
            if record.get(path_field) not in (None, "", []) and record.get(code_field) in (None, "", []):
                add_issue(
                    issues,
                    counters,
                    "warning",
                    line,
                    row_id,
                    f"prepared row has `{path_field}` but no `{code_field}`; training may need to encode references on the fly.",
                )

    validate_optional_fields(record, line, row_id, issues, counters)


def validate_realtime(
    record: Dict[str, Any],
    line: int,
    args: argparse.Namespace,
    base_dir: Path,
    exists_check: bool,
    issues: List[Issue],
    counters: Counters,
) -> None:
    row_id = record.get("id", line)
    expected_n_vq = expected_n_vq_for_task(args, "realtime")
    conversations = record.get("conversations")
    if not isinstance(conversations, list) or not conversations:
        add_issue(issues, counters, "error", line, row_id, "`realtime` rows require a non-empty `conversations` list.")
        return

    has_assistant = False
    for index, turn in enumerate(conversations):
        turn_label = f"conversations[{index}]"
        if not isinstance(turn, dict):
            add_issue(issues, counters, "error", line, row_id, f"`{turn_label}` must be an object.")
            continue
        role = turn.get("role")
        if role not in ("user", "assistant"):
            add_issue(issues, counters, "error", line, row_id, f"`{turn_label}.role` must be `user` or `assistant`.")
        if role == "assistant":
            has_assistant = True
        if not nonempty_string(turn.get("text")):
            add_issue(issues, counters, "error", line, row_id, f"`{turn_label}.text` must be a non-empty string.")

        has_wav = nonempty_string(turn.get("wav"))
        has_codes = turn.get("audio_codes") not in (None, "", [])
        if args.mode == "raw" and not has_wav:
            add_issue(issues, counters, "error", line, row_id, f"raw mode requires `{turn_label}.wav`.")
        elif args.mode == "prepared" and not has_codes:
            add_issue(issues, counters, "error", line, row_id, f"prepared mode requires `{turn_label}.audio_codes`.")
        elif args.mode == "auto" and not (has_wav or has_codes):
            add_issue(issues, counters, "error", line, row_id, f"`{turn_label}` needs either raw `wav` or prepared `audio_codes`.")
        if has_wav:
            check_path_field(turn.get("wav"), f"{turn_label}.wav", line, row_id, issues, counters, base_dir, exists_check)
        if has_codes:
            validate_code_matrix(
                turn.get("audio_codes"),
                f"{turn_label}.audio_codes",
                line,
                row_id,
                issues,
                counters,
                expected_n_vq,
                realtime_orientation_ok=True,
            )

    if not has_assistant:
        add_issue(issues, counters, "error", line, row_id, "Realtime row has no assistant turn; preprocessing skips these rows.")

    if record.get("ref_wav") not in (None, ""):
        check_path_field(record.get("ref_wav"), "ref_wav", line, row_id, issues, counters, base_dir, exists_check)
        if args.mode == "prepared" and record.get("ref_audio_codes") in (None, "", []):
            add_issue(issues, counters, "error", line, row_id, "prepared Realtime row with `ref_wav` requires `ref_audio_codes`.")
    if record.get("ref_audio_codes") not in (None, "", []):
        validate_code_matrix(
            record.get("ref_audio_codes"),
            "ref_audio_codes",
            line,
            row_id,
            issues,
            counters,
            expected_n_vq,
            realtime_orientation_ok=True,
        )


def read_jsonl(path: Path, issues: List[Issue], counters: Counters) -> List[Tuple[int, Dict[str, Any]]]:
    rows: List[Tuple[int, Dict[str, Any]]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    counters.blank_lines += 1
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    add_issue(issues, counters, "error", line_number, f"line-{line_number}", f"invalid JSON: {exc.msg}")
                    continue
                if not isinstance(value, dict):
                    add_issue(issues, counters, "error", line_number, f"line-{line_number}", "each JSONL line must be an object.")
                    continue
                rows.append((line_number, value))
    except OSError as exc:
        add_issue(issues, counters, "error", 0, "file", f"cannot read JSONL: {exc}")
    return rows


def validate_rows(args: argparse.Namespace) -> Tuple[Counters, List[Issue], Dict[str, int]]:
    issues: List[Issue] = []
    counters = Counters()
    base_dir = (args.base_dir if args.base_dir is not None else args.jsonl.parent).resolve()
    exists_check = not args.no_exists_check
    task_counts: Dict[str, int] = {}

    rows = read_jsonl(args.jsonl, issues, counters)
    counters.rows = len(rows)
    for line, record in rows:
        before_errors = counters.errors
        task = infer_task(record) if args.task == "auto" else args.task
        task_counts[task] = task_counts.get(task, 0) + 1
        if task == "realtime":
            validate_realtime(record, line, args, base_dir, exists_check, issues, counters)
        else:
            validate_nonrealtime(record, task, line, args, base_dir, exists_check, issues, counters)
        if counters.errors == before_errors:
            counters.valid_rows += 1
        else:
            counters.invalid_rows += 1
    return counters, issues, task_counts


def print_text(path: Path, args: argparse.Namespace, counters: Counters, issues: List[Issue], task_counts: Dict[str, int]) -> None:
    status = "OK" if counters.errors == 0 else "INVALID"
    print(f"{status}: {path}")
    print(
        f"rows={counters.rows} valid_rows={counters.valid_rows} invalid_rows={counters.invalid_rows} "
        f"errors={counters.errors} warnings={counters.warnings} blank_lines={counters.blank_lines}"
    )
    print(f"task_counts={task_counts} mode={args.mode} task_requested={args.task}")
    if not args.no_exists_check:
        print(f"audio_paths_checked={counters.audio_paths_checked} missing_audio_paths={counters.missing_audio_paths}")
    for issue in issues[: max(0, args.max_issues)]:
        print(f"{issue.level.upper()} line={issue.line} row={issue.row_id}: {issue.message}")
    if len(issues) > args.max_issues:
        print(f"... {len(issues) - args.max_issues} more issue(s) omitted")


def print_json(path: Path, args: argparse.Namespace, counters: Counters, issues: List[Issue], task_counts: Dict[str, int]) -> None:
    payload = {
        "path": str(path),
        "valid": counters.errors == 0,
        "mode": args.mode,
        "task_requested": args.task,
        "task_counts": task_counts,
        "summary": asdict(counters),
        "issues": [asdict(issue) for issue in issues[: max(0, args.max_issues)]],
        "issues_truncated": max(0, len(issues) - max(0, args.max_issues)),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def main() -> int:
    args = parse_args()
    if args.expected_n_vq is not None and args.expected_n_vq <= 0:
        print("--expected-n-vq must be positive", file=sys.stderr)
        return 2
    counters, issues, task_counts = validate_rows(args)
    if args.format == "json":
        print_json(args.jsonl, args, counters, issues, task_counts)
    else:
        print_text(args.jsonl, args, counters, issues, task_counts)
    return 1 if counters.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
