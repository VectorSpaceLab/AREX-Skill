#!/usr/bin/env python3
"""Deterministic GSM8K answer extraction and calculator validation."""

from __future__ import annotations

import argparse
import ast
import json
import math
import operator
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path


ANSWER_RE = re.compile(r"####\s*([-+]?[0-9][0-9,]*(?:\.[0-9]+)?)")
ANNOTATION_RE = re.compile(r"<<([^<>=]+)=([^<>]+)>>")
INVALID_ANSWER = "[invalid]"

ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
ALLOWED_UNARY = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def canonicalize_answer(value: object) -> str:
    text = str(value).strip().replace(",", "")
    if not text:
        return INVALID_ANSWER
    try:
        number = Decimal(text)
    except InvalidOperation:
        return text
    if number == number.to_integral_value():
        return str(number.quantize(Decimal(1)))
    normalized = format(number.normalize(), "f")
    return normalized.rstrip("0").rstrip(".") if "." in normalized else normalized


def extract_answer(text: str) -> str:
    match = ANSWER_RE.search(text or "")
    if not match:
        return INVALID_ANSWER
    return canonicalize_answer(match.group(1))


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_BINOPS:
        return ALLOWED_BINOPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_UNARY:
        return ALLOWED_UNARY[type(node.op)](_eval_node(node.operand))
    raise ValueError(f"unsupported expression node: {type(node).__name__}")


def safe_eval_arithmetic(expression: str) -> float:
    compact = expression.strip().replace(",", "")
    if not compact or any(ch not in "0123456789+-*/.() " for ch in compact):
        raise ValueError("expression contains unsupported characters")
    parsed = ast.parse(compact, mode="eval")
    return _eval_node(parsed)


def validate_calculator_annotations(text: str, tolerance: float = 1e-9) -> list[dict]:
    records = []
    for match in ANNOTATION_RE.finditer(text or ""):
        expression = match.group(1).strip()
        stated = match.group(2).strip().replace(",", "")
        record = {
            "annotation": match.group(0),
            "expression": expression,
            "stated": stated,
            "ok": False,
            "computed": None,
            "error": "",
        }
        try:
            computed = safe_eval_arithmetic(expression)
            stated_value = float(stated)
            record["computed"] = computed
            record["ok"] = math.isclose(computed, stated_value, rel_tol=tolerance, abs_tol=tolerance)
        except Exception as exc:
            record["error"] = str(exc)
        records.append(record)
    return records


def load_jsonl(path: str | Path) -> list[dict]:
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def label_candidate(candidate_solution: str, gold_solution: str) -> dict:
    extracted = extract_answer(candidate_solution)
    gold = extract_answer(gold_solution)
    return {
        "extracted_answer": extracted,
        "gold_answer": gold,
        "correct": extracted != INVALID_ANSWER and gold != INVALID_ANSWER and extracted == gold,
        "calculator_checks": validate_calculator_annotations(candidate_solution),
    }


def self_test() -> None:
    assert extract_answer("work\n#### 1,200") == "1200"
    assert extract_answer("work\n#### -3.0") == "-3"
    assert extract_answer("no marker") == INVALID_ANSWER
    checks = validate_calculator_annotations("A <<48/2=24>> B <<2+2=5>>")
    assert checks[0]["ok"] is True
    assert checks[1]["ok"] is False
    assert label_candidate("x\n#### 72", "y\n#### 72")["correct"] is True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_extract = sub.add_parser("extract")
    p_extract.add_argument("text")
    p_label = sub.add_parser("label")
    p_label.add_argument("--candidate", required=True)
    p_label.add_argument("--gold", required=True)
    p_load = sub.add_parser("load-jsonl")
    p_load.add_argument("path")
    sub.add_parser("self-test")
    args = parser.parse_args(argv)
    if args.cmd == "extract":
        print(extract_answer(args.text))
    elif args.cmd == "label":
        print(json.dumps(label_candidate(args.candidate, args.gold), indent=2))
    elif args.cmd == "load-jsonl":
        print(json.dumps(load_jsonl(args.path), indent=2))
    elif args.cmd == "self-test":
        self_test()
        print(json.dumps({"ok": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
