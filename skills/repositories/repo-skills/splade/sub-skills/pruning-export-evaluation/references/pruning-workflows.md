# Pruning Workflows

SPLADE static pruning operates on Anserini-style document JSONL created by `python -m splade.create_anserini`. The bundled scripts in this sub-skill adapt the original pruning utilities so future agents can prune explicit input directories without relying on a repository-local `data/<name>/base_index` layout.

## Expected Input Layout

Use a directory containing one or more `.jsonl` or `.jsonl.gz` files. Each non-empty line must be a JSON object with at least:

```json
{"id": "doc-1", "vector": {"token_a": 120, "token_b": 8}}
```

Additional fields such as `content` are preserved. Output files keep the same filenames and compression style unless a script-specific output path says otherwise.

## Top-k and Value Pruning

Use `scripts/prune_doc_index.py` when pruning each document independently.

Top-k pruning keeps the highest weighted tokens per document:

```bash
python scripts/prune_doc_index.py \
  --input-dir anserini_export \
  --output-dir pruned_top8 \
  --top-k 8
```

Value pruning keeps tokens whose integer impact is greater than a threshold. To mirror the original SPLADE pruning script, use `--value-to-prune`, where the actual integer threshold is `value_to_prune * --value-scale`. The default `--value-scale 100` preserves the original script's `value_to_prune * 100` behavior:

```bash
python scripts/prune_doc_index.py \
  --input-dir anserini_export \
  --output-dir pruned_value_075 \
  --value-to-prune 0.75
```

For already-integer thresholding, set `--value-scale 1`:

```bash
python scripts/prune_doc_index.py \
  --input-dir anserini_export \
  --output-dir pruned_gt10 \
  --value-to-prune 10 \
  --value-scale 1
```

The script can write top-k and value outputs in one invocation with separate subdirectories:

```bash
python scripts/prune_doc_index.py \
  --input-dir anserini_export \
  --output-dir pruned \
  --top-k 16 \
  --value-to-prune 1.0
```

This creates `pruned/prune_size_16/` and `pruned/prune_value_1.0/`.

## Quantile Pruning

Use `scripts/prune_quantile.py` when pruning by per-token global quantiles. The script scans all input vectors, computes a quantile threshold for each token, then keeps values strictly greater than that token's threshold:

```bash
python scripts/prune_quantile.py \
  --input-dir anserini_export \
  --output-dir pruned_quantile_085 \
  --quantile 0.85
```

Quantile pruning is token-specific. A rare token and a common token can receive different thresholds because thresholds are computed over each token's observed values.

## Safe Preview Options

Both scripts support:

- `--dry-run`: validate inputs and report planned writes without writing output files;
- `--limit N`: process only the first `N` records across input files, useful for tiny fixture checks;
- `.jsonl.gz`: read and write gzip-compressed JSONL when filenames end in `.gz`.

Run `--help` before using the scripts on large exports.

## Preserved Semantics

The bundled scripts preserve these source semantics:

- records remain JSONL objects;
- `id`, `content`, and any other non-`vector` fields are preserved;
- `vector` remains a mapping from token string to numeric impact;
- value and quantile pruning keep weights strictly greater than the threshold, not greater-or-equal;
- top-k pruning sorts by descending weight and keeps the first `k` tokens.

The scripts intentionally add validation around malformed records, missing vectors, non-numeric weights, output collisions, and explicit input/output directories.

## Reference-only Shell Workflows

The original shell workflow family is intentionally not bundled as executable runtime scripts:

| Workflow family | Why it is reference-only |
| --- | --- |
| run-all orchestration shell | creates hardcoded folders and chains pruning, indexing, and retrieval against local data names |
| Anserini/Pyserini indexing shells | require Pyserini/Anserini, Java, disk-heavy Lucene indexes, and pre-existing export folders |
| Anserini/Pyserini query shells | require Anserini indexes, query TSV files, external qrels, and `ir_measures` |
| fixed-value pruning loop shells | only loop fixed pruning values over repository-local folder names; the bundled Python scripts replace the reusable local pruning part |

When the user wants the full pruning/index/retrieve/evaluate pipeline, first produce a plan: identify input export directory, pruning variants, Pyserini installation, Java version, qrels/topics, output run path, expected metrics, and whether downloads or external engines are approved.

## Common Pruning Variants

Original pruning studies used examples like:

- top-k sizes: `4`, `8`, `16`, `32`, `64`;
- value thresholds: `0.5`, `0.75`, `1.0`, `1.25` with scale `100`;
- quantiles: `0.5`, `0.75`, `0.85`.

These values are not universally optimal. Treat them as reproducibility anchors and ask for the target effectiveness/efficiency trade-off before pruning production exports.
