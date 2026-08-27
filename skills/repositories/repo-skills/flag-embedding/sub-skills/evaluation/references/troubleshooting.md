# Troubleshooting

Use this reference for evaluation-specific failures. For broad FlagEmbedding import problems, Python/package mismatches, or backend setup questions, route to the root troubleshooting reference.

## `faiss` Or `pytrec_eval` Missing

Symptoms:

- `ModuleNotFoundError: No module named 'faiss'`
- `ModuleNotFoundError: No module named 'pytrec_eval'`
- `python -m FlagEmbedding.evaluation.custom --help` fails before showing help.

Cause: evaluation utilities import both dependencies at module import time. They are not safe to postpone until metric computation.

Fix for CPU evaluation:

```shell
python -m pip install faiss-cpu pytrec_eval
python -m FlagEmbedding.evaluation.custom --help
```

Use a GPU Faiss build only when the environment is already prepared for that CUDA stack. Avoid installing CPU and GPU Faiss variants into the same environment unless the package manager explicitly supports that combination.

## Dataset Layout Errors

Symptoms:

- `Corpus not found ... Trying to download the corpus from the remote`
- `Qrels not found ... Trying to download the qrels from the remote`
- `Queries not found ... Trying to download the queries from the remote`
- `Split <name> not found in the dataset`

Checks:

- `--dataset_dir` must point at the directory containing `corpus.jsonl`, `<split>_queries.jsonl`, and `<split>_qrels.jsonl` for custom evaluation.
- The split in `--splits` must match the file prefix. `--splits dev` requires `dev_queries.jsonl` and `dev_qrels.jsonl`.
- For custom evaluation, do not pass `--dataset_names`; the custom loader has no dataset-name registry.
- For official benchmark loaders with local files, each `--dataset_names` value is expected as a child directory under `--dataset_dir`.

Use the bundled tiny fixture generator to compare a known-good layout:

```shell
python scripts/create_tiny_retrieval_dataset.py --output-dir ./tiny_retrieval --overwrite
```

## Download And Cache Surprises

Official benchmark modules can download corpora, queries, qrels, benchmark metadata, and models. Network use can happen when `--dataset_dir` is omitted, files are missing, `--force_redownload True` is set, or the selected external benchmark package needs task data.

Controls:

- Set `--dataset_dir` to a populated local directory when possible.
- Set `--cache_path` for datasets and `--cache_dir` for models. AIR-Bench uses `--cache_dir` for benchmark data and `--model_cache_dir` for models.
- Leave `--force_redownload False` unless the user explicitly wants refreshed data.
- Ask before enabling `--trust_remote_code` or downloading gated/private resources.

## Metrics Missing From Output

Symptoms:

- The aggregate markdown has `-` in metric cells.
- The requested metric is absent from `eval_results.json`.

Checks:

- `--eval_metrics` controls which metrics are displayed, not necessarily which metrics are computed.
- `--k_values` controls metric cutoffs. Requesting `recall_at_100` requires `--k_values 100`.
- Generic retrieval metrics include names such as `ndcg_at_10`, `map_at_10`, `recall_at_10`, `precision_at_10`, `mrr_at_10`, and `recall_cap_at_10`.
- MKQA uses QA recall metrics such as `qa_recall_at_20`.
- MTEB writes its own JSON aggregate and does not follow the markdown output path used by the base evaluator.

## Reranker Top-K Problems

Symptoms:

- Reranking is slower than expected.
- Reranker output has fewer candidates than expected.
- A reranker command runs out of memory.

Checks:

- `--search_top_k` is the first-stage retrieval cutoff.
- `--rerank_top_k` truncates first-stage results before scoring query-document pairs.
- Keep `--rerank_top_k <= --search_top_k`.
- Lower `--reranker_batch_size` or `--reranker_max_length` for memory pressure.
- If the reranker checkpoint is custom or not auto-mapped, set `--reranker_model_class`.

## Identical Query And Document IDs

`--ignore_identical_ids True` drops hits where `qid == docid`. This is useful for datasets where queries are derived from documents and self-retrieval is invalid.

Do not enable it automatically. Some benchmarks use id spaces where identical ids are meaningful or where the loader expects them to remain. The MIRACL path warns against enabling identical-id filtering.

When in doubt, inspect a few qids and docids before deciding:

```shell
head -n 3 test_queries.jsonl
head -n 3 corpus.jsonl
```

## Reusing Corpus Embeddings Gives Wrong Results

The saved corpus embedding file reflects the embedder, checkpoint, instructions, pooling, normalization, truncation, and corpus text at the time it was created. If any of those change, use a new `--corpus_embd_save_dir` or rerun with `--overwrite True`.

## Official Benchmark Scope Too Broad

If `--dataset_names`, `--tasks`, `--task_types`, or language selectors are omitted, a benchmark runner may evaluate every available item. For exploratory work, always pass a narrow selector and small split first.
