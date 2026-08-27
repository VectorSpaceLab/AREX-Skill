#!/usr/bin/env python3
"""Validate a Gherkin feature file and print the corresponding lavague-qa command.

This probe is file-only: it does not launch a browser, call an LLM, or write
any generated tests.
"""

from __future__ import annotations

import argparse
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


STEP_RE = re.compile(r"^\s*(Given|When|Then|And|But)\b(.*)$", re.IGNORECASE)
FEATURE_RE = re.compile(r"^\s*Feature:\s*(.+?)\s*$", re.IGNORECASE)
SCENARIO_RE = re.compile(r"^\s*Scenario(?: Outline)?:\s*(.+?)\s*$", re.IGNORECASE)


@dataclass
class ScenarioSummary:
    name: str
    contexts: int
    actions: int
    outcomes: int


@dataclass
class FeatureSummary:
    feature_name: str
    scenarios: List[ScenarioSummary]
    raw_steps: int
    line_based: bool


class ValidationError(Exception):
    pass


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def _line_based_summary(text: str) -> FeatureSummary:
    feature_name = ""
    scenarios: List[ScenarioSummary] = []
    current: Optional[ScenarioSummary] = None
    last_kind: Optional[str] = None
    raw_steps = 0

    for line in text.splitlines():
        if not feature_name:
            m = FEATURE_RE.match(line)
            if m:
                feature_name = m.group(1).strip()
        scenario_match = SCENARIO_RE.match(line)
        if scenario_match:
            current = ScenarioSummary(
                name=scenario_match.group(1).strip(), contexts=0, actions=0, outcomes=0
            )
            scenarios.append(current)
            last_kind = None
            continue

        step_match = STEP_RE.match(line)
        if step_match and current is not None:
            raw_steps += 1
            keyword = step_match.group(1).title()
            if keyword in {"And", "But"}:
                keyword = last_kind or ""
            else:
                last_kind = keyword
            if keyword == "Given":
                current.contexts += 1
            elif keyword == "When":
                current.actions += 1
            elif keyword == "Then":
                current.outcomes += 1

    return FeatureSummary(feature_name=feature_name, scenarios=scenarios, raw_steps=raw_steps, line_based=True)


def _gherkin_summary(text: str) -> Optional[FeatureSummary]:
    try:
        from gherkin.parser import Parser
    except Exception:
        return None

    try:
        parsed = Parser().parse(text)
    except Exception as exc:
        raise ValidationError(f"Gherkin parse error: {exc}") from exc

    feature = parsed.get("feature") or {}
    feature_name = (feature.get("name") or "").strip()
    scenarios: List[ScenarioSummary] = []
    raw_steps = 0

    for child in feature.get("children", []):
        scenario = child.get("scenario") or {}
        name = (scenario.get("name") or "").strip()
        contexts = actions = outcomes = 0
        last_keyword: Optional[str] = None
        for step in scenario.get("steps", []):
            raw_steps += 1
            keyword = (step.get("keywordType") or "").strip()
            if keyword == "Conjunction":
                keyword = last_keyword or ""
            else:
                last_keyword = keyword
            if keyword == "Context":
                contexts += 1
            elif keyword == "Action":
                actions += 1
            elif keyword == "Outcome":
                outcomes += 1
        scenarios.append(ScenarioSummary(name=name, contexts=contexts, actions=actions, outcomes=outcomes))

    return FeatureSummary(feature_name=feature_name, scenarios=scenarios, raw_steps=raw_steps, line_based=False)


def _summarize_feature(path: Path) -> FeatureSummary:
    text = _read_text(path)
    if not text.strip():
        raise ValidationError(f"Feature file is empty: {path}")

    summary = _gherkin_summary(text)
    if summary is None:
        summary = _line_based_summary(text)

    if not summary.feature_name:
        raise ValidationError("Missing `Feature:` header")
    if not summary.scenarios:
        raise ValidationError("Missing `Scenario:` block")

    first = summary.scenarios[0]
    if first.actions == 0:
        raise ValidationError("The first scenario has no `When`/`And` action steps")
    if first.outcomes == 0:
        raise ValidationError("The first scenario has no `Then` outcome step")

    return summary


def _format_command(args: argparse.Namespace) -> str:
    pieces = ["lavague-qa", "--url", args.url, "--feature", str(args.feature)]
    if args.full_llm:
        pieces.append("--full-llm")
    if args.context:
        pieces.extend(["--context", args.context])
    if args.headless:
        pieces.append("--headless")
    if args.log_to_db:
        pieces.append("--log-to-db")
    return " ".join(shlex.quote(piece) for piece in pieces)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a Gherkin feature and print the matching lavague-qa command."
    )
    parser.add_argument("--url", required=True, help="Target site URL")
    parser.add_argument("--feature", required=True, type=Path, help="Path to a .feature file")
    parser.add_argument("--full-llm", action="store_true", help="Include --full-llm in the printed command")
    parser.add_argument("--context", help="Optional context Python file to include in the printed command")
    parser.add_argument("--headless", action="store_true", help="Include --headless in the printed command")
    parser.add_argument("--log-to-db", action="store_true", help="Include --log-to-db in the printed command")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    feature_path = args.feature.expanduser()
    if not feature_path.exists():
        raise ValidationError(f"Feature file not found: {feature_path}")
    if feature_path.suffix != ".feature":
        print(f"Warning: expected a .feature file, got {feature_path.name}", file=sys.stderr)

    summary = _summarize_feature(feature_path)

    stem = feature_path.stem
    generated_name = f"{stem}_llm.py" if args.full_llm else f"{stem}.py"
    print(f"Feature: {summary.feature_name or feature_path.name}")
    print(f"Scenarios: {len(summary.scenarios)} (using the first scenario: {summary.scenarios[0].name})")
    print(
        f"First scenario steps: {summary.scenarios[0].contexts} context, "
        f"{summary.scenarios[0].actions} action, {summary.scenarios[0].outcomes} outcome"
    )
    if len(summary.scenarios) > 1:
        print("Warning: lavague-qa generation uses the first scenario only.", file=sys.stderr)
    print(f"Expected output: generated_tests/{feature_path.name} + generated_tests/{generated_name}")
    print(_format_command(args))
    print("No browser or LLM was launched by this probe.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)
