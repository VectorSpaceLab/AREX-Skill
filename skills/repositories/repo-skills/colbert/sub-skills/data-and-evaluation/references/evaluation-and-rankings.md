# Evaluation and Ranking Workflows

This reference covers ColBERT ranking evaluation and utility workflows. It focuses on file contracts and lightweight reproductions rather than GPU retrieval or training.

## MSMARCO Passage Evaluation

MSMARCO-style evaluation compares qrels against a ranking TSV.

Inputs:

- `qrels.tsv`: whitespace-separated `qid 0 pid 1` rows.
- `ranking.tsv`: tab-separated `qid<TAB>pid<TAB>rank[<TAB>score]` rows.

Metric behavior:

- `MRR@10`: for each judged qid, use the reciprocal rank of the first positive pid if it appears in ranks 1 through 10; otherwise use `0`.
- `Recall@k`: for each judged qid, sum `1 / number_of_positives` for each positive pid retrieved within depth `k`.
- The denominator is the number of judged qids, not only ranked qids.
- The native utility warns when the number of judged qids differs from the number of ranked qids.
- The native utility asserts that ranking qids are a subset of qrels qids.

Fixture-safe evaluation:

```bash
python scripts/evaluate_tiny_ranking.py --qrels qrels.tsv --ranking ranking.tsv --depths 10 50 200 1000
```

Optional annotation output:

```bash
python scripts/evaluate_tiny_ranking.py --qrels qrels.tsv --ranking ranking.tsv --annotate annotated.tsv
```

Annotation rows are:

```text
qid<TAB>pid<TAB>rank<TAB>score<TAB>label
```

When the source ranking has no score column, the annotation row omits score and writes `qid<TAB>pid<TAB>rank<TAB>label`.

## LoTTE Success@k Evaluation

LoTTE evaluation checks whether any retrieved passage in the top `k` appears in a QA line's `answer_pids`.

Required data layout:

```text
<data-dir>/<dataset>/<split>/qas.<query-type>.jsonl
```

Required ranking layout:

```text
<rankings-dir>/<split>/<dataset>.<query-type>.ranking.tsv
```

Common values:

- `split`: `dev` or `test`
- `query-type`: `search` or `forum`
- `dataset`: `writing`, `recreation`, `science`, `technology`, `lifestyle`, `pooled`

Ranking constraints:

- Rows are `qid<TAB>pid<TAB>rank<TAB>score`.
- Qids are integer ids matching QA rows.
- Ranks must be sequential and 1-indexed for each qid.
- Native documentation notes qids should be sequential from `0`; this is especially important for complete benchmark exports.
- Missing qids lower Success@k and should be reported.

Minimal Success@k logic:

```text
success(qid) = bool(set(top_k_pids_for_qid) intersects set(answer_pids_for_qid))
Success@k = 100 * successes / number_of_qas
```

Tiny LoTTE check:

```bash
python scripts/evaluate_tiny_ranking.py --lotte-qas qas.search.jsonl --ranking writing.search.ranking.tsv --success-at 5
```

## Exact-Match Annotation

Exact-match annotation joins a QA file, collection, and ranking file, then labels ranked passages by whether they contain an answer string after tokenization and normalization.

Operational cautions:

- It can be CPU-heavy because answer tokenization and passage labeling are parallelized.
- Native output paths append `.annotated` and `.annotated.metrics` to the ranking path.
- The utility asserts annotation output paths do not already exist.
- QA schema, collection PIDs, and ranking PIDs must be aligned before launching annotation.

## Ranking Split and Merge Helpers

### Merge Scored Rankings

Use when separate ranking shards for the same qids must be combined by score.

Input rows must have scores:

```text
qid<TAB>pid<TAB>rank<TAB>score
```

Workflow:

1. Load one or more ranking files.
2. Group rows by qid.
3. Sort each qid's candidate rows by descending score.
4. Rewrite 1-indexed ranks.
5. Optionally truncate to `depth`.

Cautions:

- Score must parse as float.
- Ties use tuple ordering, so behavior is deterministic but not necessarily semantically meaningful.
- Validate there are no duplicate `(qid, pid)` rows unless duplicate candidates are intentional.
- Output paths usually assert no overwrite.

### Split by Query Source

Use when a merged query set was searched and ranking rows need to be routed back to original query files.

Two patterns exist:

- Split by query membership: build a qid-to-source map from query TSV files, then write `ranking.tsv.0`, `ranking.tsv.1`, etc.
- Split by offset: use large qid gaps such as `1_000_000_000`, then convert qids back with modulo arithmetic.

Cautions:

- Query IDs must be unique across source files for membership splitting.
- Offset splitting assumes qids were intentionally offset before retrieval.
- Both patterns assert outputs do not already exist.

### Query Splitting and Subsampling

Use deterministic splitting for development/holdout checks and sampled QA evaluations.

Cautions:

- Source utilities use fixed random seeds for reproducible samples.
- Query IDs must remain aligned with qrels, QA files, and rankings after splitting.
- If a ranking is split after query splitting, validate every output subset independently.

### Tune Checkpoint Selection

Use when many metrics JSON files correspond to checkpoints and one metric path should select the best checkpoint.

Workflow:

1. Load each metrics JSON.
2. Follow a dotted metric key such as `success.20`.
3. Pick the path with the highest float score.
4. Resolve the checkpoint path from logs metadata.
5. Write selected checkpoint path plus metadata.

Cautions:

- This is a model-selection helper, not an evaluator.
- Metric JSON nesting must match the requested dotted key.
- Output files assert no overwrite.

## Validation Checklist

Before calling a native evaluator or helper, check:

- TSV rows have expected column counts.
- Qids and pids parse as integers where the utility expects integers.
- Ranks are sequential and start at `1` within each qid.
- Every ranked qid is present in qrels or QA data.
- PIDs in ranking rows exist in the collection when a collection file is available.
- Optional score columns are consistently present when required.
- Output files do not already exist unless the tool explicitly supports overwrite.
