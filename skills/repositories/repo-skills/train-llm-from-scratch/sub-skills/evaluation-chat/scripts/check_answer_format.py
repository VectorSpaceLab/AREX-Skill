#!/usr/bin/env python3
"""Inspect GSM8K-style answer extraction and verifier-shaped reward behavior.

This is a standalone parser helper: no model loading, no torch import, no dataset
access. It mirrors the repo parser's priority: <answer> tag, then ####, then
last number in the text.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ANSWER_OPEN = "<answer>"
ANSWER_CLOSE = "</answer>"
NUMBER_RE = re.compile(r"-?\$?\d[\d,]*(?:\.\d+)?")
ANSWER_RE = re.compile(re.escape(ANSWER_OPEN) + r"(.*?)" + re.escape(ANSWER_CLOSE), re.DOTALL)
HASH_RE = re.compile(r"####\s*(-?\$?\d[\d,]*(?:\.\d+)?)")
FLOAT_TOL = 1e-4


@dataclass
class ParseResult:
    method: str
    parsed_answer: float | None
    tag_count: int
    well_formed_single_answer_tag: bool
    gold: float | None = None
    correct: bool | None = None
    estimated_reward: float | None = None
    note: str = ""


def parse_number(s: str | None) -> float | None:
    if s is None:
        return None
    m = NUMBER_RE.search(s)
    if not m:
        return None
    raw = m.group(0).replace(",", "").replace("$", "")
    try:
        return float(raw)
    except ValueError:
        return None


def extract_answer(text: str) -> tuple[str, float | None]:
    m = ANSWER_RE.search(text)
    if m:
        n = parse_number(m.group(1))
        if n is not None:
            return "answer_tag", n
    m = HASH_RE.search(text)
    if m:
        n = parse_number(m.group(1))
        if n is not None:
            return "hash", n
    nums = NUMBER_RE.findall(text)
    if nums:
        return "last_number", parse_number(nums[-1])
    return "none", None


def analyze(text: str, gold: float | None = None) -> ParseResult:
    method, answer = extract_answer(text)
    tag_count = len(ANSWER_RE.findall(text))
    well_formed = tag_count == 1
    correct = None
    reward = None
    if gold is not None:
        correct = answer is not None and math.isclose(answer, gold, rel_tol=0.0, abs_tol=FLOAT_TOL)
        reward = (1.0 if correct else 0.0) + (0.2 if well_formed else 0.0)
        reward = min(reward, 1.2)
    notes = {
        "answer_tag": "Parsed the first numeric value inside <answer>...</answer>.",
        "hash": "No parseable answer tag won; parsed the GSM8K #### number.",
        "last_number": "No parseable tag or #### answer won; parsed the last number in the text.",
        "none": "No numeric answer could be parsed.",
    }
    return ParseResult(
        method=method,
        parsed_answer=answer,
        tag_count=tag_count,
        well_formed_single_answer_tag=well_formed,
        gold=gold,
        correct=correct,
        estimated_reward=reward,
        note=notes[method],
    )


def read_text(args: argparse.Namespace) -> str:
    sources = [args.text is not None, args.file is not None]
    if sum(sources) > 1:
        raise SystemExit("choose only one input source: --text, file, or stdin")
    if args.text is not None:
        return args.text
    if args.file is not None:
        return Path(args.file).read_text(encoding="utf-8")
    return sys.stdin.read()


def print_human(result: ParseResult) -> None:
    print(f"method: {result.method}")
    print(f"parsed_answer: {result.parsed_answer}")
    print(f"answer_tag_count: {result.tag_count}")
    print(f"well_formed_single_answer_tag: {result.well_formed_single_answer_tag}")
    if result.gold is not None:
        print(f"gold: {result.gold}")
        print(f"correct: {result.correct}")
        print(f"estimated_reward: {result.estimated_reward}")
    print(f"note: {result.note}")
    print("reward_rule: +1.0 correct numeric match, +0.2 exactly one answer tag, clipped at 1.2")


def run_self_test() -> int:
    cases = [
        ("<think>13+29</think><answer>42</answer>", 42.0, "answer_tag", 42.0, True, 1.2),
        ("reasoning #### 18", 18.0, "hash", 18.0, True, 1.0),
        ("first 5 then final 7", 7.0, "last_number", 7.0, True, 1.0),
        ("<answer></answer> fallback #### 9", 9.0, "hash", 9.0, True, 1.2),
        ("<answer>1</answer><answer>2</answer>", 1.0, "answer_tag", 1.0, True, 1.0),
        ("no digits here", None, "none", None, None, None),
    ]
    for text, gold, method, parsed, correct, reward in cases:
        res = analyze(text, gold)
        assert res.method == method, (text, res.method, method)
        assert res.parsed_answer == parsed, (text, res.parsed_answer, parsed)
        assert res.correct == correct, (text, res.correct, correct)
        assert res.estimated_reward == reward, (text, res.estimated_reward, reward)
    print("self-test passed: parser priority and reward estimate match expected tiny fixtures")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Parse a model answer using <answer>, ####, then last-number fallback; optionally compare gold."
    )
    p.add_argument("file", nargs="?", help="text file to inspect; omit to read stdin unless --text is supplied")
    p.add_argument("--text", help="text to inspect directly")
    p.add_argument("--gold", type=float, help="optional numeric gold answer for correctness/reward estimate")
    p.add_argument("--json", action="store_true", help="emit JSON instead of human-readable lines")
    p.add_argument("--self-test", action="store_true", help="run tiny built-in parser fixtures and exit")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test()
    text = read_text(args)
    result = analyze(text, args.gold)
    if args.json:
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
    else:
        print_human(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
