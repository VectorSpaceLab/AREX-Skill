#!/usr/bin/env python3
"""Convert local GSM8K-style question/answer records to XTuner RL JSONL.

This is a network-free adaptation of XTuner's GSM8K conversion behavior. It
accepts local JSONL/JSON files containing records with question and answer
fields, extracts the final answer after "####", and writes XTuner RL reward
records with reward_model.ground_truth.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

FINAL_RE = re.compile(r"####\s*([-+]?(?:\d[\d,]*\.?\d*|\.\d+))")
LAST_NUMBER_RE = re.compile(r"[-+]?(?:\d[\d,]*\.?\d*|\.\d+)")
DEFAULT_INSTRUCTION = 'Let\'s think step by step and output the final answer after "####".'
TOOL_SYSTEM_PROMPT = (
    "You are a math expert. You are given a question and you need to solve it step by step. "
    "Reasoning step by step before any tool call. "
    "You should use the `calc_gsm8k_reward` tool after step by step solving the question, "
    "before generate final answer at least once and refine your answer if necessary. "
    "Put your final answer in the format of `#### <answer>`."
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert local GSM8K JSON/JSONL to XTuner RL reward JSONL.")
    parser.add_argument(
        "--input-dir",
        "--input",
        dest="input_dir",
        required=True,
        help="Local input file or directory. Directories may contain train/test/validation JSONL or JSON files.",
    )
    parser.add_argument("--out-dir", required=True, help="Output directory for converted split JSONL files.")
    parser.add_argument("--question-field", default="question", help="Input field containing the question.")
    parser.add_argument("--answer-field", default="answer", help="Input field containing the worked answer.")
    parser.add_argument("--data-source", default="openai/gsm8k", help="Value for data_source.")
    parser.add_argument("--ability", default="math", help="Value for ability.")
    parser.add_argument("--instruction", default=DEFAULT_INSTRUCTION, help="Instruction appended to each question.")
    parser.add_argument(
        "--split",
        default=None,
        help="Split name for a single input file. Defaults to the file stem or top-level JSON split key.",
    )
    parser.add_argument(
        "--with-tool",
        action="store_true",
        help="Add tool-agent system prompt and tools_kwargs metadata while retaining reward_model.ground_truth.",
    )
    parser.add_argument(
        "--allow-last-number",
        action="store_true",
        help="If an answer lacks '####', use the last number in the answer as ground_truth instead of failing.",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=20,
        help="Maximum conversion errors to print before suppressing extras.",
    )
    return parser.parse_args(argv)


def normalize_number(text: str) -> str:
    return text.strip().replace(",", "")


def extract_solution(answer: Any, record: dict[str, Any], *, allow_last_number: bool) -> str:
    if not isinstance(answer, str):
        raise ValueError("answer field must be a string")
    match = FINAL_RE.search(answer)
    if match:
        return normalize_number(match.group(1))
    for key in ("ground_truth", "final_answer", "answer_number", "target", "solution"):
        value = record.get(key)
        if value is not None and str(value) != "":
            return normalize_number(str(value))
    if allow_last_number:
        matches = LAST_NUMBER_RE.findall(answer)
        if matches:
            return normalize_number(matches[-1])
    raise ValueError("could not extract final answer; expected marker like '#### 72'")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            text = raw.strip()
            if not text:
                continue
            try:
                obj = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc.msg}") from exc
            if not isinstance(obj, dict):
                raise ValueError(f"{path}:{line_no}: each JSONL line must be an object")
            records.append(obj)
    return records


def read_json(path: Path) -> dict[str, list[dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {path.stem: ensure_record_list(data, str(path))}
    if isinstance(data, dict):
        split_map: dict[str, list[dict[str, Any]]] = {}
        # A single record with question/answer fields.
        if "question" in data or "answer" in data:
            split_map[path.stem] = [data]
            return split_map
        for split, value in data.items():
            if isinstance(value, list):
                split_map[str(split)] = ensure_record_list(value, f"{path}:{split}")
        if split_map:
            return split_map
    raise ValueError(f"{path}: expected a record, a list of records, or a split mapping")


def ensure_record_list(value: list[Any], label: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for idx, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"{label}[{idx}]: expected object")
        records.append(item)
    return records


def discover_inputs(input_path: Path, requested_split: str | None) -> dict[str, list[dict[str, Any]]]:
    if input_path.is_file():
        if input_path.suffix == ".jsonl":
            split = requested_split or input_path.stem
            return {split: read_jsonl(input_path)}
        if input_path.suffix == ".json":
            split_map = read_json(input_path)
            if requested_split and len(split_map) == 1:
                return {requested_split: next(iter(split_map.values()))}
            return split_map
        raise ValueError(f"unsupported input suffix: {input_path.suffix}")

    if not input_path.is_dir():
        raise ValueError(f"input path does not exist: {input_path}")

    preferred_names = ["train", "test", "validation", "val", "dev"]
    files: list[tuple[str, Path]] = []
    for name in preferred_names:
        for suffix in (".jsonl", ".json"):
            candidate = input_path / f"{name}{suffix}"
            if candidate.exists():
                split = "validation" if name in {"val", "dev"} else name
                files.append((split, candidate))
    if not files:
        for candidate in sorted(input_path.glob("*.jsonl")) + sorted(input_path.glob("*.json")):
            files.append((candidate.stem, candidate))
    if not files:
        raise ValueError(f"no .jsonl or .json files found under {input_path}")

    split_map: dict[str, list[dict[str, Any]]] = {}
    for split, path in files:
        if path.suffix == ".jsonl":
            split_map[split] = read_jsonl(path)
        else:
            nested = read_json(path)
            if len(nested) == 1 and split not in nested:
                split_map[split] = next(iter(nested.values()))
            else:
                split_map.update(nested)
    return split_map


def make_prompt(question: str, instruction: str) -> str:
    question = question.rstrip()
    if instruction:
        return f"{question} {instruction}"
    return question


def convert_record(
    record: dict[str, Any],
    *,
    idx: int,
    split: str,
    args: argparse.Namespace,
) -> dict[str, Any]:
    question_raw = record.get(args.question_field)
    if not isinstance(question_raw, str) or not question_raw.strip():
        raise ValueError(f"missing non-empty question field '{args.question_field}'")
    answer_raw = record.get(args.answer_field)
    solution = extract_solution(answer_raw, record, allow_last_number=args.allow_last_number)
    question = make_prompt(question_raw, args.instruction)

    prompt = [{"role": "user", "content": question}]
    if args.with_tool:
        prompt = [{"role": "system", "content": TOOL_SYSTEM_PROMPT}] + prompt

    extra_info: dict[str, Any] = {
        "split": split,
        "index": idx,
        "answer": answer_raw,
        "question": question_raw,
    }
    if args.with_tool:
        extra_info.update(
            {
                "need_tools_kwargs": True,
                "tools_kwargs": {
                    "calc_gsm8k_reward": {
                        "create_kwargs": {"ground_truth": solution},
                    }
                },
            }
        )

    converted = {
        "data_source": args.data_source,
        "prompt": prompt,
        "ability": args.ability,
        "reward_model": {"style": "rule", "ground_truth": solution},
        "extra_info": extra_info,
    }
    if args.with_tool:
        converted["agent_name"] = "tool_agent"
    return converted


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
            f.write("\n")
            count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    input_path = Path(args.input_dir)
    out_dir = Path(args.out_dir)

    try:
        split_map = discover_inputs(input_path, args.split)
    except Exception as exc:  # noqa: BLE001 - user-facing CLI
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    error_count = 0
    suppressed = False

    for split, raw_records in split_map.items():
        converted: list[dict[str, Any]] = []
        for idx, record in enumerate(raw_records):
            try:
                converted.append(convert_record(record, idx=idx, split=split, args=args))
            except Exception as exc:  # noqa: BLE001 - keep converting other records
                error_count += 1
                if error_count <= args.max_errors:
                    print(f"ERROR: split={split} index={idx}: {exc}", file=sys.stderr)
                elif not suppressed:
                    print("ERROR: further conversion errors suppressed", file=sys.stderr)
                    suppressed = True
        out_path = out_dir / f"{split}.jsonl"
        count = write_jsonl(out_path, converted)
        total += count
        print(f"wrote {count} records to {out_path}")

    if error_count:
        print(f"FAILED: {error_count} records could not be converted; wrote {total} valid records", file=sys.stderr)
        return 1
    print(f"OK: converted {total} records across {len(split_map)} split(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
