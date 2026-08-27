---
name: evaluation
description: "Evaluate FlagEmbedding embedders and optional rerankers on local
  retrieval data or supported benchmarks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# FlagEmbedding Evaluation

Use this sub-skill when a task needs FlagEmbedding evaluation commands, custom retrieval JSONL preparation, metric/output selection, or benchmark routing for MTEB, BEIR, MSMARCO, MIRACL, MLDR, MKQA, AIR-Bench, or BRIGHT.

Do not use this sub-skill for low-level embedder or reranker API details; route those to sibling `inference`. Do not use it for training or fine-tuning data preparation; route those to sibling `fine-tuning`. Broad package install, backend, or import troubleshooting belongs to the root `troubleshooting` reference.

## First Decision

1. For local retrieval data with `corpus.jsonl`, `<split>_queries.jsonl`, and `<split>_qrels.jsonl`, prefer `python -m FlagEmbedding.evaluation.custom`.
2. For local data stored in multiple subdirectories, run the custom module once per subdirectory with its own `--dataset_dir`, `--output_dir`, `--corpus_embd_save_dir`, and `--eval_output_path`. The custom loader reports no dataset names, so do not use `--dataset_names` for this case.
3. For official benchmark names or languages, choose the benchmark module from `references/cli-reference.md` and confirm network, model-cache, and compute approval before running.
4. If the user wants only schema validation or a smoke fixture, create a tiny dataset with `scripts/create_tiny_retrieval_dataset.py` before building a model command.

## Operating Procedure

1. Confirm dependencies for the selected path. All dense retrieval evaluation paths import `faiss` and `pytrec_eval`; the focused CPU dependency set is `faiss-cpu` plus `pytrec_eval`.
2. Check the data layout against `references/data-formats.md`. For custom evaluation, use the generic IR schema with corpus `id`, optional `title`, `text`; query `id`, `text`; qrels `qid`, `docid`, `relevance`.
3. Build the command from `references/cli-reference.md`. Always make output paths explicit: `--output_dir`, `--eval_output_path`, and, when reusing corpus embeddings, `--corpus_embd_save_dir`.
4. Decide `--ignore_identical_ids` deliberately. Use it when query ids and document ids share an id namespace and self-hits are invalid; leave it false for datasets where identical ids are meaningful or when unsure.
5. If adding a reranker, set `--reranker_name_or_path`, choose `--reranker_model_class` for custom checkpoints, and keep `--rerank_top_k` no larger than `--search_top_k`.
6. After execution, inspect both raw search result JSON under `--output_dir` and the aggregate file at `--eval_output_path`.

## Verification Hooks

- Safe help check: `python -m FlagEmbedding.evaluation.custom --help`.
- Loader fact check: `CustomEvalDataLoader.available_dataset_names()` returns `[]`; `available_splits()` returns `["test"]`.
- Fixture check: `python scripts/create_tiny_retrieval_dataset.py --help` and a run that writes `corpus.jsonl`, `test_queries.jsonl`, and `test_qrels.jsonl`.
- Official benchmark shell flows are reference candidates only. Treat them as network and compute dependent, not safe defaults.

## References

- `references/cli-reference.md`: module commands, shared arguments, and benchmark-specific notes.
- `references/data-formats.md`: local JSONL schema and output structure.
- `references/troubleshooting.md`: dependency, layout, cache, metrics, reranker, and identical-id issues.
- `scripts/create_tiny_retrieval_dataset.py`: tiny self-contained custom retrieval fixture generator.
