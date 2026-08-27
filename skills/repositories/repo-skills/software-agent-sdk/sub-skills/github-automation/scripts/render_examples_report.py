#!/usr/bin/env python3
"""Render a markdown summary for example-run results."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path


@dataclass(slots=True)
class ExampleResult:
    name: str
    status: str
    duration_seconds: float | None
    cost: str | None
    failure_reason: str | None


def _coerce_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except Exception:
        return None


def _coerce_cost(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def load_results(results_dir: Path) -> list[ExampleResult]:
    results: list[ExampleResult] = []
    for path in sorted(results_dir.glob("*.json")):
        payload = json.loads(path.read_text())
        results.append(
            ExampleResult(
                name=str(payload.get("example", path.stem)),
                status=str(payload.get("status", "unknown")),
                duration_seconds=_coerce_float(payload.get("duration_seconds")),
                cost=_coerce_cost(payload.get("cost")),
                failure_reason=_coerce_cost(payload.get("failure_reason")),
            )
        )
    return results


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "--"
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, sec = divmod(int(seconds + 0.5), 60)
    if minutes < 60:
        return f"{minutes}m {sec}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m"


def format_cost(value: str | None) -> str:
    if not value:
        return "--"
    try:
        amount = Decimal(value)
    except InvalidOperation:
        return "--"
    return f"${amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"


def build_report(
    results: list[ExampleResult],
    model: str,
    workflow_url: str,
    timestamp: str,
) -> str:
    ts = timestamp or datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        f"## 🔄 Running Examples with `{model}`",
        "",
        f"_Generated: {ts}_",
        "",
        "| Example | Status | Duration | Cost |",
        "|---------|--------|----------|------|",
    ]
    for result in results:
        status = "✅ PASS" if result.status == "passed" else "❌ FAIL"
        if result.status != "passed" and result.failure_reason:
            escaped_reason = result.failure_reason.replace("|", "\\|").replace(
                "\n", "<br>"
            )
            status = f"{status}<br>{escaped_reason}"
        example = result.name.replace("|", "\\|").replace("\n", "<br>")
        duration = format_duration(result.duration_seconds)
        cost = format_cost(result.cost)
        lines.append(f"| {example} | {status} | {duration} | {cost} |")
    if not results:
        lines.append("| _No results_ | -- | -- | -- |")
    passed = sum(1 for item in results if item.status == "passed")
    failed = len(results) - passed
    if failed == 0 and results:
        summary = "✅ All tests passed!"
    elif not results:
        summary = "ℹ️ No examples were executed"
    else:
        summary = "❌ Some tests failed"
    lines.extend(
        [
            "",
            "---",
            "",
            f"### {summary}",
            f"**Total:** {len(results)} | **Passed:** {passed} | **Failed:** {failed}",
        ]
    )
    if workflow_url:
        lines.extend(["", f"[View full workflow run]({workflow_url})"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--model", default="Unknown model")
    parser.add_argument("--workflow-url", default="")
    parser.add_argument("--timestamp", default="")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    report = build_report(
        load_results(args.results_dir),
        args.model,
        args.workflow_url,
        args.timestamp,
    )
    if args.output is not None:
        args.output.write_text(report)
    print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
