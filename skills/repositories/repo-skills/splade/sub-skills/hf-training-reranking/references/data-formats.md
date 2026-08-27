# HF Training Data Formats

HF SPLADE training reads text collections plus a training-file source of positives/negatives/scores. Validate data arguments before creating commands because failures often happen before model training starts.

## Required Text and Qrel Files

For `L2I_Dataset` and `RerankingDataset`, provide:

| Argument | Expected format | Purpose |
| --- | --- | --- |
| `hf.data.document_dir` | TSV file, one document per line as `DOCID<TAB>TEXT` | Document collection loaded by content id |
| `hf.data.query_dir` | TSV file, one query per line as `QID<TAB>TEXT` | Query collection loaded by content id |
| `hf.data.qrels_path` | JSON object `{QID: {DOCID: relevance, ...}, ...}` | Positive labels; relevance values below `1` are filtered out |
| `hf.data.training_data_path` | Format depends on `training_data_type` | Hard negatives, run scores, or triplets |
| `hf.data.training_data_type` | One of `saved_pkl`, `pkl_dict`, `trec`, `json`, `triplets` | Chooses the loader path |

IDs are cast to strings in several loaders. Keep qrel IDs, collection IDs, and run/hard-negative IDs aligned exactly after string conversion.

## Accepted `training_data_type` Values

| Type | File shape | Notes |
| --- | --- | --- |
| `saved_pkl` | Pickle object shaped like a query-to-document score mapping | Used for already filtered saved training samples. |
| `pkl_dict` | Gzip pickle dictionary `{QID: {DID: score, ...}, ...}` | Intended for hard-negative score files where qids/dids may be integers; loader casts to strings and filters qids not in qrels. |
| `trec` | TREC run lines: `qid Q0 did rank score tag` | Scores are read per query/document from a run file. |
| `json` | JSON object `{QID: {DID: score, ...}, ...}` | Typical SPLADE-run or hard-negative JSON; documents are sorted by score. |
| `triplets` | Raw TSV rows `query<TAB>positive<TAB>negative` | Uses `TRIPLET_Dataset`; no collection/query/qrel lookup is performed by the triplet dataset itself. |

The converter asserts that `training_data_type` is in `['saved_pkl', 'pkl_dict', 'trec', 'json', 'triplets']`. The non-triplet `L2I_Dataset` implementation raises `NotImplementedError` mentioning only `saved_pkl`, `pkl_dict`, `trec`, and `json`; `triplets` is handled earlier by `splade.hf_train`.

## Hard-Negative JSON Example

A compact JSON hard-negative file can look like:

```json
{
  "101": {"D9": 14.2, "D7": 13.8, "D3": 9.1, "D5": 7.0},
  "102": {"D4": 12.5, "D8": 10.3, "D1": 3.2, "D6": 1.4}
}
```

With qrels:

```json
{
  "101": {"D2": 1},
  "102": {"D4": 1}
}
```

The loader removes qrel positives from the candidate negative list. Include at least `n_negatives` usable non-positive candidates per query when possible; if too few remain, the loader samples with replacement.

## Triplets

Triplet rows are raw text, not IDs:

```text
what is splade<TAB>a sparse lexical expansion model<TAB>a dense image classifier
how to index docs<TAB>run the index command<TAB>train the reranker only
```

Rules:

- Use `hf.data.training_data_type=triplets`.
- Set `hf.data.n_negatives=1`; the conversion logic asserts this.
- If `hf.data.training_data_path` is omitted and the classic data config contains `data.TRAIN_DATA_DIR`, the converter uses `data.TRAIN_DATA_DIR/raw.tsv`.
- Since triplets contain raw query/document text, `document_dir`, `query_dir`, and `qrels_path` are not needed by `TRIPLET_Dataset`.

## Reranker Training Data

`python -m splade.hf_train_reranker` uses `RerankingDataset`, a subclass of `L2I_Dataset`. It expects the same non-triplet hard-negative/qrel/collection/query arguments and returns repeated query text paired with a positive document plus negatives.

Common reranker-training overrides:

```bash
hf.data.training_data_type=json \
hf.data.training_data_path='<RERANKER_TRAIN_RUN_OR_HARD_NEGATIVES_JSON>' \
hf.data.document_dir='<COLLECTION_RAW_TSV>' \
hf.data.query_dir='<TRAIN_QUERIES_RAW_TSV>' \
hf.data.qrels_path='<TRAIN_QRELS_JSON>' \
hf.data.n_negatives=1 \
hf.data.prompt_q='Query: {}\n' \
hf.data.prompt_d='Document: {}\n'
```

Prompts are optional. When supplied, `RerankerCollator` formats every query/document string before tokenization.

## Validation Checklist

Before returning a command, confirm:

- `training_data_type` is exactly one of `saved_pkl`, `pkl_dict`, `trec`, `json`, or `triplets`.
- Non-triplet training has `training_data_path`, `document_dir`, `query_dir`, and `qrels_path`.
- Triplet training has `training_data_path` or a config that resolves to `TRAIN_DATA_DIR/raw.tsv`, plus `n_negatives=1`.
- Qrels contain at least one relevance `>= 1` positive for each training query used by non-triplet data.
- Hard-negative/run files contain enough non-positive candidates for the requested `n_negatives`.
- Paths are quoted when they contain shell metacharacters, and placeholder paths are explicitly called out as placeholders.
