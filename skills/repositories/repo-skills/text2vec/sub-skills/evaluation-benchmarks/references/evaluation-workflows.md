# Evaluation workflows

Use this reference to plan bounded evaluations and summarize existing scores. Full benchmark execution can download models and datasets; prefer local summaries when the user already has predictions.

## Evidence distilled into this reference

- `compute_spearmanr` and `compute_pearsonr` are the repo's primitive correlation metrics.
- `model_spearman.py` shows the local benchmark pattern: score aligned sentence pairs, compute Spearman per dataset, then average selected datasets.
- `eval_MTEB.py` and `eval_C-MTEB.py` show full MTEB / C-MTEB planning: enumerate tasks, handle retrieval instructions, and write one result JSON per task.
- `summarize_results.py` shows how MTEB/C-MTEB task JSON files are aggregated by task type and model.
- `test_qps.py` shows local throughput measurement, not a portable performance guarantee.

## Workflow 1: summarize local pair-score files

Use this when a model has already produced one score per gold-labeled pair and you only need Spearman/Pearson.

Input must be CSV or JSONL with at least:
- one numeric gold label column;
- one numeric predicted-score column.

Run the bundled helper:

```bash
python scripts/summarize_scores.py \
  --input-file pair_scores.csv \
  --label-column label \
  --score-column score \
  --output-file score_summary.json
```

The script does not load models or download data. It uses `scipy` if available, falls back to text2vec's metric helpers if importable, and otherwise uses a local deterministic implementation.

The JSON report includes:
- `spearman`: rank correlation, the primary metric used by the source release tables;
- `pearson`: linear correlation, useful for calibration checks;
- row counts, skipped-row examples, metric backend, and min/max ranges.

Use this workflow for the difficult case: "I have local pair-score CSV/JSONL and want Spearman/Pearson without running MTEB." It is the fastest safe path.

## Workflow 2: local benchmark interpretation

The local benchmark pattern is:

1. Prepare paired examples with `sentence1`, `sentence2`, and a numeric label.
2. Produce exactly one prediction score per pair. Avoid accidentally evaluating a full cross-product matrix.
3. Compute Spearman between predictions and labels.
4. Report per-dataset results, then average only the datasets that were actually evaluated.

Common local benchmark families in the release evidence are ATEC, BQ, LCQMC, PAWSX, STS-B, SOHU-dd, and SOHU-dc. These datasets have different domains and label distributions; do not compare a score from one dataset directly to a score from another dataset as if they had the same meaning.

Skip conditions:
- if a dataset file is missing, skip that dataset and list it as unavailable;
- if labels are malformed or nonnumeric, fix or filter them before computing metrics;
- if all labels or all scores are constant, Spearman/Pearson are undefined and should be reported as unavailable rather than zero.

## Workflow 3: bounded MTEB / C-MTEB planning

Full benchmark runs are expensive because they can require `mteb`, `C_MTEB`, task dataset downloads, model downloads, and GPU/large-CPU time.

Plan before running:

| Decision | Guidance |
|:--|:--|
| Language | English MTEB uses English tasks; C-MTEB uses Chinese / zh-CN tasks. Do not merge the task lists without saying so. |
| Task type | Retrieval, STS, pair classification, reranking, clustering, summarization, and classification use different main metrics. |
| Dataset availability | If network/cache access is unavailable, skip the task and record why. Do not extrapolate missing benchmark results. |
| Model cache | A model ID that is not cached may trigger a model download. Confirm the user accepts that cost. |
| Query instructions | Retrieval/reranking tasks may require query instruction prefixes for BGE-style models. Keep the instruction choice fixed when comparing models. |
| Normalization | The source English MTEB runner disables normalization for some task families; the Chinese runner can use normalized embeddings. Do not compare runs with different normalization flags as identical. |
| Output shape | Per-model directories should contain one JSON file per task, with split keys such as `test`, `dev`, or `validation` and language keys such as `en`, `en-en`, `zh`, or `zh-CN`. |

Known skip examples from the evidence:
- `MSMARCOv2` was skipped because it has no test split;
- Chinese evaluation filtered to tasks recognized by the Chinese benchmark task list;
- retrieval tasks changed query-instruction handling by model family.

## Workflow 4: summarize benchmark result directories

The source result summarizer groups result JSON by task type and model name, then averages only tasks with present results.

When creating or consuming summary tables:
- preserve the model directory names so rows can be traced to a model;
- record missing task JSON explicitly;
- use the benchmark's `main_score` where available;
- use `cos_sim.spearman` for cosine Spearman tasks and average precision for AP tasks;
- report language and task-family filters in the table title or notes.

## Workflow 5: QPS / throughput interpretation

QPS is a throughput measurement, not a semantic-quality metric.

Use QPS only when device, batch size, sequence length, model family, precision, and implementation are the same. The release table states its GPU QPS environment as Tesla V100 with 32GB memory, so CPU, MPS, consumer GPU, and multi-GPU numbers are not directly comparable.

For production search or dedup scale, choose/evaluate the model here, then route search-system mechanics to the separate `similarities` package or the `similarity-search` sub-skill.
