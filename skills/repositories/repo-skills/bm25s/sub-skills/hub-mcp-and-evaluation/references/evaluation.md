# BEIR-style evaluation and benchmark helpers

The public evaluation helpers are adapters around local BEIR-shaped files and
`pytrec_eval`. They do not make a dataset appear, choose a relevance policy,
or replace an experiment's acceptance criteria.

## Data flow

A safe evaluation flow is:

1. Start with a local corpus and query set whose IDs are strings and whose
   document IDs are the same IDs used by qrels.
2. Index document text with the same tokenizer/stemmer configuration used for
   queries. Retrieve using the document-ID list as the `corpus` argument when
   the result must be evaluated by IDs.
3. Convert the returned arrays with
   `postprocess_results_for_eval(results, scores, query_ids)`.
4. Load or construct qrels with the same query/document ID namespace.
5. Call `evaluate(qrels, result_dict, [1, 10], ...)` on a small local case
   before considering a larger benchmark.

The adapter expects `results` and `scores` in the same query order and
`query_ids` in that order. It creates a mapping of each query ID to document
IDs and floating-point scores. A score matrix without an ID mapping is not
sufficient evidence for BEIR metrics.

```python
from bm25s.utils.beir import postprocess_results_for_eval, evaluate

result_dict = postprocess_results_for_eval(
    results, scores, query_ids=["q-cat", "q-fish"]
)
ndcg, mean_ap, recall, precision = evaluate(
    qrels,
    result_dict,
    k_values=[1, 2],
)
print(ndcg, mean_ap, recall, precision)
```

`clean_results_keys(mapping)` strips everything through the last `@` in each
key. Use it only when an upstream evaluator returns keys such as
`NDCG@10` and the consumer needs the suffix-free form; do not apply it to
query IDs or document IDs.

## `evaluate` contract

`evaluate(qrels, results, k_values, ignore_identical_ids=True)` lazily imports
`pytrec_eval`. Install the `evaluation` extra or `pytrec_eval` if this route is
explicitly selected. The inputs are:

- `qrels`: `{query_id: {document_id: integer_relevance}}`.
- `results`: `{query_id: {document_id: float_score}}`.
- `k_values`: a non-empty list of cutoffs supported by the installed evaluator.
- `ignore_identical_ids`: defaults to `True`.

The return value is a four-tuple in this exact order:

```text
(ndcg, mean_average_precision, recall, precision)
```

Each item is a dictionary with keys `NDCG@k`, `MAP@k`, `Recall@k`, or `P@k`,
respectively. Values are rounded to five decimal places and averaged over
queries scored by `pytrec_eval`. Preserve these labels in reports; do not call
the second item “NDCG” or assume a scalar return.

With the default `ignore_identical_ids=True`, the implementation removes any
result where a query ID equals a document ID before evaluation and logs that
choice. It mutates the nested `results` mapping while doing so. Pass a copied
mapping when the original result dictionary must remain unchanged. Set the
flag to `False` only when identical IDs are valid for the task and that choice
is recorded.

A missing `pytrec_eval` raises an actionable `ImportError`. Missing or empty
scores/qrels, inconsistent IDs, unsupported cutoff syntax, or a zero-query
case are data/evaluator failures; stop and repair the fixture rather than
interpreting a partial metric. In particular, the averaging implementation
requires at least one evaluated query.

## Local loading helpers

The utility module provides local BEIR-shaped loaders:

| Helper | Contract |
| --- | --- |
| `load_corpus(dataset, save_dir="./datasets", ...)` | Reads `<save_dir>/<dataset>/corpus.jsonl`; returns an ID-keyed dict by default, removes `metadata`, and ensures a `title` key. |
| `load_queries(dataset, save_dir="./datasets", ...)` | Reads `queries.jsonl`; returns an ID-keyed dict by default and removes `metadata`. |
| `load_qrels(dataset, split="test", save_dir="./datasets", ...)` | Reads `qrels/<split>.tsv`; accepts only `train`, `dev`, or `test`; returns `{qid: {cid: score}}` by default. |
| `load_jsonl(dataset, fname, ...)` | Lower-level JSONL loader; can return a list with `return_dict=False`, force a title, and remove selected fields. |
| `merge_cqa_dupstack(data_path, ...)` | Merges a local `cqadupstack` directory and prefixes IDs with the corpus name. It is a data-preparation mutation. |

These helpers raise `FileNotFoundError` for missing expected files. The
corpus/query loader mutates each decoded record by removing `_id` when making
the default dictionary, so preserve a copy if the raw record is needed.
`load_qrels` skips the TSV header and parses integer relevance values.

## Dataset acquisition boundary

`download_dataset(dataset, base_url=..., save_dir="./datasets", unzip=True,
redownload=False, ...)` downloads a ZIP (or multipart release), extracts it,
and may merge CQADupStack files. It uses network access, writes to the target,
and can consume substantial disk/time. It is reference-only for normal skill
operation:

- request explicit permission and a bounded dataset/destination first;
- verify the dataset name and source URL rather than accepting arbitrary input;
- avoid `redownload=True` unless repairing a known incomplete archive;
- inspect disk budget before extraction;
- do not treat a successful download as a license or evaluation approval.

For a smoke check, create a tiny local `corpus.jsonl`, `queries.jsonl`, and
`qrels/test.tsv` tree and use the loaders with `show_progress=False`. No
external BEIR package is required for these local parsing checks, but
`evaluate` still requires `pytrec_eval`.

## Benchmark utilities

`bm25s.utils.benchmark` is separate from BEIR scoring:

- `Timer(prefix="", precision=4)` supports `start`, `stop`, `pause`, `resume`,
  `elapsed`, `show`, `show_all`, and `to_dict`.
- `get_max_memory_usage(format="GB")` returns process peak memory for `GB`,
  `MB`, or `KB` on platforms with `resource`; invalid formats raise
  `ValueError`, and unsupported platforms return `None` with a warning.

These helpers are useful for a bounded local measurement. They do not control
threads, normalize hardware, download datasets, or produce a comparison claim.
Keep full BEIR comparisons, large corpus runs, and other long benchmarks out of
routine verification.

## Difficult local cases

A useful evaluator test should include two queries, a tied or zero-score
result, and one result whose document ID equals the query ID. Verify that the
ID-equal result is removed by default and that passing a copied mapping with
`ignore_identical_ids=False` preserves it. A second test should omit
`qrels/test.tsv` or use a wrong document namespace and assert a clear repair
message, not a fabricated metric.

For failure diagnosis, see [troubleshooting.md](troubleshooting.md).
