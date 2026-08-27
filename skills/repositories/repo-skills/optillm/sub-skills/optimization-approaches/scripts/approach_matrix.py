#!/usr/bin/env python3
"""Inspect OptiLLM approach slugs and parse approach/model strings offline."""
from __future__ import annotations

import argparse
import json

FALLBACK_APPROACHES = [
    "none", "mcts", "bon", "moa", "rto", "z3", "self_consistency", "pvg",
    "rstar", "cot_reflection", "plansearch", "leap", "re2", "cepo", "mars",
]


def load_known_approaches() -> list[str]:
    try:
        from optillm import known_approaches
        return list(known_approaches)
    except Exception:
        return FALLBACK_APPROACHES


def parse(model: str, known: list[str]):
    try:
        from optillm import parse_combined_approach
        return parse_combined_approach(model, known, {})
    except Exception:
        if model == "auto":
            return "SINGLE", ["none"], model
        parts = model.split("-")
        approaches = []
        operation = "SINGLE"
        model_parts = []
        parsing = True
        for part in parts:
            if parsing:
                if part in known:
                    approaches.append(part)
                elif "&" in part:
                    operation = "AND"
                    approaches.extend(part.split("&"))
                elif "|" in part:
                    operation = "OR"
                    approaches.extend(part.split("|"))
                else:
                    parsing = False
                    model_parts.append(part)
            else:
                model_parts.append(part)
        if not approaches:
            approaches = ["none"]
        return operation, approaches, "-".join(model_parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="List or parse OptiLLM approaches without provider calls")
    parser.add_argument("--parse", dest="model_string", help="Model/approach string to parse, e.g. bon|moa|mcts-gpt-4o-mini")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    known = load_known_approaches()
    result = {"known_approaches": known}
    if args.model_string:
        operation, approaches, model = parse(args.model_string, known)
        result["parse"] = {
            "input": args.model_string,
            "operation": operation,
            "approaches": approaches,
            "model": model,
        }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Known approaches: " + ", ".join(known))
        if "parse" in result:
            parsed = result["parse"]
            print(f"Input: {parsed['input']}")
            print(f"Operation: {parsed['operation']}")
            print("Approaches: " + ", ".join(parsed["approaches"]))
            print(f"Model: {parsed['model']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
