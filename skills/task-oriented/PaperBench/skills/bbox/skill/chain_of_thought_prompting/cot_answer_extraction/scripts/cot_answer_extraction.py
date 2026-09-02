#!/usr/bin/env python3
"""Final-answer extraction for chain-of-thought outputs."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from typing import Any


MARKERS = [
    "so the answer is",
    "the answer is",
    "answer:",
    "final answer:",
]


@dataclass
class ExtractionResult:
    raw_text: str
    extracted_answer: str
    normalized_answer: str
    diagnostics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "extracted_answer": self.extracted_answer,
            "normalized_answer": self.normalized_answer,
            "diagnostics": self.diagnostics,
        }


def _strip_answer(text: str) -> str:
    value = text.strip()
    value = re.split(r"[\n\r]", value, maxsplit=1)[0].strip()
    value = re.sub(r"\s+", " ", value)
    value = value.strip(" \t\"'")
    value = value.rstrip(".。!; ")
    return value


def _span_after_marker(text: str) -> tuple[str, str | None]:
    lower = text.lower()
    best = (-1, None)
    for marker in MARKERS:
        idx = lower.rfind(marker)
        if idx > best[0]:
            best = (idx, marker)
    if best[1] is None:
        return "", None
    start = best[0] + len(best[1])
    return _strip_answer(text[start:]), best[1]


def _last_number(text: str) -> str:
    numbers = re.findall(r"-?\$?\d[\d,]*(?:\.\d+)?", text)
    return numbers[-1] if numbers else ""


def normalize_answer(answer: str, task_type: str) -> str:
    value = _strip_answer(answer)
    task_type = task_type.lower()
    if task_type == "numeric":
        number = _last_number(value)
        if not number:
            return ""
        return number.replace("$", "").replace(",", "")
    if task_type == "multiple_choice":
        match = re.search(r"\(([a-e])\)|\b([a-e])\b", value.lower())
        return (match.group(1) or match.group(2)) if match else value.lower()
    if task_type == "yes_no":
        lowered = value.lower()
        if re.search(r"\byes\b", lowered):
            return "yes"
        if re.search(r"\bno\b", lowered):
            return "no"
        return lowered
    if task_type == "date":
        match = re.search(r"\d{1,2}/\d{1,2}/\d{4}", value)
        return match.group(0) if match else value
    if task_type == "plan":
        return re.sub(r"\s+", " ", value.lower()).strip()
    if task_type == "symbolic":
        return re.sub(r"[^a-z0-9]+", "", value.lower())
    raise ValueError(f"unsupported task_type: {task_type}")


def extract_answer(text: str, task_type: str = "numeric") -> ExtractionResult:
    raw = str(text)
    span, marker = _span_after_marker(raw)
    fallback = False
    if not span:
        fallback = True
        if task_type == "numeric":
            span = _last_number(raw)
        else:
            span = _strip_answer(raw.splitlines()[-1] if raw.splitlines() else raw)
    normalized = normalize_answer(span, task_type)
    return ExtractionResult(
        raw_text=raw,
        extracted_answer=span,
        normalized_answer=normalized,
        diagnostics={"marker": marker, "fallback_used": fallback, "task_type": task_type},
    )


def _self_test() -> None:
    text = "5 + 6 = 11. Then 11 - 3 = 8. The answer is 8."
    result = extract_answer(text, "numeric")
    assert result.normalized_answer == "8"
    assert result.diagnostics["fallback_used"] is False
    assert extract_answer("So the answer is (b).", "multiple_choice").normalized_answer == "b"
    assert extract_answer("Thus, it would float. So the answer is no.", "yes_no").normalized_answer == "no"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", default="")
    parser.add_argument("--task-type", default="numeric")
    parser.add_argument("--output", default="")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print(json.dumps({"ok": True}))
        return 0
    result = extract_answer(args.text, args.task_type).to_dict()
    encoded = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(encoded)
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
