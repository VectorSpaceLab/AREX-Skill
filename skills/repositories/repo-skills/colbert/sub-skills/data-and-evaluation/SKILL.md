---
name: data-and-evaluation
description: "Use when preparing or validating ColBERT
  collection/query/ranking/qrels/LoTTE data, evaluating MSMARCO-style or LoTTE
  rankings, converting documents into passage TSVs, or troubleshooting
  data-format utility workflows. Excludes running retrieval, index updates, and
  training mechanics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ColBERT Data and Evaluation

Use this sub-skill when a task is about ColBERT data artifacts rather than model execution:

- Prepare or validate `collection.tsv`, `queries.tsv`, `ranking.tsv`, qrels, LoTTE QA JSONL, or tiny fixtures.
- Read, write, or reason about `Collection`, `Queries`, and `Ranking` objects.
- Evaluate MSMARCO-style rankings with `MRR@10` and `Recall@k`.
- Evaluate or debug LoTTE-style `Success@k` layouts and ranking files.
- Adapt preprocessing workflows such as converting document TSV rows into passage TSV rows.
- Split, merge, inspect, or annotate ranking files before downstream evaluation.

For retrieval that creates rankings from an index, route to `indexing-and-search`. For training triples, hard-negative distillation, or trainer input validation beyond basic file shape, route to `training-and-distillation`.

## Quick Start

Validate core files before indexing, searching, training, or evaluation:

```bash
python scripts/validate_colbert_data.py --collection collection.tsv --queries queries.tsv --ranking ranking.tsv --qrels qrels.tsv
```

Require LoTTE-compatible scored rankings and QA JSONL:

```bash
python scripts/validate_colbert_data.py --ranking writing.search.ranking.tsv --lotte-qas qas.search.jsonl --require-score --require-sequential-qids
```

Convert document TSV rows into a standard passage collection with deterministic whitespace splitting:

```bash
python scripts/prepare_collection_tsv.py --input documents.tsv --output collection.tsv --format docid,text --nwords 100 --overlap 20
```

Evaluate a tiny or full MSMARCO-style ranking without importing ColBERT:

```bash
python scripts/evaluate_tiny_ranking.py --qrels qrels.tsv --ranking ranking.tsv --depths 10 50 100
```

Evaluate a tiny LoTTE-style QA/ranking pair:

```bash
python scripts/evaluate_tiny_ranking.py --lotte-qas qas.search.jsonl --ranking ranking.tsv --success-at 5
```

## References and Scripts

- `references/data-formats.md` explains TSV, qrels, JSONL QA, LoTTE layout, and tiny fixture conventions; use it before creating or converting data files.
- `references/api-reference.md` summarizes `Collection`, `Queries`, and `Ranking` behavior; use it when writing Python code against ColBERT data wrappers.
- `references/evaluation-and-rankings.md` explains MSMARCO evaluation, LoTTE Success@k, annotation, split/merge helpers, and ranking utility adaptations.
- `references/troubleshooting.md` maps common data/config/API/workflow failures to checks and fixes; use it when validation or native utilities fail.
- `scripts/validate_colbert_data.py` performs deterministic local validation of collection/query/ranking/qrels/LoTTE files without Torch, FAISS, CUDA, or ColBERT imports.
- `scripts/prepare_collection_tsv.py` converts document TSV rows into ColBERT passage TSV rows with safe whitespace splitting and optional mapping columns.
- `scripts/evaluate_tiny_ranking.py` computes fixture-friendly MSMARCO-style metrics or LoTTE Success@k and can write annotated ranking rows.

## Operating Notes

- ColBERT package imports verified for `colbert`, `colbert.infra`, `colbert.data`, `colbert.modeling.checkpoint`, `utility`, and `baleen`; CPU import checks work, but indexing/training usually require CUDA/GPU.
- The public package is `colbert-ai` and the verified distribution version is `0.2.22`; import the package as `colbert`.
- Core data signatures are `Collection(path=None, data=None)`, `Queries(path=None, data=None)`, and `Ranking(path=None, data=None, metrics=None, provenance=None)`.
- Retrieval APIs produce rankings through `Searcher(index, checkpoint=None, collection=None, config=None, index_root=None, verbose=3)`, but retrieval execution belongs in the indexing/search sub-skill.
- Native utilities often assert that output paths do not already exist; decide overwrite/delete policy before long runs.
