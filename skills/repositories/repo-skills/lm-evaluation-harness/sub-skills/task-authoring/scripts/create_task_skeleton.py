#!/usr/bin/env python3
"""Create a minimal external lm-evaluation-harness YAML task skeleton."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip()).strip("_").lower()
    if not slug:
        raise ValueError("task name must contain at least one letter or number")
    if not re.match(r"^[a-zA-Z_]", slug):
        slug = f"task_{slug}"
    return slug


def write_once(path: Path, content: str, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def yaml_content(task_name: str, with_json_fixture: bool) -> str:
    dataset_block = (
        "dataset_path: json\n"
        "dataset_name: null\n"
        "dataset_kwargs:\n"
        "  data_files:\n"
        "    validation: data/validation.jsonl\n"
        if with_json_fixture
        else "dataset_path: replace_me_dataset\ndataset_name: null\ndataset_kwargs: null\n"
    )
    return f"""task: {task_name}
task_alias: {task_name.replace('_', ' ').title()}
tag:
  - local_task
{dataset_block}validation_split: validation
fewshot_split: validation
process_docs: !function utils.process_docs
output_type: generate_until
doc_to_text: "Question: {{{{question}}}}\\nAnswer:"
doc_to_target: "{{{{answer}}}}"
generation_kwargs:
  until: ["\\n"]
metric_list:
  - metric: exact_match
    aggregation: mean
    higher_is_better: true
metadata:
  version: 1
"""


def utils_content() -> str:
    return '''"""Task-local helpers for an lm-evaluation-harness YAML task."""


def process_docs(dataset):
    """Normalize documents to the fields used by the YAML templates."""

    def normalize(doc):
        return {
            "question": str(doc["question"]).strip(),
            "answer": str(doc["answer"]).strip(),
        }

    return dataset.map(normalize)
'''


def readme_content(task_name: str) -> str:
    return f"""# {task_name}

This is an external lm-evaluation-harness task package.

Static lint:

```bash
python path/to/lint_task_yaml.py {task_name}.yaml
```

Discovery validation from the parent include directory:

```bash
lm-eval validate --tasks {task_name} --include_path ..
```

Run only after confirming dataset access, model/backend cost, and any task-local Python code implications.
"""


def fixture_lines() -> str:
    rows = [
        {"question": "What is 2 + 2?", "answer": "4"},
        {"question": "What color is a clear daytime sky often described as?", "answer": "blue"},
    ]
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a minimal external YAML task skeleton for lm-evaluation-harness.",
    )
    parser.add_argument("task_name", help="Task name to place in the YAML config.")
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory that will contain the task subdirectory. Default: current directory.",
    )
    parser.add_argument(
        "--with-json-fixture",
        action="store_true",
        help="Also create data/validation.jsonl and configure dataset_path: json.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing generated files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    task_name = slugify(args.task_name)
    task_dir = Path(args.output_dir).expanduser() / task_name

    write_once(task_dir / f"{task_name}.yaml", yaml_content(task_name, args.with_json_fixture), args.overwrite)
    write_once(task_dir / "utils.py", utils_content(), args.overwrite)
    write_once(task_dir / "README.md", readme_content(task_name), args.overwrite)
    if args.with_json_fixture:
        write_once(task_dir / "data" / "validation.jsonl", fixture_lines(), args.overwrite)

    print(f"created task skeleton: {task_dir}")
    print(f"yaml: {task_dir / (task_name + '.yaml')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
