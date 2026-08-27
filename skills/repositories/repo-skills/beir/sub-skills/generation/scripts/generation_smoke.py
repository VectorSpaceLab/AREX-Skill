#!/usr/bin/env python3
"""Offline smoke test for BEIR generation output layouts.

This helper uses fake generation models, so it performs no downloads and does
not require GPUs, model credentials, or external services.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import tempfile
from pathlib import Path
import sys


def _allow_source_checkout_import() -> None:
    """Let the script run from a BEIR source checkout as well as an installed package."""

    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists() and (parent / "beir" / "generation").is_dir():
            sys.path.insert(0, str(parent))
            return


try:
    from beir.generation import PassageExpansion, QueryGenerator
except ModuleNotFoundError:
    _allow_source_checkout_import()
    from beir.generation import PassageExpansion, QueryGenerator


class FakeQueryModel:
    def generate(self, corpus, ques_per_passage, max_length, top_p, top_k):
        queries = []
        for doc in corpus:
            title = doc.get("title", "untitled")
            for index in range(ques_per_passage):
                queries.append(f"question {index + 1} about {title}?")
        return queries

    def generate_multi_process(
        self,
        corpus,
        pool,
        ques_per_passage,
        max_length,
        top_p,
        top_k,
        chunk_size=None,
        batch_size=32,
    ):
        pool.setdefault("calls", 0)
        pool["calls"] += 1
        return self.generate(corpus, ques_per_passage, max_length, top_p, top_k)


class FakePassageExpansionModel:
    def generate(self, corpus, max_length, top_k):
        return [f"expanded terms for {doc.get('title', 'untitled')}" for doc in corpus]


def tiny_corpus():
    return {
        "doc1": {
            "title": "Relativity",
            "text": "Albert Einstein developed the theory of relativity.",
        },
        "doc2": {
            "title": "Wheat beer",
            "text": "Wheat beer is brewed with a large proportion of wheat.",
        },
    }


def read_jsonl(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def read_qrels(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.reader(handle, delimiter="\t"))


def assert_query_outputs(output_dir):
    queries_path = output_dir / "gen-queries.jsonl"
    qrels_path = output_dir / "gen-qrels" / "train.tsv"
    assert queries_path.is_file(), f"missing generated queries: {queries_path}"
    assert qrels_path.is_file(), f"missing generated qrels: {qrels_path}"

    queries = read_jsonl(queries_path)
    qrels_rows = read_qrels(qrels_path)
    assert len(queries) == 4, f"expected 4 generated queries, got {len(queries)}"
    assert qrels_rows[0] == ["query-id", "corpus-id", "score"], "unexpected qrels header"
    assert len(qrels_rows) == 5, f"expected 4 qrels rows plus header, got {len(qrels_rows)}"
    assert {row["_id"] for row in queries} == {"genQ1", "genQ2", "genQ3", "genQ4"}
    assert {row[2] for row in qrels_rows[1:]} == {"1"}


def assert_expansion_outputs(output_dir):
    corpus_path = output_dir / "gen-corpus.jsonl"
    assert corpus_path.is_file(), f"missing expanded corpus: {corpus_path}"

    rows = read_jsonl(corpus_path)
    assert len(rows) == 2, f"expected 2 expanded corpus rows, got {len(rows)}"
    by_id = {row["_id"]: row for row in rows}
    assert "expanded terms for Relativity" in by_id["doc1"]["text"]
    assert "expanded terms for Wheat beer" in by_id["doc2"]["text"]
    assert by_id["doc1"]["title"] == "Relativity"


def run_smoke(output_dir):
    corpus = tiny_corpus()

    query_generator = QueryGenerator(model=FakeQueryModel())
    query_generator.generate(
        corpus=corpus,
        output_dir=str(output_dir),
        ques_per_passage=2,
        prefix="gen",
        batch_size=1,
        save_after=2,
    )
    assert_query_outputs(output_dir)

    multiprocess_output_dir = output_dir / "multi-process"
    pool = {"processes": ["fake-worker"], "input": [], "output": []}
    QueryGenerator(model=FakeQueryModel()).generate_multi_process(
        corpus=corpus,
        pool=pool,
        output_dir=str(multiprocess_output_dir),
        ques_per_passage=2,
        prefix="gen",
        batch_size=1,
        chunk_size=1,
    )
    assert pool["calls"] == 1, "fake multi-process model was not called"
    assert_query_outputs(multiprocess_output_dir)

    PassageExpansion(model=FakePassageExpansionModel()).expand(
        corpus=corpus,
        output_dir=str(output_dir),
        prefix="gen",
        batch_size=1,
        top_k=3,
        max_length=16,
    )
    assert_expansion_outputs(output_dir)


def parse_args():
    parser = argparse.ArgumentParser(description="Run a no-download BEIR generation smoke test.")
    parser.add_argument(
        "--keep-output",
        metavar="DIR",
        help="write smoke outputs to DIR and keep them for inspection",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.keep_output:
        output_dir = Path(args.keep_output).expanduser().resolve()
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True)
        run_smoke(output_dir)
        print(f"BEIR generation smoke outputs written to {output_dir}")
        return

    with tempfile.TemporaryDirectory(prefix="beir-generation-smoke-") as tmp_dir:
        run_smoke(Path(tmp_dir))
    print("BEIR generation smoke test passed")


if __name__ == "__main__":
    main()
