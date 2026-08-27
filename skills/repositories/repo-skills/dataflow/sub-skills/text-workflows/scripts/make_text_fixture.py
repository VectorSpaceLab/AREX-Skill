#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_text_rows() -> list[dict]:
    return [
        {
            "raw_content": "Open-data pipelines should keep clean text, remove duplicates, and preserve meaning.",
            "text": "Open-data pipelines should keep clean text, remove duplicates, and preserve meaning.",
            "problem": "What is 17 + 25?",
            "source": "clean_text",
            "lang": "en",
        },
        {
            "raw_content": "Visit https://example.com for details. Thanks :)\nThanks :)\nThanks :)",
            "text": "Visit https://example.com for details. Thanks :)\nThanks :)\nThanks :)",
            "problem": "If x = 3, compute 2x^2 + 1.",
            "source": "noisy_text",
            "lang": "en",
        },
        {
            "raw_content": "<p>Short HTML snippet</p>\n<script>console.log('hi')</script>",
            "text": "Short HTML snippet",
            "problem": "Translate 'good morning' to Chinese.",
            "source": "markup_text",
            "lang": "en",
        },
    ]


def make_reasoning_rows() -> list[dict]:
    return [
        {
            "instruction": "What is 17 + 25?",
            "output": "42",
            "golden_answer": "42",
            "category": "math",
        },
        {
            "instruction": "If x = 3, compute 2x^2 + 1.",
            "output": "19",
            "golden_answer": "19",
            "category": "math",
        },
        {
            "instruction": "A train leaves at 9:00 and arrives 2 hours later. What time is it?",
            "output": "11:00",
            "golden_answer": "11:00",
            "category": "general",
        },
    ]


def make_translation_rows() -> list[dict]:
    return [
        {
            "raw_content": "Good morning, team.",
            "source_lang": "en",
            "target_lang": "zh",
            "topic": "greeting",
        },
        {
            "raw_content": "Please keep the answer in JSON.",
            "source_lang": "en",
            "target_lang": "zh",
            "topic": "instruction",
        },
        {
            "raw_content": "The model is ready for deployment.",
            "source_lang": "en",
            "target_lang": "zh",
            "topic": "ops",
        },
    ]


def make_code_rows() -> list[dict]:
    return [
        {
            "instruction": "Write a Python function that adds two numbers.",
            "input": "",
            "output": "def add(a, b):\n    return a + b",
            "generated_instruction": "Write a Python function that adds two numbers.",
            "generated_code": "def add(a, b):\n    return a + b",
            "text": "def add(a, b):\n    return a + b",
            "lines": "def add(a, b):\n    return a + b",
            "filetype": "python",
            "filename": "add.py",
            "line_count": 2,
            "language": "python",
        },
        {
            "instruction": "Sort a list of integers in ascending order.",
            "input": "",
            "output": "def sort_numbers(values):\n    return sorted(values)",
            "generated_instruction": "Sort a list of integers in ascending order.",
            "generated_code": "def sort_numbers(values):\n    return sorted(values)",
            "text": "def sort_numbers(values):\n    return sorted(values)",
            "lines": "def sort_numbers(values):\n    return sorted(values)",
            "filetype": "python",
            "filename": "sort_numbers.py",
            "line_count": 2,
            "language": "python",
        },
        {
            "instruction": "Explain why this code sample is well formed.",
            "input": "def hello():\n    print('hello')",
            "output": "It is short, readable, and executes safely.",
            "generated_instruction": "Explain why this code sample is well formed.",
            "generated_code": "def hello():\n    print('hello')",
            "text": "def hello():\n    print('hello')",
            "lines": "def hello():\n    print('hello')",
            "filetype": "text",
            "filename": "notes.md",
            "line_count": 2,
            "language": "python",
        },
    ]


def make_text2sql_rows() -> list[dict]:
    return [
        {
            "SQL": "SELECT name FROM students WHERE grade = 'A';",
            "db_id": "toy_school",
            "question": "Which students earned an A?",
            "evidence": "Table students(name, grade)",
            "prompt": "",
        },
        {
            "SQL": "SELECT COUNT(*) FROM orders WHERE status = 'paid';",
            "db_id": "toy_shop",
            "question": "How many paid orders are there?",
            "evidence": "Table orders(status)",
            "prompt": "",
        },
        {
            "SQL": "WITH recent AS (SELECT * FROM logs) SELECT * FROM recent;",
            "db_id": "toy_logs",
            "question": "Show recent logs.",
            "evidence": "Table logs(ts, message)",
            "prompt": "",
        },
    ]


def make_text2model_rows() -> list[dict]:
    return [
        {
            "text": "DataFlow turns text cleanup into repeatable pipelines.",
            "source": "text2model",
        },
        {
            "text": "Offline fixtures are useful for validating column contracts.",
            "source": "text2model",
        },
        {
            "text": "The model should answer using the provided schema only.",
            "source": "text2model",
        },
    ]


def build_manifest(files: list[tuple[str, list[dict] | int]]) -> dict:
    manifest = {}
    for rel_path, rows in files:
        if isinstance(rows, int):
            count = rows
            columns = []
        else:
            count = len(rows)
            columns = sorted({key for row in rows for key in row.keys()})
        manifest[rel_path] = {"rows": count, "columns": columns}
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate tiny offline DataFlow text fixtures")
    parser.add_argument("--output-dir", default=".", help="Directory that will receive the fixtures")
    args = parser.parse_args()

    root = Path(args.output_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)

    text_rows = make_text_rows()
    reasoning_rows = make_reasoning_rows()
    translation_rows = make_translation_rows()
    code_rows = make_code_rows()
    text2sql_rows = make_text2sql_rows()
    text2model_rows = make_text2model_rows()

    output_files: list[tuple[str, list[dict]]] = []

    write_jsonl(root / "text" / "pt_input.jsonl", text_rows)
    output_files.append(("text/pt_input.jsonl", text_rows))

    write_jsonl(root / "text" / "math_100.jsonl", [
        {"problem": "What is 17 + 25?", "source": "math"},
        {"problem": "If x = 3, compute 2x^2 + 1.", "source": "math"},
    ])
    output_files.append(("text/math_100.jsonl", [
        {"problem": "What is 17 + 25?", "source": "math"},
        {"problem": "If x = 3, compute 2x^2 + 1.", "source": "math"},
    ]))

    write_jsonl(root / "translation" / "translation.jsonl", translation_rows)
    output_files.append(("translation/translation.jsonl", translation_rows))

    write_json(root / "reasoning" / "pipeline_math_short.json", reasoning_rows[:2])
    output_files.append(("reasoning/pipeline_math_short.json", reasoning_rows[:2]))

    write_json(root / "reasoning" / "pipeline_general.json", reasoning_rows)
    output_files.append(("reasoning/pipeline_general.json", reasoning_rows))

    raw_code_rows = [
        {
            "input": row["text"],
            "text": row["text"],
            "lines": row["lines"],
            "filetype": row["filetype"],
            "filename": row["filename"],
            "line_count": row["line_count"],
            "language": row["language"],
        }
        for row in code_rows
    ]
    write_jsonl(root / "code" / "raw_code.jsonl", raw_code_rows)
    output_files.append(("code/raw_code.jsonl", raw_code_rows))

    code_filter_rows = [
        {
            "lines": row["lines"],
            "text": row["text"],
            "filetype": row["filetype"],
            "filename": row["filename"],
            "line_count": row["line_count"],
            "language": row["language"],
        }
        for row in code_rows
    ]
    write_jsonl(root / "code" / "code_input.jsonl", code_filter_rows)
    output_files.append(("code/code_input.jsonl", code_filter_rows))

    write_jsonl(root / "code" / "code_sft_seed.jsonl", [
        {
            "instruction": row["instruction"],
            "input": row["input"],
            "output": row["output"],
        }
        for row in code_rows[:2]
    ])
    output_files.append(("code/code_sft_seed.jsonl", [
        {
            "instruction": row["instruction"],
            "input": row["input"],
            "output": row["output"],
        }
        for row in code_rows[:2]
    ]))

    write_jsonl(root / "text2sql" / "pipeline_refine.jsonl", text2sql_rows)
    output_files.append(("text2sql/pipeline_refine.jsonl", text2sql_rows))

    write_jsonl(root / "text2sql" / "pipeline_gen.jsonl", [
        {
            "SQL": row["SQL"],
            "db_id": row["db_id"],
            "question": "",
            "evidence": row["evidence"],
        }
        for row in text2sql_rows
    ])
    output_files.append(("text2sql/pipeline_gen.jsonl", [
        {
            "SQL": row["SQL"],
            "db_id": row["db_id"],
            "question": "",
            "evidence": row["evidence"],
        }
        for row in text2sql_rows
    ]))

    write_jsonl(root / "text2model" / "text_input.jsonl", text2model_rows)
    output_files.append(("text2model/text_input.jsonl", text2model_rows))

    write_jsonl(root / "conversation" / "empty.jsonl", [
        {
            "category": "general",
            "conversation": [
                {"role": "user", "value": "Hello"},
                {"role": "assistant", "value": "Hi there!"},
            ],
        }
    ])
    output_files.append(("conversation/empty.jsonl", [
        {
            "category": "general",
            "conversation": [
                {"role": "user", "value": "Hello"},
                {"role": "assistant", "value": "Hi there!"},
            ],
        }
    ]))

    manifest = build_manifest(output_files)
    (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {len(output_files)} fixture files to {root}")
    for rel_path, rows in output_files:
        print(f"- {rel_path}: {len(rows)} rows")
    print("- manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
