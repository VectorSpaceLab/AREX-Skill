#!/usr/bin/env python3
"""Convert OpenChat HumanEval result rows to EvalPlus JSONL samples.

This is a safe, self-contained adaptation of OpenChat's converter. It reads
OpenChat result JSON files, extracts rows whose task_type is coding/humaneval,
and writes one EvalPlus-compatible JSONL sample file per input result file.
It does not import OpenChat, require a source checkout, execute generated code,
or install EvalPlus.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Iterator, Any


def iter_result_files(path: Path) -> Iterator[Path]:
    if path.is_file():
        if path.suffix.lower() == ".json":
            yield path
        return
    yield from sorted(p for p in path.glob("*.json") if p.is_file())


def load_json_array(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path} is not a JSON array")
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"{path} row {index} is not a JSON object")
        rows.append(item)
    return rows


def humaneval_samples(rows: Iterable[dict[str, Any]], *, strict: bool) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for index, item in enumerate(rows):
        if item.get("task_type") != "coding/humaneval":
            continue
        answer = item.get("answer")
        if not isinstance(answer, dict):
            if strict:
                raise ValueError(f"coding/humaneval row {index} has non-object answer")
            continue
        if not isinstance(answer.get("task_id"), str) or not isinstance(answer.get("completion"), str):
            if strict:
                raise ValueError(f"coding/humaneval row {index} answer lacks string task_id/completion")
            continue
        samples.append({"task_id": answer["task_id"], "completion": answer["completion"]})
    return samples


def write_jsonl(samples: Iterable[dict[str, Any]], path: Path) -> int:
    count = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False, separators=(",", ":")))
            f.write("\n")
            count += 1
    return count


def convert_to_evalplus(results_path: Path, output_path: Path, *, strict: bool, skip_empty: bool) -> dict[str, int]:
    if not results_path.exists():
        raise FileNotFoundError(f"results path does not exist: {results_path}")

    converted: dict[str, int] = {}
    files = list(iter_result_files(results_path))
    if not files:
        raise FileNotFoundError(f"no .json result files found in {results_path}")

    output_path.mkdir(parents=True, exist_ok=True)
    for result_file in files:
        rows = load_json_array(result_file)
        samples = humaneval_samples(rows, strict=strict)
        if skip_empty and not samples:
            continue
        out_file = output_path / f"{result_file.stem}.jsonl"
        converted[str(out_file)] = write_jsonl(samples, out_file)
    return converted


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert OpenChat coding/humaneval result rows into EvalPlus JSONL sample files."
    )
    parser.add_argument(
        "--results-path",
        "--results_path",
        type=Path,
        default=Path("eval_results"),
        help="Directory of OpenChat .json result files, or one result .json file.",
    )
    parser.add_argument(
        "--output-path",
        "--output_path",
        type=Path,
        default=Path("evalplus_codegen"),
        help="Directory where EvalPlus .jsonl sample files will be written.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if a coding/humaneval row has a malformed answer object.",
    )
    parser.add_argument(
        "--skip-empty",
        action="store_true",
        help="Do not create output files for result files that contain no HumanEval samples.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    converted = convert_to_evalplus(
        args.results_path,
        args.output_path,
        strict=args.strict,
        skip_empty=args.skip_empty,
    )
    for filename, count in converted.items():
        print(f"wrote {count} samples: {filename}")


if __name__ == "__main__":
    main()
