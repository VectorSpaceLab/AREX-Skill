#!/usr/bin/env python3
"""Validate and optionally score a Hack EE-style token mapping submission."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

TOKEN_ID_RE = re.compile(r"^[0-9]+$")


class DuplicateTrackingDict(dict):
    def __init__(self, pairs: list[tuple[str, Any]]):
        super().__init__()
        self.duplicates: list[str] = []
        for key, value in pairs:
            if key in self:
                self.duplicates.append(key)
            self[key] = value


def load_json_with_duplicates(path: Path) -> tuple[Any, list[str]]:
    duplicates: list[str] = []

    def hook(pairs: list[tuple[str, Any]]) -> DuplicateTrackingDict:
        obj = DuplicateTrackingDict(pairs)
        duplicates.extend(obj.duplicates)
        return obj

    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=hook)
    return data, duplicates


def validate_submission(data: Any, duplicates: list[str]) -> tuple[dict[str, str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if duplicates:
        warnings.append(f"duplicate JSON keys detected before parsing collapsed them: {sorted(set(duplicates))}")
    if not isinstance(data, dict):
        errors.append("top-level JSON must be an object")
        return {}, errors, warnings
    tokens = data.get("tokens")
    if not isinstance(tokens, dict):
        errors.append("top-level object must contain a 'tokens' object")
        return {}, errors, warnings
    normalized: dict[str, str] = {}
    for key, value in tokens.items():
        if not isinstance(key, str) or not TOKEN_ID_RE.match(key):
            errors.append(f"token id key must be a non-negative integer string, got {key!r}")
        if not isinstance(value, str):
            errors.append(f"mapping value for {key!r} must be a string, got {type(value).__name__}")
        else:
            normalized[str(key)] = value
    if not normalized:
        warnings.append("submission contains no token mappings")
    return normalized, errors, warnings


def score_submission(guess: dict[str, str], gold: dict[str, str], ignored: set[str]) -> dict[str, Any]:
    correct = 0
    incorrect = 0
    ignored_count = 0
    missing_gold: list[str] = []
    details: dict[str, str] = {}
    for key, value in guess.items():
        if key in ignored:
            ignored_count += 1
            details[key] = "ignored"
        elif key not in gold:
            missing_gold.append(key)
            incorrect += 1
            details[key] = "no-gold-counted-incorrect"
        elif gold[key] == value:
            correct += 1
            details[key] = "correct"
        else:
            incorrect += 1
            details[key] = "incorrect"
    return {
        "correct": correct,
        "incorrect": incorrect,
        "ignored": ignored_count,
        "score": correct * 10 - incorrect,
        "missing_gold_keys": missing_gold,
        "details": details,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Hack EE token mapping JSON and optionally score against a local gold file.")
    parser.add_argument("submission", type=Path, help="Submission JSON with top-level tokens object.")
    parser.add_argument("--gold", type=Path, help="Optional gold JSON with a top-level tokens object or direct id->token object.")
    parser.add_argument("--ignore-ids", help="Comma-separated token id strings to ignore, e.g. hinted tokens.")
    args = parser.parse_args()

    data, duplicates = load_json_with_duplicates(args.submission)
    guess, errors, warnings = validate_submission(data, duplicates)
    result: dict[str, Any] = {"valid": not errors, "mapping_count": len(guess), "errors": errors, "warnings": warnings}

    if args.gold:
        gold_data, _ = load_json_with_duplicates(args.gold)
        gold_tokens = gold_data.get("tokens") if isinstance(gold_data, dict) and isinstance(gold_data.get("tokens"), dict) else gold_data
        if not isinstance(gold_tokens, dict):
            result.setdefault("errors", []).append("gold file must be an object or contain a tokens object")
            result["valid"] = False
        else:
            ignored = {item.strip() for item in (args.ignore_ids or "").split(",") if item.strip()}
            result["score"] = score_submission(guess, {str(k): str(v) for k, v in gold_tokens.items()}, ignored)

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
