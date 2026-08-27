# Data Loading Troubleshooting

## Missing Local Files

Symptom:

```text
ValueError: File ... not present! Please provide accurate file.
```

Likely causes and fixes:

- `data_folder` points one level too high or too low. The standard layout is `data_folder/corpus.jsonl`, `data_folder/queries.jsonl`, and `data_folder/qrels/<split>.tsv`.
- `split` does not match the qrels filename. `load(split="dev")` expects `qrels/dev.tsv`.
- `prefix` is set but files are unprefixed. `prefix="fiqa"` expects `fiqa-queries.jsonl` and `fiqa-qrels/<split>.tsv`.
- `prefix` is missing but files are prefixed. Either rename to `queries.jsonl` and `qrels/`, or pass the matching `prefix`.

Run the validator with the same split and prefix you plan to load:

```bash
python scripts/validate_beir_dataset.py ./my-dataset --split test --prefix fiqa
```

## Wrong Extensions

Symptom:

```text
ValueError: File ... must be present with extension jsonl
ValueError: File ... must be present with extension tsv
```

Fix:

- Use `.jsonl` for corpus and queries.
- Use `.tsv` for qrels.
- If the content is already correct but filenames differ, rename files or pass explicit `corpus_file`, `query_file`, and `qrels_file` paths to `GenericDataLoader(...).load_custom()`.

## Malformed JSONL

Symptoms:

- JSON decoder errors from BEIR or the bundled validator.
- Rows load with missing/`None` ids.
- Later qrels checks cannot find expected ids.

Fix:

- Keep exactly one JSON object per line.
- Use double-quoted JSON strings.
- Ensure every corpus row has `_id`, `title`, and `text`.
- Ensure every query row has `_id` and `text`.
- Make `_id` values non-empty strings and unique inside each file.

## Malformed Qrels TSV

Symptoms:

- Integer conversion failures for scores.
- Validator errors about header or column count.
- Loaded queries unexpectedly disappear.

Fix:

- The first row must be `query-id<TAB>corpus-id<TAB>score`.
- Each data row must have exactly three tab-separated fields.
- Use integer-compatible scores for `GenericDataLoader`, such as `0`, `1`, or `2`.
- Make every qrel query id exist in the query JSONL and every corpus id exist in corpus JSONL.

## Qrels Reference Missing Documents or Queries

Symptom from the bundled validator:

```text
qrels/test.tsv:4 corpus-id 'doc99' is not present in corpus
qrels/test.tsv:5 query-id 'q99' is not present in queries
```

Repair path:

1. Check whether the id is a typo in qrels.
2. If the id is correct, add the missing corpus or query row with matching `_id`.
3. If the judged item should be excluded, remove the qrels row and document why.
4. Re-run validation before retrieval or evaluation.

This is important because BEIR evaluation compares retrieval result ids against qrels ids; mismatched id universes create misleading zero scores or runtime failures.

## Prefix Path Surprises

Symptom:

- `GenericDataLoader(data_folder=..., prefix="x").load()` cannot find qrels even though `qrels/test.tsv` exists.

Cause:

- Prefix mode looks for `x-qrels/test.tsv`, not `qrels/test.tsv`.
- Prefix mode looks for `x-queries.jsonl`, not `queries.jsonl`.
- Prefix mode still looks for unprefixed `corpus.jsonl`.

Fix:

- Rename files/folders to match prefix mode, or remove `prefix`.
- Validate with `--prefix x` to see the exact paths before loading.

## Hugging Face Streaming vs Local Dict Behavior

Symptoms:

- Code expects `corpus.keys()` or `queries.items()` after `HFDataLoader`.
- Code fails when using `len()`, indexing, or repeated scans with `streaming=True`.

Fix:

- `GenericDataLoader` returns Python dictionaries.
- `HFDataLoader` returns Hugging Face Dataset-like objects for corpus and queries, with rows containing `id`, `text`, and optional `title`.
- For streaming mode, write iterable-friendly code or materialize a bounded subset explicitly before operations that require random access.
- If the downstream retriever requires plain BEIR dictionaries, use `GenericDataLoader` or convert HF rows into dictionaries carefully.

## Download, Network, and Archive Issues

Symptoms:

- Download stalls or fails.
- Extracted folder is missing expected files.
- Re-running does not refresh a corrupt zip.

Fix:

- Confirm network access and the dataset URL.
- `download_and_unzip()` skips download if the zip file already exists and skips extraction if the target folder already exists. Delete the corrupt zip/folder before retrying.
- Validate the extracted dataset with the bundled validator.
- BEIR's utility does not verify checksums; use an external checksum only when the data provider publishes one.
- Extract only trusted zip archives because `util.unzip()` extracts archive contents into the output directory.

## Runfile Format Issues

Symptoms:

- `util.load_runfile()` raises an unpacking error.
- Scores fail to parse as floats.
- Query or document ids are split unexpectedly.

Fix:

- Keep each row as exactly six space-separated fields: `qid Q0 docid 0 score run_name`.
- Avoid spaces in query ids, document ids, and run names.
- Ensure scores are numeric.
- If constructing a runfile manually, prefer `util.save_runfile()` to preserve sorting and column shape.

## Result JSON Issues

Symptoms:

- Metric JSON omits expected optional sections.
- Cutoff keys appear as strings after JSON load.

Fix:

- `save_results()` writes optional metrics only when their dictionaries are provided and truthy.
- JSON object keys are strings after loading; normalize keys before comparing across runs if your test expects integers.
