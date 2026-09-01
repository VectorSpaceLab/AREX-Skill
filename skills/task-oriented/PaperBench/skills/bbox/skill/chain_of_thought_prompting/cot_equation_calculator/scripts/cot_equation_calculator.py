#!/usr/bin/env python3
"""Safe arithmetic equation checks for chain-of-thought traces."""

from __future__ import annotations

import argparse
import ast
import json
import operator
import re
from dataclasses import dataclass
from typing import Any


OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}
EQUATION_RE = re.compile(r"(?P<expr>(?:[-+]?\d+(?:\.\d+)?|\s|[()+*/-]){3,80})=\s*(?P<result>-?\d+(?:\.\d+)?)")


@dataclass
class EquationCheck:
    expression: str
    stated_result: float
    computed_result: float
    is_correct: bool
    span: tuple[int, int]

    def public(self) -> dict[str, Any]:
        return {
            "expression": self.expression,
            "stated_result": self.stated_result,
            "computed_result": self.computed_result,
            "is_correct": self.is_correct,
        }


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        return float(OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right)))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
        return float(OPS[type(node.op)](_eval_node(node.operand)))
    raise ValueError(f"unsupported expression node: {type(node).__name__}")


def safe_eval_expression(expression: str) -> float:
    cleaned = expression.strip()
    if not re.fullmatch(r"[-+*/(). 0-9]+", cleaned):
        raise ValueError("expression contains unsafe characters")
    tree = ast.parse(cleaned, mode="eval")
    return _eval_node(tree)


def _display_number(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.6g}"


def check_equations(text: str, repair: bool = False) -> dict[str, Any]:
    checks: list[EquationCheck] = []
    for match in EQUATION_RE.finditer(text):
        expr = match.group("expr").strip()
        if not re.search(r"\d\s*[-+*/]\s*\d", expr):
            continue
        try:
            computed = safe_eval_expression(expr)
            stated = float(match.group("result"))
        except Exception:
            continue
        checks.append(
            EquationCheck(
                expression=expr,
                stated_result=stated,
                computed_result=computed,
                is_correct=abs(computed - stated) < 1e-9,
                span=match.span("result"),
            )
        )
    repaired = text
    if repair and checks:
        chars = list(text)
        for check in reversed(checks):
            if check.is_correct:
                continue
            start, end = check.span
            chars[start:end] = list(_display_number(check.computed_result))
        repaired = "".join(chars)
    return {
        "checks": [check.public() for check in checks],
        "all_equations_correct": all(check.is_correct for check in checks) if checks else True,
        "repaired_text": repaired,
    }


def _self_test() -> None:
    result = check_equations("2 * 3 = 7. Then 5 + 6 = 11.", repair=True)
    assert len(result["checks"]) == 2
    assert result["checks"][0]["is_correct"] is False
    assert "2 * 3 = 6" in result["repaired_text"]
    assert check_equations("__import__('os') = 0")["checks"] == []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", default="")
    parser.add_argument("--repair", action="store_true")
    parser.add_argument("--output", default="")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print(json.dumps({"ok": True}))
        return 0
    result = check_equations(args.text, repair=args.repair)
    encoded = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(encoded)
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
