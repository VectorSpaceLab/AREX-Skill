# Data and Evaluation Troubleshooting

## Install and Import Failures

Symptoms:

- `ModuleNotFoundError: No module named 'colbert'`.
- Importing `utility.evaluate...` fails in a fresh environment.
- Torch imports on CPU but GPU-backed indexing or training fails later.

Checks:

- The package distribution is `colbert-ai`; import it as `colbert`.
- Verified imports include `colbert`, `colbert.infra`, `colbert.data`, `colbert.modeling.checkpoint`, `utility`, and `baleen`.
- Data validation scripts in this sub-skill are self-contained and do not import ColBERT, Torch, FAISS, or CUDA libraries.

Fix:

- Use bundled scripts for data checks in minimal environments.
- Prepare a proper ColBERT environment before running native retrieval, indexing, or training.
- Treat CUDA/GPU issues as execution-skill problems after data files validate cleanly.

## Optional Dependency Failures

Symptoms:

- `jsonlines` import fails while evaluating LoTTE with the native utility.
- WordPiece preprocessing tries to download `bert-base-uncased` tokenizer assets.
- `ujson` import fails in direct wrapper usage.

Checks:

- Native LoTTE evaluation imports `jsonlines`.
- Native document preprocessing imports Hugging Face Transformers only when WordPiece mode is requested.
- The bundled scripts use only the Python standard library.

Fix:

- Use `scripts/evaluate_tiny_ranking.py --lotte-qas ...` for tiny LoTTE checks without `jsonlines`.
- Use whitespace passage splitting unless WordPiece parity is required.
- If WordPiece parity is required, provision tokenizer assets and document that dependency for the target environment.

## TSV Column Errors

Symptoms:

- `ValueError` while unpacking columns.
- Empty qids or pids.
- Ranking rows parse incorrectly.
- Collection conversion drops many rows as ill-formatted.

Checks:

- Collections and queries should have exactly two tab-separated columns for standard ColBERT use.
- Rankings should have three or four tab-separated columns.
- MSMARCO qrels should have four whitespace-separated columns.
- Normalize tabs and newlines inside text before writing TSV rows.

Fix:

```bash
python scripts/validate_colbert_data.py --collection collection.tsv --queries queries.tsv --ranking ranking.tsv --qrels qrels.tsv
```

## Rank Starts at 0 or Skips Values

Symptoms:

- LoTTE evaluator assertion failure.
- Metrics differ from expected tiny fixtures.
- A top result appears as rank `0`.
- A merged ranking has ranks like `1, 3, 4`.

Cause:

- ColBERT ranking/evaluation utilities expect ranks to start at `1` for each qid and proceed sequentially.

Fix:

- Rewrite ranks per qid in final sorted output order as `1, 2, 3, ...`.
- Do not use Python list indexes directly without adding `1`.
- Re-rank after merge/truncation, not before.

## Non-Sequential LoTTE Qids

Symptoms:

- LoTTE documentation says qids should start at `0`, but a partial file starts at an arbitrary qid.
- Native evaluation prints warnings for missing qids or reports misleading Success@k.
- Split/merged LoTTE rankings contain qids not present in QA JSONL.

Checks:

- Full LoTTE ranking exports should use integer qids aligned with QA rows and sequential from `0`.
- Partial tiny fixtures can be evaluated if qids match QA rows, but do not treat them as complete benchmark exports.
- Use `--require-sequential-qids` in `validate_colbert_data.py` when preparing official LoTTE-style files.

Fix:

- Renumber qids consistently across `questions.*.tsv`, `qas.*.jsonl`, and ranking files.
- Keep an external mapping from original IDs to sequential LoTTE qids when converting datasets.

## Duplicate or Missing Query IDs

Symptoms:

- `Queries` rejects JSON QA input.
- Split-by-query routing fails.
- Evaluation warns that judged and ranked query counts differ.
- Ranking qids are absent from qrels or QA JSONL.

Checks:

- Every qid appears once in `queries.tsv` or QA JSONL.
- Ranked qids are a subset of qrels or QA qids.
- Source query files have disjoint qids when splitting by query membership.

Fix:

- Deduplicate source queries before retrieval.
- Renumber or offset qids deliberately when merging query sets.
- Keep a mapping file when converting external dataset IDs to integer qids.

## PID Mismatches and Duplicate PIDs

Symptoms:

- Evaluation gives zero recall despite apparently relevant text.
- Exact-match annotation labels no positives.
- Validator reports ranking pids not present in collection.
- Collection conversion creates duplicate or shifted PIDs.

Checks:

- Ranking PIDs must refer to rows in the same collection used for retrieval/evaluation.
- `Collection(data=list).save(...)` re-enumerates PIDs from zero.
- Document-to-passage conversion creates passage IDs, not original document IDs, unless mapping columns are explicitly preserved.

Fix:

- Validate ranking PIDs against collection PIDs when collection files are available.
- Preserve source document IDs in a side mapping or optional output column for inspection, but feed standard two-column collections to ColBERT.
- Rebuild qrels over passage IDs after document-to-passage conversion.

## Missing Qrels Positives

Symptoms:

- Qrels validator rejects empty files or non-`1` labels.
- Metrics are zero for queries expected to have positives.
- Ranking qids exist but qrels has no matching positive pids.

Checks:

- Native MSMARCO utility expects qrels rows like `qid 0 pid 1`.
- Every evaluated query should have at least one positive PID.
- The ranking file may omit a judged qid; that lowers metrics because denominator is judged queries.

Fix:

- Regenerate qrels from the same collection PID space as the ranking.
- Remove queries from the evaluation set only if the benchmark definition allows it.

## Output Already Exists

Symptoms:

- Assertion error showing an output path.
- `Ranking.save()` writes the ranking but a sidecar collision or output collision breaks the run.
- Annotation, split, or merge jobs stop immediately.

Cause:

- Many ColBERT utilities assert no overwrite for safety.

Fix:

- Choose a new output path.
- Delete stale outputs only after confirming they are disposable.
- For bundled scripts, use `--overwrite` only when the command documents it.
- Remember `Ranking.save("x.tsv")` also writes `x.tsv.meta`.

## LoTTE Layout Problems

Symptoms:

- Success@k prints `???` for some datasets.
- QA file open errors.
- Ranking assertion failures.
- Partial LoTTE files look successful but cover only one domain or query type.

Checks:

- Data files follow `<data-dir>/<dataset>/<split>/qas.<query-type>.jsonl`.
- Ranking files follow `<rankings-dir>/<split>/<dataset>.<query-type>.ranking.tsv`.
- Dataset names match exactly: `writing`, `recreation`, `science`, `technology`, `lifestyle`, `pooled`.
- Query types match exactly: `search`, `forum`.
- Split is `dev` or `test`.

Fix:

- Rename files to expected names rather than passing alternate names to the native script.
- Validate ranking ranks are sequential per qid and require scores.
- Record partial-file status explicitly; do not report partial LoTTE output as full benchmark coverage.

## JSONL QA Schema Mismatch

Symptoms:

- Key errors for `qid`, `question`, `query`, or `answer_pids`.
- Empty `Queries.qas()` output.
- LoTTE Success@k sees no answer pids.

Checks:

- LoTTE-style QA uses `qid`, `query`, and `answer_pids`.
- `Queries` JSON loader expects `qid` and `question` for query text.
- Exact-match QA loaders may expect answer text fields, not just answer pids.

Fix:

- Convert QA files to the schema required by the specific workflow.
- Keep LoTTE QA JSONL separate from `Queries` QA JSON unless adapting field names.

## API Misuse

Symptoms:

- `Collection.cast`, `Queries.cast`, or `Ranking.cast` asserts on object type.
- Saving to a non-TSV ranking path fails.
- Ranking dictionaries flatten into unexpected tuple order.

Checks:

- `Collection.cast` accepts a path string, list, or `Collection`.
- `Queries.cast` accepts a path string, dict/list data, or `Queries`.
- `Ranking.cast` accepts a path string, dict/list data, or `Ranking`.
- `Ranking.save()` requires `tsv` in the final filename extension segments and writes a sidecar.

Fix:

- Convert custom objects to plain paths, dictionaries, or flat lists before calling wrappers.
- Prefer flat ranking tuples `(qid, pid, rank, score)` when preserving exact column order matters.
