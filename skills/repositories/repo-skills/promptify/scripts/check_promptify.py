#!/usr/bin/env python3
"""Promptify smoke and inspection helper.

This script is safe to run from any directory after Promptify has been installed.
It never calls a provider. Use it to inspect the public API, exercise the core
structured-task path with mocked engines, and verify the dataset/evaluation
helpers on tiny fixtures.

Optional local-development aid:
  --repo-root PATH adds a checkout to sys.path before importing promptify.

Examples:
  python scripts/check_promptify.py --mode inspect
  python scripts/check_promptify.py --mode tasks
  python scripts/check_promptify.py --mode evaluation
  python scripts/check_promptify.py --mode all
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import inspect as pyinspect
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List


def _preparse_repo_root() -> str | None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--repo-root", default=None)
    known, _ = parser.parse_known_args()
    return known.repo_root


_REPO_ROOT = _preparse_repo_root()
if _REPO_ROOT:
    sys.path.insert(0, _REPO_ROOT)

from pydantic import BaseModel
from promptify import (
    Classify,
    ExtractRelations,
    ExtractTable,
    ExtractTopics,
    GenerateQuestions,
    GenerateSQL,
    ModelConfig,
    NER,
    NormalizeText,
    QA,
    Summarize,
    Task,
    get_cost_summary,
)
from promptify.core.config import CacheConfig
from promptify.engine.llm import LLMResponse
from promptify.eval.metrics import exact_match
from promptify.parser import Parser
from promptify.prompts import PromptBuilder


class _MockEngine:
    def __init__(self, payload: str):
        self.payload = payload

    def complete(self, messages, output_schema=None, **kwargs):
        return LLMResponse(text=self.payload, parsed=None, usage={}, model="mock", cost=0.0)

    async def acomplete(self, messages, output_schema=None, **kwargs):
        return self.complete(messages, output_schema=output_schema, **kwargs)


class _Review(BaseModel):
    sentiment: str
    rating: float


class _MockTask:
    def __call__(self, text, **kwargs):
        return kwargs.get("reply", "yes")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def print_header(title: str) -> None:
    print(f"\n== {title} ==")


def inspect_public_api() -> None:
    from importlib.metadata import version
    import promptify

    print_header("Promptify metadata")
    print(f"version={version('promptify')}")
    print(f"module_file={promptify.__file__}")
    exports = [
        "Classify",
        "ExtractRelations",
        "ExtractTable",
        "ExtractTopics",
        "GenerateQuestions",
        "GenerateSQL",
        "ModelConfig",
        "NER",
        "NormalizeText",
        "QA",
        "Summarize",
        "Task",
        "get_cost_summary",
        "setup_logging",
    ]
    print(f"exports={exports}")

    print_header("Signatures")
    symbols = [
        ("NER", NER),
        ("Classify", Classify),
        ("QA", QA),
        ("Summarize", Summarize),
        ("Task", Task),
        ("ExtractRelations", ExtractRelations),
        ("ExtractTable", ExtractTable),
        ("GenerateQuestions", GenerateQuestions),
        ("GenerateSQL", GenerateSQL),
        ("NormalizeText", NormalizeText),
        ("ExtractTopics", ExtractTopics),
        ("ModelConfig", ModelConfig),
        ("CacheConfig", CacheConfig),
        ("Parser", Parser),
        ("PromptBuilder", PromptBuilder),
        ("get_cost_summary", get_cost_summary),
    ]
    for name, obj in symbols:
        print(f"{name} {pyinspect.signature(obj)}")


async def _async_call(task, text: str, **kwargs):
    return await task.acall(text, **kwargs)


def smoke_tasks() -> None:
    print_header("Structured task smoke")

    ner = NER(model="gpt-4o-mini", domain="medical")
    ner.engine = _MockEngine('{"entities": [{"text": "diabetes", "label": "CONDITION"}]}')
    ner_result = ner("The patient has diabetes")
    require(ner_result.entities[0].text == "diabetes", "NER mock smoke failed")

    clf = Classify(model="gpt-4o-mini", labels=["positive", "negative"])
    clf.engine = _MockEngine('{"label": "positive", "confidence": 0.91}')
    clf_result = clf("Great product")
    require(clf_result.label == "positive", "Classify smoke failed")

    qa = QA(model="gpt-4o-mini")
    qa.engine = _MockEngine('{"answer": "Ulm", "evidence": "Einstein was born in Ulm", "confidence": 0.95}')
    qa_result = qa("Einstein was born in Ulm in 1879.", question="Where was Einstein born?")
    require(qa_result.answer == "Ulm", "QA smoke failed")
    qa_async_result = asyncio.run(_async_call(qa, "Einstein was born in Ulm in 1879.", question="Where was Einstein born?"))
    require(qa_async_result.answer == "Ulm", "QA async smoke failed")

    summarizer = Summarize(model="gpt-4o-mini", key_points=True)
    summarizer.engine = _MockEngine('{"summary": "short summary", "key_points": ["a", "b"]}')
    summary = summarizer("Long article text")
    require(summary.key_points == ["a", "b"], "Summarize smoke failed")

    custom = Task(model="gpt-4o-mini", output_schema=_Review, instruction="Return JSON")
    custom.engine = _MockEngine('{"sentiment": "positive", "rating": 8.5}')
    review = custom("Nice movie")
    require(review.sentiment == "positive", "Custom Task smoke failed")
    batch = custom.batch(["x", "y"], max_concurrent=2)
    require(len(batch) == 2, "Custom Task batch smoke failed")

    extract_rel = ExtractRelations(model="gpt-4o-mini")
    extract_rel.engine = _MockEngine('{"relations": [{"subject": "Einstein", "predicate": "born_in", "object": "Ulm"}]}')
    rel_result = extract_rel("Einstein was born in Ulm.")
    require(rel_result.relations[0].object == "Ulm", "ExtractRelations smoke failed")

    extract_table = ExtractTable(model="gpt-4o-mini")
    extract_table.engine = _MockEngine('{"rows": [{"data": {"name": "Alice", "age": "30"}}]}')
    table_result = extract_table("Alice is 30.")
    require(table_result.rows[0].data["name"] == "Alice", "ExtractTable smoke failed")

    gen_questions = GenerateQuestions(model="gpt-4o-mini", num_questions=2)
    gen_questions.engine = _MockEngine('{"questions": [{"question": "Where was Einstein born?", "answer": "Ulm"}]}')
    questions_result = gen_questions("Einstein was born in Ulm.")
    require(questions_result.questions[0].answer == "Ulm", "GenerateQuestions smoke failed")

    gen_sql = GenerateSQL(model="gpt-4o-mini", schema="CREATE TABLE users (id INT, name TEXT)")
    gen_sql.engine = _MockEngine('{"query": "SELECT * FROM users", "explanation": "list all users"}')
    sql_result = gen_sql("Get all users")
    require(sql_result.query.startswith("SELECT"), "GenerateSQL smoke failed")

    normalize = NormalizeText(model="gpt-4o-mini", rules=["lowercase", "remove punctuation"])
    normalize.engine = _MockEngine('{"normalized_text": "hello world"}')
    normalized = normalize("Hello, World!")
    require(normalized.normalized_text == "hello world", "NormalizeText smoke failed")

    topics = ExtractTopics(model="gpt-4o-mini", num_topics=2)
    topics.engine = _MockEngine('{"topics": [{"topic": "science", "words": ["ai", "data"]}]}')
    topic_result = topics("AI and data are changing science.")
    require(topic_result.topics[0].topic == "science", "ExtractTopics smoke failed")

    parser = Parser()
    parsed = parser.parse('{"answer": "yes"}')
    require(parsed == {"answer": "yes"}, "Parser smoke failed")

    builder = PromptBuilder()
    messages = builder.build(instruction="Return JSON.", text_input="Hello", labels=["greet"])
    require(messages[0]["role"] == "system", "PromptBuilder smoke failed")

    print("structured_tasks_smoke_ok")


def smoke_evaluation() -> None:
    print_header("Evaluation smoke")

    from promptify.eval import evaluate
    from promptify.eval.datasets import load_dataset
    from promptify.eval.metrics import rouge

    sample_list = [
        {"input": "q1", "expected": "yes", "reply": "yes"},
        {"input": "q2", "expected": "no", "reply": "no"},
    ]
    loaded_list = load_dataset(sample_list)
    require(len(loaded_list) == 2, "List dataset load failed")

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        json_path = root / "dataset.json"
        csv_path = root / "dataset.csv"
        json_payload = [
            {"input": "json-1", "expected": "yes", "reply": "yes"},
            {"input": "json-2", "expected": "no", "reply": "no"},
        ]
        json_path.write_text(json.dumps(json_payload), encoding="utf-8")
        csv_rows = [
            {"input": "csv-1", "expected": "yes", "reply": "yes"},
            {"input": "csv-2", "expected": '{"label": "pos"}', "reply": '{"label": "pos"}'},
        ]
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["input", "expected", "reply"])
            writer.writeheader()
            writer.writerows(csv_rows)

        loaded_json = load_dataset(json_path)
        loaded_csv = load_dataset(csv_path)
        require(len(loaded_json) == 2, "JSON dataset load failed")
        require(loaded_csv[1]["expected"] == {"label": "pos"}, "CSV JSON decoding failed")

    progress_calls: List[tuple[int, int]] = []
    scores = evaluate(
        task=_MockTask(),
        dataset=sample_list,
        metrics=["exact_match"],
        progress_callback=lambda current, total: progress_calls.append((current, total)),
    )
    require(scores["exact_match"] == 1.0, "evaluate exact_match failed")
    require(progress_calls == [(1, 2), (2, 2)], "Progress callback smoke failed")

    limited = evaluate(task=_MockTask(), dataset=sample_list, metrics=["exact_match"], max_samples=1)
    require(limited["exact_match"] == 1.0, "max_samples smoke failed")

    require(exact_match("same", "same") == 1.0, "exact_match helper failed")
    try:
        rouge_scores = rouge("same", "same")
        require(round(rouge_scores["rougeL"], 6) == 1.0, "rouge smoke failed")
    except ImportError as exc:
        raise RuntimeError("ROUGE smoke failed: install promptify[eval] to enable rouge-score") from exc

    print("evaluation_smoke_ok")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Promptify smoke and inspection helper")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Optional checkout path to add to sys.path before importing promptify",
    )
    parser.add_argument(
        "--mode",
        choices=["inspect", "tasks", "evaluation", "all"],
        default="inspect",
        help="Which check to run",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.mode in {"inspect", "all"}:
        inspect_public_api()
    if args.mode in {"tasks", "all"}:
        smoke_tasks()
    if args.mode in {"evaluation", "all"}:
        smoke_evaluation()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
