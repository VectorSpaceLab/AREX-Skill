#!/usr/bin/env python3
"""Conservative CI gate for Deepchecks result JSON.

Reads one JSON file produced by Deepchecks CheckResult.to_json(...) or
SuiteResult.to_json(...), evaluates visible condition statuses, prints a human
or JSON summary, and exits non-zero on gate failure. The script uses only the
Python standard library, performs no network calls, reads no credentials, and
writes no files by default.

Exit codes:
  0: gate passed
  1: gate failed on valid Deepchecks result JSON
  2: unreadable file, malformed JSON, or unsupported schema
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"
ERROR = "ERROR"
SUPPORTED_CONDITION_STATUSES = {PASS, WARN, FAIL, ERROR}
SUPPORTED_RESULT_TYPES = {"SuiteResult", "CheckResult", "CheckFailure"}


class GateInputError(Exception):
    """Raised when the JSON file cannot be interpreted as Deepchecks result JSON."""


@dataclass
class Issue:
    """One gate issue to display in CI output."""

    severity: str
    result: str
    condition: str
    detail: str


@dataclass
class Summary:
    """Aggregated CI gate summary."""

    source: str
    result_type: str
    result_name: str
    check_results: int = 0
    check_failures: int = 0
    condition_rows: int = 0
    pass_conditions: int = 0
    warn_conditions: int = 0
    fail_conditions: int = 0
    error_conditions: int = 0
    unknown_conditions: int = 0
    results_without_conditions: int = 0
    gate_issues: List[Issue] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.gate_issues


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Apply a conservative CI gate to a Deepchecks CheckResult/SuiteResult JSON file. "
            "By default, WARN conditions fail, CheckFailure/not-run records fail, and artifacts "
            "with no condition rows fail."
        )
    )
    parser.add_argument(
        "result_json",
        help="Path to JSON written by Deepchecks result.to_json(...).",
    )
    parser.add_argument(
        "--allow-warnings",
        action="store_true",
        help="Treat WARN condition statuses as passing. FAIL and ERROR still fail.",
    )
    parser.add_argument(
        "--allow-check-failures",
        action="store_true",
        help="Do not fail the gate on CheckFailure/not-run records. They are still reported.",
    )
    parser.add_argument(
        "--allow-no-conditions",
        action="store_true",
        help="Allow an artifact with zero condition rows to pass if no other issue is found.",
    )
    parser.add_argument(
        "--emit-json-summary",
        action="store_true",
        help="Print the gate summary as JSON instead of human-readable text.",
    )
    parser.add_argument(
        "--max-issues",
        type=int,
        default=20,
        help="Maximum number of detailed issues to print in human-readable output (default: 20).",
    )
    return parser.parse_args(argv)


def load_result_json(path: Path) -> Dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise GateInputError(f"Could not read {path}: {exc}") from exc

    if not text.strip():
        raise GateInputError(f"{path} is empty; expected Deepchecks result JSON.")

    try:
        payload: Any = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GateInputError(
            f"Malformed JSON in {path} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

    # Some pipelines accidentally JSON-encode the JSON string a second time.
    if isinstance(payload, str):
        nested = payload.strip()
        if nested.startswith("{") or nested.startswith("["):
            try:
                payload = json.loads(nested)
            except json.JSONDecodeError as exc:
                raise GateInputError(
                    "The file contains a quoted JSON string, but nested decoding failed "
                    f"at line {exc.lineno}, column {exc.colno}: {exc.msg}"
                ) from exc

    if not isinstance(payload, dict):
        raise GateInputError(
            f"Expected a top-level JSON object produced by Deepchecks to_json(...); got {type(payload).__name__}."
        )
    return payload


def top_level_type(payload: Dict[str, Any]) -> str:
    result_type = payload.get("type")
    if result_type is None:
        if isinstance(payload.get("results"), list):
            result_type = "SuiteResult"
        elif "conditions_results" in payload:
            result_type = "CheckResult"
        elif "exception" in payload:
            result_type = "CheckFailure"
        else:
            raise GateInputError(
                "Missing result 'type'. Expected one of SuiteResult, CheckResult, or CheckFailure."
            )
    if not isinstance(result_type, str):
        raise GateInputError(f"Result 'type' must be a string; got {type(result_type).__name__}.")
    if result_type not in SUPPORTED_RESULT_TYPES:
        raise GateInputError(
            f"Unsupported result type {result_type!r}; expected one of {sorted(SUPPORTED_RESULT_TYPES)}."
        )
    return result_type


def result_name(record: Dict[str, Any], fallback: str) -> str:
    header = record.get("header")
    if isinstance(header, str) and header:
        return header
    name = record.get("name")
    if isinstance(name, str) and name:
        return name
    check = record.get("check")
    if isinstance(check, dict):
        check_name = check.get("name")
        if isinstance(check_name, str) and check_name:
            return check_name
    return fallback


def iter_result_records(payload: Dict[str, Any]) -> Iterable[Tuple[str, Dict[str, Any]]]:
    result_type = top_level_type(payload)
    if result_type == "SuiteResult":
        results = payload.get("results")
        if not isinstance(results, list):
            raise GateInputError("SuiteResult JSON must contain a list field named 'results'.")
        for index, record in enumerate(results):
            if not isinstance(record, dict):
                raise GateInputError(
                    f"SuiteResult results[{index}] must be an object; got {type(record).__name__}."
                )
            yield f"results[{index}]", record
    else:
        yield "$", payload


def status_from_condition(condition: Dict[str, Any], location: str) -> str:
    raw = condition.get("Status")
    if not isinstance(raw, str):
        raise GateInputError(f"{location} condition row is missing string field 'Status'.")
    status = raw.strip().upper()
    if status not in SUPPORTED_CONDITION_STATUSES:
        raise GateInputError(
            f"{location} has unsupported condition Status {raw!r}; expected PASS, WARN, FAIL, or ERROR."
        )
    return status


def analyze(payload: Dict[str, Any], args: argparse.Namespace, source: str) -> Summary:
    payload_type = top_level_type(payload)
    summary = Summary(
        source=source,
        result_type=payload_type,
        result_name=result_name(payload, fallback=payload_type),
    )

    for location, record in iter_result_records(payload):
        record_type = record.get("type")
        if record_type is None:
            if "conditions_results" in record:
                record_type = "CheckResult"
            elif "exception" in record:
                record_type = "CheckFailure"
            else:
                raise GateInputError(f"{location} is missing result 'type'.")
        if not isinstance(record_type, str):
            raise GateInputError(f"{location} result 'type' must be a string.")
        if record_type not in {"CheckResult", "CheckFailure"}:
            raise GateInputError(
                f"{location} has unsupported nested result type {record_type!r}; "
                "expected CheckResult or CheckFailure."
            )

        name = result_name(record, fallback=location)
        if record_type == "CheckFailure":
            summary.check_failures += 1
            exception = record.get("exception")
            detail = str(exception) if exception is not None else "Check did not run; no exception text provided."
            if args.allow_check_failures:
                summary.notes.append(f"Allowed CheckFailure/not-run record: {name}: {detail}")
            else:
                summary.gate_issues.append(Issue("CHECK_NOT_RUN", name, "", detail))
            continue

        summary.check_results += 1
        conditions = record.get("conditions_results")
        if conditions is None:
            conditions = []
        if not isinstance(conditions, list):
            raise GateInputError(f"{location} conditions_results must be a list when present.")
        if not conditions:
            summary.results_without_conditions += 1
            continue

        for condition_index, condition in enumerate(conditions):
            if not isinstance(condition, dict):
                raise GateInputError(
                    f"{location} conditions_results[{condition_index}] must be an object."
                )
            status = status_from_condition(condition, f"{location} conditions_results[{condition_index}]")
            condition_name = str(condition.get("Condition") or f"condition[{condition_index}]")
            detail = str(condition.get("More Info") or "")
            summary.condition_rows += 1

            if status == PASS:
                summary.pass_conditions += 1
            elif status == WARN:
                summary.warn_conditions += 1
                if not args.allow_warnings:
                    summary.gate_issues.append(Issue(WARN, name, condition_name, detail))
            elif status == FAIL:
                summary.fail_conditions += 1
                summary.gate_issues.append(Issue(FAIL, name, condition_name, detail))
            elif status == ERROR:
                summary.error_conditions += 1
                summary.gate_issues.append(Issue(ERROR, name, condition_name, detail))
            else:  # Defensive; status_from_condition rejects this branch.
                summary.unknown_conditions += 1
                summary.gate_issues.append(Issue("UNKNOWN", name, condition_name, detail))

    if summary.condition_rows == 0:
        message = (
            "No condition rows were found. Deepchecks results without configured conditions are useful reports, "
            "but they are not an explicit CI pass/fail gate."
        )
        if args.allow_no_conditions:
            summary.notes.append(message)
        else:
            summary.gate_issues.append(Issue("NO_CONDITIONS", summary.result_name, "", message))

    return summary


def summary_payload(summary: Summary) -> Dict[str, Any]:
    payload = asdict(summary)
    payload["passed"] = summary.passed
    return payload


def print_human_summary(summary: Summary, max_issues: int) -> None:
    status = "PASS" if summary.passed else "FAIL"
    print(f"{status}: Deepchecks JSON CI gate for {summary.source}")
    print(
        "Summary: "
        f"type={summary.result_type}, "
        f"checks={summary.check_results}, "
        f"check_failures={summary.check_failures}, "
        f"conditions={summary.condition_rows}, "
        f"PASS={summary.pass_conditions}, WARN={summary.warn_conditions}, "
        f"FAIL={summary.fail_conditions}, ERROR={summary.error_conditions}, "
        f"without_conditions={summary.results_without_conditions}"
    )

    if summary.notes:
        print("Notes:")
        for note in summary.notes[:max_issues]:
            print(f"  - {note}")
        if len(summary.notes) > max_issues:
            print(f"  - ... {len(summary.notes) - max_issues} more notes omitted")

    if summary.gate_issues:
        print("Gate issues:")
        for issue in summary.gate_issues[:max_issues]:
            location = issue.result
            condition = f" / {issue.condition}" if issue.condition else ""
            detail = f": {issue.detail}" if issue.detail else ""
            print(f"  - [{issue.severity}] {location}{condition}{detail}")
        if len(summary.gate_issues) > max_issues:
            print(f"  - ... {len(summary.gate_issues) - max_issues} more issues omitted")


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if args.max_issues < 1:
        print("ERROR: --max-issues must be at least 1", file=sys.stderr)
        return 2

    path = Path(args.result_json)
    try:
        payload = load_result_json(path)
        summary = analyze(payload, args, str(path))
    except GateInputError as exc:
        if args.emit_json_summary:
            print(json.dumps({"passed": False, "error": str(exc), "exit_code": 2}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.emit_json_summary:
        print(json.dumps(summary_payload(summary), indent=2, sort_keys=True))
    else:
        print_human_summary(summary, args.max_issues)

    return 0 if summary.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
