#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Any


def format_example(record: dict[str, Any]) -> dict[str, Any]:
    instruction = str(record.get("instruction", "")).strip()
    input_text = str(record.get("input", "")).strip()
    answer = str(record.get("answer", "")).strip()
    mode = str(record.get("mode", "direct")).strip().lower()
    if not instruction or not input_text or not answer:
        raise ValueError("instruction, input, and answer are required")
    if mode not in {"direct", "cot"}:
        raise ValueError("mode must be direct or cot")

    blocks: list[str] = [f"Instruction: {instruction}"]
    exemplars = record.get("exemplars") or []
    for idx, exemplar in enumerate(exemplars, start=1):
        ex_input = str(exemplar.get("input", "")).strip()
        ex_answer = str(exemplar.get("answer", "")).strip()
        if ex_input and ex_answer:
            blocks.append(f"Example {idx} input: {ex_input}\nExample {idx} answer: {ex_answer}")
    blocks.append(f"Input: {input_text}")
    prompt = "\n\n".join(blocks)

    if mode == "cot":
        rationale = str(record.get("rationale", "")).strip()
        if not rationale:
            raise ValueError("cot mode requires a rationale")
        target = f"{rationale}\nFinal answer: {answer}"
    else:
        target = answer

    return {
        "prompt": prompt,
        "target": target,
        "metadata": {
            "mode": mode,
            "exemplar_count": len(exemplars),
            "uses_chain_of_thought": mode == "cot",
        },
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    record = json.loads(open(args.input_json, encoding="utf-8").read())
    output = format_example(record)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
