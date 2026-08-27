---
name: indexing-and-search
description: "Build ColBERT indexes, load existing indexes, run single-query and
  batch retrieval, tune search hyperparameters, and save rankings safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ColBERT Indexing and Search

Use this sub-skill when the task is to turn a TSV passage collection into a ColBERT index, open an existing ColBERT index, retrieve top-k passages for one query or many queries, tune retrieval speed/quality settings, validate collection/query/ranking inputs, or diagnose index path and ranking-output issues.

## Route the task

- For public imports, verified signatures, path resolution, return shapes, overwrite modes, and CPU/GPU behavior, read `references/api-reference.md`.
- For copy-editable indexing, existing-index loading, single-query search, batch search, ranking save, `index_root`, mmap, and tuning workflows, read `references/index-search-workflows.md`.
- For checkpoint, optional dependency, backend, TSV/config, API misuse, overwrite, `qid_to_pids`, and output-location failures, read `references/troubleshooting.md`.
- For deterministic preflight checks of user-provided collection, query, and ranking TSV files before expensive ColBERT runs, use `scripts/validate_colbert_inputs.py`.
- For an editable minimal script that exposes `index`, `search`, and `search-all` subcommands with public ColBERT APIs, adapt `scripts/minimal_index_search_template.py`.

## Core boundaries

- Cover `Indexer`, `Searcher`, `Run`, `RunConfig`, `ColBERTConfig`, `Collection`, `Queries`, `Ranking`, `index_root`, overwrite/reuse/resume, `load_index_with_mmap`, and `ncells`/`ndocs` search tuning.
- Keep training, distillation, triples, and checkpoint training workflows in `../training-and-distillation/`.
- Keep TSV/qrels/evaluation details beyond basic indexing/search I/O in `../data-and-evaluation/`.
- Keep mutable add/remove/persist index serving workflows in `../index-updates-and-serving/`.
- Keep tokenizer internals, checkpoint architecture, and model compatibility analysis in `../modeling-and-tokenization/`.

## Fast starting point

1. Validate TSV shapes before expensive work: `python scripts/validate_colbert_inputs.py --collection collection.tsv --queries queries.tsv`.
2. Index with explicit `checkpoint`, `root`, `experiment`, `index_name`, and overwrite policy.
3. Search by reusing the same `root`, `experiment`, and `index_name`, or pass explicit `index_root` when the index is outside the default layout.
4. Save batch results with `Ranking.save(...)`; use an absolute output path or print the returned path because relative paths are resolved by the active `Run` context.

## Verified package facts

- Distribution: `colbert-ai` 0.2.22; import package: `colbert`.
- Verified imports include `colbert`, `colbert.infra`, `colbert.data`, `colbert.modeling.checkpoint`, `utility`, and `baleen`.
- CPU import inspection works, but practical indexing and training usually require CUDA/GPU; CPU search is possible and mmap search is CPU-only.
- Important signatures: `Indexer(checkpoint, config=None, verbose=3)`, `Searcher(index, checkpoint=None, collection=None, config=None, index_root=None, verbose=3)`, `Collection(path=None, data=None)`, `Queries(path=None, data=None)`, and `Ranking(path=None, data=None, metrics=None, provenance=None)`.
