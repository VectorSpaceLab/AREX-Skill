#!/usr/bin/env python3
"""Validate tree-of-thoughts TotAgent model-output text safely.

The package parser uses eval(), but this checker intentionally uses safe parsers
so samples can be validated without executing model output.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import sys
from numbers import Real
from typing import Any


def parse_sample(text: str) -> Any:
    """Parse JSON or Python-literal dict text without executing code."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    try:
        return ast.literal_eval(text)
    except (SyntaxError, ValueError) as exc:
        raise ValueError(
            "sample output must be JSON or Python dict-literal text"
        ) from exc


def validate_contract(value: Any) -> tuple[str, float]:
    if not isinstance(value, dict):
        raise ValueError(f"parsed value must be a dict, got {type(value).__name__}")

    missing = [key for key in ("thought", "evaluation") if key not in value]
    if missing:
        raise ValueError(f"missing required key(s): {', '.join(missing)}")

    thought = value["thought"]
    if not isinstance(thought, str) or not thought.strip():
        raise ValueError("thought must be a non-empty string")

    evaluation = value["evaluation"]
    if isinstance(evaluation, bool) or not isinstance(evaluation, Real):
        raise ValueError("evaluation must be numeric, not bool/string/null")

    evaluation_float = float(evaluation)
    if not math.isfinite(evaluation_float):
        raise ValueError("evaluation must be finite")

    if not 0.1 <= evaluation_float <= 1.0:
        raise ValueError("evaluation should be in the expected 0.1 to 1.0 range")

    return thought, evaluation_float


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a tree-of-thoughts model output sample. The sample must "
            "parse to a dict with a non-empty thought string and numeric "
            "evaluation score."
        )
    )
    parser.add_argument(
        "--sample-output",
        required=True,
        help=(
            "Model output text, e.g. "
            "'{\"thought\":\"try factorization\",\"evaluation\":0.82}'"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        parsed = parse_sample(args.sample_output)
        thought, evaluation = validate_contract(parsed)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    preview = repr(thought)
    if len(preview) > 80:
        preview = preview[:77] + "..."
    print(f"OK: parsed dict with thought={preview} evaluation={evaluation:g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
