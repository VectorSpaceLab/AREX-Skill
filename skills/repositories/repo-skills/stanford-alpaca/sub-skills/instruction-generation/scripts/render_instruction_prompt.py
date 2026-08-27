#!/usr/bin/env python3
"""Offline renderer for Stanford Alpaca instruction-generation prompts."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

DEFAULT_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "references" / "prompt-template.md"
DEFAULT_SELF_CHECK_FIXTURE = [
    {
        "instruction": "Summarize the meeting notes:",
        "input": "The team will ship the onboarding update on Friday and move analytics work to next sprint.",
        "output": "The team plans to ship the onboarding update on Friday and defer analytics work to next sprint.",
    },
    {
        "instruction": "Classify the sentiment of the review",
        "input": "The pasta was undercooked, but the staff fixed it quickly and politely.",
        "output": "Mixed",
    },
    {
        "instruction": "List three risks for the launch",
        "input": "",
        "output": "Insufficient testing, hidden bugs, and poor user feedback are all launch risks.",
    },
]


def extract_template(text: str) -> str:
    start = "<!-- prompt-template:start -->"
    end = "<!-- prompt-template:end -->"
    if start in text and end in text:
        return text.split(start, 1)[1].split(end, 1)[0].strip("\n")
    fenced = re.search(r"```(?:text)?\n(.*?)\n```", text, flags=re.S)
    if fenced:
        return fenced.group(1).strip("\n")
    return text.strip("\n")


def normalize_record(item: dict) -> dict:
    if not isinstance(item, dict):
        raise TypeError(f"Expected a mapping, got {type(item)!r}")
    if "instruction" not in item:
        raise ValueError("Each record needs an instruction field")

    if item.get("instances"):
        instance = item["instances"][0] or {}
        input_text = instance.get("input", "")
        output_text = instance.get("output", "")
    else:
        input_text = item.get("input", "")
        output_text = item.get("output", "")

    return {
        "instruction": str(item["instruction"]),
        "input": "" if input_text is None else str(input_text),
        "output": "" if output_text is None else str(output_text),
    }


def load_records(path: Path) -> List[dict]:
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".jsonl":
        records = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            records.append(normalize_record(json.loads(line)))
        return records

    payload = json.loads(text)
    if isinstance(payload, list):
        return [normalize_record(item) for item in payload]
    if isinstance(payload, dict) and "records" in payload and isinstance(payload["records"], list):
        return [normalize_record(item) for item in payload["records"]]
    raise ValueError(f"Unsupported fixture format in {path}")


def render_prompt(template: str, prompt_instructions: Sequence[dict]) -> str:
    prompt = template.rstrip() + "\n"
    idx = 0
    for idx, task_dict in enumerate(prompt_instructions):
        instruction = re.sub(r"\s+", " ", task_dict["instruction"]).strip().rstrip(":")
        input_text = task_dict["input"]
        input_text = "<noinput>" if input_text.lower() == "" else input_text
        prompt += "###\n"
        prompt += f"{idx + 1}. Instruction: {instruction}\n"
        prompt += f"{idx + 1}. Input:\n{input_text}\n"
        prompt += f"{idx + 1}. Output:\n{task_dict['output']}\n"
    prompt += "###\n"
    prompt += f"{idx + 2}. Instruction:"
    return prompt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--template-path",
        type=Path,
        default=DEFAULT_TEMPLATE_PATH,
        help="Path to the bundled prompt-template.md file.",
    )
    parser.add_argument(
        "--seed-tasks-path",
        type=Path,
        help="Optional seed-task JSONL/JSON fixture to render.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="Number of seed records to render from the fixture.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output file. If omitted, the prompt is printed to stdout.",
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="Render the built-in tiny fixture and print a short success message.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    template = extract_template(args.template_path.read_text(encoding="utf-8"))

    if args.seed_tasks_path is None:
        records = [normalize_record(item) for item in DEFAULT_SELF_CHECK_FIXTURE]
    else:
        records = load_records(args.seed_tasks_path)

    if args.count < 1:
        raise SystemExit("--count must be at least 1")
    if args.count > len(records):
        raise SystemExit(f"Requested {args.count} records but only found {len(records)}")

    prompt = render_prompt(template, records[: args.count])

    if args.output:
        args.output.write_text(prompt, encoding="utf-8")
    else:
        sys.stdout.write(prompt)
        if not prompt.endswith("\n"):
            sys.stdout.write("\n")

    if args.self_check:
        assert prompt.endswith(f"{args.count + 1}. Instruction:")
        if args.seed_tasks_path is None and args.count >= 3:
            assert "3. Input:\n<noinput>" in prompt
        elif any(not record["input"] for record in records[: args.count]):
            assert "<noinput>" in prompt
        print(f"\n[ok] rendered {args.count} records from the offline fixture", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
