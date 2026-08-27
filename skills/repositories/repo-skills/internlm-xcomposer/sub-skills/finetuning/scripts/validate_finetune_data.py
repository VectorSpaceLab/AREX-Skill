#!/usr/bin/env python3
"""Validate InternLM-XComposer finetuning JSON/data.txt manifests safely.

This helper is intentionally stdlib-only. It parses JSON and text manifests,
checks schema and family-specific placeholder rules, and optionally checks path
existence. It never imports torch, PIL, transformers, deepspeed, or peft.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence, Tuple, Union


PLACEHOLDER = "<ImageHere>"
KNOWN_ROLES = {"human", "user", "bot", "assistant"}
HUMAN_ROLES = {"human", "user"}
MANIFEST_LINE_RE = re.compile(r"^\S+(?: \S+)?$")


@dataclass
class Issue:
    severity: str
    location: str
    message: str


@dataclass
class FileReport:
    path: str
    samples: int = 0
    text_samples: int = 0
    single_image_samples: int = 0
    multi_image_samples: int = 0
    manifest_target: Optional[int] = None
    manifest_value: Optional[str] = None
    issues: List[Issue] = field(default_factory=list)

    @property
    def errors(self) -> List[Issue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> List[Issue]:
        return [issue for issue in self.issues if issue.severity == "warning"]


@dataclass
class ValidationReport:
    family: str
    given_num_mode: bool
    check_paths: bool
    files: List[FileReport] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)

    @property
    def all_issues(self) -> List[Issue]:
        found = list(self.issues)
        for file_report in self.files:
            found.extend(file_report.issues)
        return found

    @property
    def errors(self) -> List[Issue]:
        return [issue for issue in self.all_issues if issue.severity == "error"]

    @property
    def warnings(self) -> List[Issue]:
        return [issue for issue in self.all_issues if issue.severity == "warning"]


def add_issue(target: Union[FileReport, ValidationReport], severity: str, location: str, message: str) -> None:
    target.issues.append(Issue(severity=severity, location=location, message=message))


class JsonLoadError(RuntimeError):
    pass


def _read_json_list(path: Path) -> List[Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception as exc:  # noqa: BLE001 - produce CLI-friendly error
        raise JsonLoadError(f"could not read JSON: {exc}") from exc
    if not isinstance(payload, list):
        raise JsonLoadError("top-level JSON value must be a list")
    return payload


def _normalize_image_field(value: Any) -> Tuple[int, List[str], Optional[str]]:
    if isinstance(value, str):
        if not value:
            return 0, [], "image path string is empty"
        return 1, [value], None
    if isinstance(value, list):
        if not value:
            return 0, [], "image list is empty"
        paths: List[str] = []
        for index, item in enumerate(value):
            if not isinstance(item, str) or not item:
                return 0, [], f"image list item {index} is not a non-empty string"
            paths.append(item)
        return len(paths), paths, None
    return 0, [], "image must be a string or a list of strings"


def _count_placeholders(turns: Iterable[dict]) -> Tuple[int, int]:
    total = 0
    assistant_side = 0
    for turn in turns:
        value = turn.get("value")
        if not isinstance(value, str):
            continue
        count = value.count(PLACEHOLDER)
        total += count
        role = str(turn.get("from", "")).lower()
        if role not in HUMAN_ROLES:
            assistant_side += count
    return total, assistant_side


def _check_placeholder_policy(
    report: FileReport,
    *,
    family: str,
    location: str,
    image_count: int,
    placeholder_count: int,
    assistant_placeholders: int,
) -> None:
    if assistant_placeholders:
        add_issue(
            report,
            "warning",
            location,
            f"{assistant_placeholders} placeholder token(s) appear outside human/user turns",
        )

    if family == "2.5":
        if image_count == 0 and placeholder_count:
            add_issue(report, "warning", location, "text-only sample contains <ImageHere> tokens")
        elif image_count == 1 and placeholder_count > 1:
            add_issue(report, "error", location, "2.5 single-image sample should not contain multiple <ImageHere> tokens")
        elif image_count > 1 and placeholder_count != image_count:
            add_issue(
                report,
                "error",
                location,
                f"2.5 multi-image sample has {image_count} images but {placeholder_count} <ImageHere> token(s)",
            )
    elif family == "2.0":
        if image_count == 0 and placeholder_count:
            add_issue(report, "warning", location, "text-only sample contains <ImageHere> tokens")
        elif image_count > 0 and placeholder_count != image_count:
            add_issue(
                report,
                "error",
                location,
                f"2.0 image sample should have one <ImageHere> per image ({image_count} expected, {placeholder_count} found)",
            )
    elif family == "1.0":
        if placeholder_count:
            add_issue(
                report,
                "warning",
                location,
                "1.0 finetuning examples are placeholder-free; confirm custom legacy trainer before using <ImageHere>",
            )


def _validate_turns(report: FileReport, sample: dict, location: str) -> List[dict]:
    if "conversations" not in sample:
        if "conversation" in sample:
            add_issue(report, "error", location, "use 'conversations' plural; the loader does not read 'conversation'")
        else:
            add_issue(report, "error", location, "missing required key: conversations")
        return []
    turns = sample["conversations"]
    if not isinstance(turns, list) or not turns:
        add_issue(report, "error", location, "conversations must be a non-empty list")
        return []
    valid_turns: List[dict] = []
    for turn_index, turn in enumerate(turns):
        turn_loc = f"{location}.conversations[{turn_index}]"
        if not isinstance(turn, dict):
            add_issue(report, "error", turn_loc, "turn must be an object")
            continue
        role = turn.get("from")
        value = turn.get("value")
        if not isinstance(role, str) or not role:
            add_issue(report, "error", turn_loc, "turn 'from' must be a non-empty string")
        elif role.lower() not in KNOWN_ROLES:
            add_issue(report, "warning", turn_loc, f"unusual role {role!r}; loader treats non-human/user as assistant")
        if not isinstance(value, str) or not value:
            add_issue(report, "error", turn_loc, "turn 'value' must be a non-empty string")
        valid_turns.append(turn)
    return valid_turns


def _check_image_paths(report: FileReport, image_paths: Sequence[str], base_dir: Path, location: str) -> None:
    for item in image_paths:
        candidate = Path(item).expanduser()
        if not candidate.is_absolute():
            candidate = base_dir / candidate
        if not candidate.exists():
            add_issue(report, "error", location, f"image/video path does not exist: {item}")


def validate_json_file(
    path: Path,
    *,
    family: str,
    base_dir: Path,
    check_paths: bool,
    manifest_value: Optional[str] = None,
    manifest_target: Optional[int] = None,
) -> FileReport:
    report = FileReport(
        path=str(path),
        manifest_value=manifest_value,
        manifest_target=manifest_target,
    )
    try:
        payload = _read_json_list(path)
    except JsonLoadError as exc:
        add_issue(report, "error", str(path), str(exc))
        return report

    report.samples = len(payload)
    if not payload:
        add_issue(report, "error", str(path), "JSON list is empty")
        return report

    first_kind: Optional[str] = None
    for sample_index, sample in enumerate(payload):
        location = f"{path.name}[{sample_index}]"
        if not isinstance(sample, dict):
            add_issue(report, "error", location, "sample must be an object")
            continue
        if "id" not in sample:
            add_issue(report, "warning", location, "missing id; loader can run, but traceability is poor")

        turns = _validate_turns(report, sample, location)
        image_count = 0
        image_paths: List[str] = []
        if "image" in sample:
            image_count, image_paths, image_error = _normalize_image_field(sample["image"])
            if image_error:
                add_issue(report, "error", location, image_error)
            elif check_paths:
                _check_image_paths(report, image_paths, base_dir, location)

        kind = "image" if image_count > 0 else "text"
        if first_kind is None:
            first_kind = kind
        elif kind != first_kind:
            add_issue(
                report,
                "error",
                location,
                f"mixed JSON file: first sample is {first_kind}, but this sample is {kind}",
            )

        if image_count == 0:
            report.text_samples += 1
        elif image_count == 1:
            report.single_image_samples += 1
        else:
            report.multi_image_samples += 1

        placeholder_count, assistant_placeholders = _count_placeholders(turns)
        _check_placeholder_policy(
            report,
            family=family,
            location=location,
            image_count=image_count,
            placeholder_count=placeholder_count,
            assistant_placeholders=assistant_placeholders,
        )
    return report


def _resolve_path(token: str, base_dir: Path) -> Path:
    candidate = Path(token).expanduser()
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    return candidate


def _target_from_value(value: Optional[str], sample_count: int, given_num_mode: bool) -> Optional[int]:
    if value is None:
        return None
    numeric = float(value)
    if given_num_mode:
        return int(numeric * 1000)
    return int(sample_count * numeric)


def validate_manifest(path: Path, *, args: argparse.Namespace, report: ValidationReport) -> None:
    manifest_base = Path(args.base_dir).expanduser() if args.base_dir else path.parent
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:  # noqa: BLE001 - CLI-friendly
        add_issue(report, "error", str(path), f"could not read manifest: {exc}")
        return

    if not lines:
        add_issue(report, "error", str(path), "manifest is empty")
        return

    for line_number, raw_line in enumerate(lines, 1):
        stripped = raw_line.strip()
        location = f"{path.name}:{line_number}"
        if not stripped:
            add_issue(report, "error", location, "blank lines are not supported by the source loader")
            continue
        if stripped.startswith("#"):
            add_issue(report, "error", location, "comment lines are not supported by the source loader")
            continue
        if not MANIFEST_LINE_RE.fullmatch(stripped):
            add_issue(report, "error", location, "expected one path token plus optional numeric token separated by one space")
            continue
        parts = stripped.split(" ")
        data_path = _resolve_path(parts[0], manifest_base)
        manifest_value = parts[1] if len(parts) == 2 else None
        if data_path.suffix.lower() != ".json":
            add_issue(report, "error", location, f"manifest entry should point to a .json file: {parts[0]}")
            continue
        if not data_path.exists():
            add_issue(report, "error", location, f"JSON file does not exist: {parts[0]}")
            continue
        file_report = validate_json_file(
            data_path,
            family=args.family,
            base_dir=manifest_base,
            check_paths=args.check_paths,
            manifest_value=manifest_value,
            manifest_target=None,
        )
        if manifest_value is not None:
            try:
                file_report.manifest_target = _target_from_value(
                    manifest_value,
                    file_report.samples,
                    not args.ratio_mode,
                )
            except ValueError:
                add_issue(file_report, "error", location, f"manifest sampling value is not numeric: {manifest_value!r}")
        report.files.append(file_report)


def validate_path(input_path: Path, *, args: argparse.Namespace, report: ValidationReport) -> None:
    if not input_path.exists():
        add_issue(report, "error", str(input_path), "input path does not exist")
        return
    if input_path.suffix.lower() == ".json":
        base_dir = Path(args.base_dir).expanduser() if args.base_dir else Path.cwd()
        report.files.append(
            validate_json_file(
                input_path,
                family=args.family,
                base_dir=base_dir,
                check_paths=args.check_paths,
            )
        )
    else:
        validate_manifest(input_path, args=args, report=report)


def render_text(report: ValidationReport, *, strict: bool) -> str:
    lines: List[str] = []
    mode = "given_num" if report.given_num_mode else "ratio"
    lines.append(f"family={report.family} manifest_mode={mode} check_paths={report.check_paths}")
    total_samples = sum(item.samples for item in report.files)
    lines.append(f"files={len(report.files)} samples={total_samples}")
    for item in report.files:
        target = f", target={item.manifest_target}" if item.manifest_target is not None else ""
        lines.append(
            f"- {item.path}: samples={item.samples}, text={item.text_samples}, "
            f"single_image={item.single_image_samples}, multi_image={item.multi_image_samples}{target}"
        )

    issues = report.all_issues
    if issues:
        lines.append("")
        lines.append("Issues:")
        for issue in issues:
            severity = "error" if strict and issue.severity == "warning" else issue.severity
            lines.append(f"- {severity.upper()} {issue.location}: {issue.message}")
    else:
        lines.append("")
        lines.append("No issues found.")
    return "\n".join(lines)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate InternLM-XComposer finetuning data files safely.")
    parser.add_argument("paths", nargs="+", help="JSON file(s) or data.txt manifest(s) to validate.")
    parser.add_argument("--family", choices=["2.5", "2.0", "1.0"], default="2.5", help="Placeholder policy to apply.")
    parser.add_argument("--ratio-mode", action="store_true", help="Interpret manifest numbers as ratios instead of thousands of samples.")
    parser.add_argument("--check-paths", action="store_true", help="Check referenced image/video path existence.")
    parser.add_argument("--base-dir", help="Base directory for relative manifest and image/video paths.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors for the exit code and text rendering.")
    parser.add_argument("--json-output", action="store_true", help="Emit a JSON report instead of human-readable text.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = ValidationReport(
        family=args.family,
        given_num_mode=not args.ratio_mode,
        check_paths=args.check_paths,
    )
    for raw_path in args.paths:
        validate_path(Path(raw_path).expanduser(), args=args, report=report)

    if args.json_output:
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    else:
        print(render_text(report, strict=args.strict))

    if report.errors or (args.strict and report.warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
