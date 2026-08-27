# Data Loading Workflows

Use these workflows to create, validate, load, download, and persist BEIR-format data without depending on repository examples.

## Create a Tiny Offline Dataset

Use the bundled fixture maker when a user needs a known-good local dataset for smoke tests, examples, or validation repair work:

```bash
python scripts/make_tiny_beir_dataset.py ./tiny-beir
python scripts/validate_beir_dataset.py ./tiny-beir --split test
```

The fixture contains:

- `corpus.jsonl` with two documents.
- `queries.jsonl` with two queries.
- `qrels/test.tsv` with one relevant document per query.

Then load it with BEIR:

```python
from beir.datasets.data_loader import GenericDataLoader

corpus, queries, qrels = GenericDataLoader(data_folder="./tiny-beir").load(split="test")
```

## Validate a Custom Dataset Before Loading

Run the bundled validator first:

```bash
python scripts/validate_beir_dataset.py ./my-dataset --split test
```

The validator checks that:

- `corpus.jsonl`, `queries.jsonl`, and `qrels/<split>.tsv` exist.
- JSONL rows are valid JSON objects with non-empty string `_id` fields.
- Corpus rows include `text` and `title`; query rows include `text`.
- Duplicate corpus or query ids are reported.
- Qrels header is `query-id<TAB>corpus-id<TAB>score`.
- Qrels rows have three tab-separated fields and integer-compatible scores.
- Every qrel query id exists in queries and every qrel corpus id exists in corpus.

After validation, use:

```python
from beir.datasets.data_loader import GenericDataLoader

corpus, queries, qrels = GenericDataLoader(data_folder="./my-dataset").load(split="test")
```

## Repair Missing Qrel References

If validation reports a missing document id such as `qrels/test.tsv:4 corpus-id 'doc99' is not present in corpus`, decide whether the qrel or corpus is wrong:

1. If `doc99` is a typo, edit the qrels row to the correct corpus `_id`.
2. If `doc99` is a real judged document, add a `corpus.jsonl` row with `_id`, `title`, and `text`.
3. Re-run the validator until it exits successfully.
4. Load with `GenericDataLoader` only after qrels and file ids agree.

Do not ignore this error: retrieval evaluation expects result ids and qrels ids to refer to the same document universe.

## Use Explicit Custom File Paths

When a user's files do not follow the standard directory layout, pass explicit paths and call `load_custom()`:

```python
from beir.datasets.data_loader import GenericDataLoader

corpus, queries, qrels = GenericDataLoader(
    corpus_file="./data/custom_corpus.jsonl",
    query_file="./data/custom_queries.jsonl",
    qrels_file="./labels/custom_qrels.tsv",
).load_custom()
```

The file extension checks still apply: corpus and queries must end in `jsonl`, and qrels must end in `tsv`.

## Use a Prefixed Dataset

BEIR prefix mode supports multiple query/qrels sets sharing one corpus:

```text
my-dataset/
  corpus.jsonl
  fiqa-queries.jsonl
  fiqa-qrels/test.tsv
```

Validate and load:

```bash
python scripts/validate_beir_dataset.py ./my-dataset --split test --prefix fiqa
```

```python
from beir.datasets.data_loader import GenericDataLoader

corpus, queries, qrels = GenericDataLoader(data_folder="./my-dataset", prefix="fiqa").load(split="test")
```

Prefix behavior is a common source of missing-file errors: `prefix="fiqa"` changes `queries.jsonl` to `fiqa-queries.jsonl` and `qrels/` to `fiqa-qrels/`, but it leaves `corpus.jsonl` unchanged.

## Load Through Hugging Face Datasets

Use `HFDataLoader` when the user needs Hugging Face Dataset objects, streaming, or `hf_repo` access:

```python
from beir.datasets.data_loader_hf import HFDataLoader

corpus, queries, qrels = HFDataLoader(hf_repo="BeIR/scifact").load(split="test")
```

For local files through the `datasets` library:

```python
from beir.datasets.data_loader_hf import HFDataLoader

corpus, queries, qrels = HFDataLoader(data_folder="./my-dataset", keep_in_memory=True).load(split="test")
```

When `streaming=True`, treat corpus and queries as iterable/streaming datasets. Avoid logic that requires `len()`, slicing, stable materialized ordering, or repeated full scans unless you explicitly materialize the dataset.

## Download Public BEIR Dataset Zips

When network access is permitted and the user wants a public BEIR dataset zip, use `util.download_and_unzip()`:

```python
from beir import util

url = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/scifact.zip"
data_path = util.download_and_unzip(url, "./datasets")
```

Then validate the extracted folder before downstream work:

```bash
python scripts/validate_beir_dataset.py ./datasets/scifact --split test
```

The repository's bulk dataset download example is intentionally reference-only for this skill because it performs network downloads for many datasets. Prefer a user-approved single URL and validate the result.

## Save and Reload Retrieval Runfiles

Route retrieval execution to the retrieval/evaluation sub-skill, then use these utilities to persist results:

```python
from beir import util

util.save_runfile("./results/scifact.run.trec", results, run_name="my-run", top_k=1000)
loaded_results = util.load_runfile("./results/scifact.run.trec")
```

Runfile rows have six space-separated columns: `qid Q0 docid 0 score run_name`. Keep ids free of spaces because `load_runfile()` splits on spaces.

## Save Metric Results

After evaluation computes metric dictionaries, write JSON with:

```python
from beir import util

util.save_results(
    "./results/scifact.metrics.json",
    ndcg=ndcg,
    _map=_map,
    recall=recall,
    precision=precision,
    mrr=mrr,
)
```

The JSON is useful for reports, reranking comparisons, and regression checks. If optional metric dicts are empty or `None`, they are omitted.
