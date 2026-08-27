# Retrieval and Representation Data Formats

## Representation input

`RepresentationModel.encode_sentences()` accepts a list of strings. Choose a combine strategy that matches the downstream use: all tokens, selected token, mean pooling, or concatenation depending on model/source support.

## Retrieval train/eval DataFrame or TSV

Columns:

| column | type | notes |
|---|---|---|
| `query_text` | string | query |
| `gold_passage` | string | positive passage |
| `title` | string optional | passage title; controlled by `include_title` |

When `use_hf_datasets=True`, a path to a TSV with equivalent columns may be used.

## Prediction queries

Prediction input is a list of query strings. If using precomputed or persistent passages, validate `prediction_passages` and any FAISS index path before prediction.

## BEIR-style files

Common BEIR structures use corpus documents with `_id`, `title`, `text`, query records with `_id`, `text`, and qrels mapping query ids to document ids/relevance. Conversion helpers exist in the package, but optional BEIR dependencies are not installed by default.

## Hard negatives

Hard-negative training variants need positive passage text plus one or more negative passage fields/lists. Keep data format aligned with the selected `RetrievalArgs` flags (`hard_negatives`, `include_hard_negatives`, `data_format`, and loss options).

## Validator

```bash
python scripts/validate_retrieval_data.py --task retrieval-csv --input train.csv
python scripts/validate_retrieval_data.py --task tsv --input train.tsv
python scripts/validate_retrieval_data.py --task query-lines --input predict.txt
python scripts/validate_retrieval_data.py --task beir-corpus-jsonl --input corpus.jsonl
python scripts/validate_retrieval_data.py --task beir-queries-jsonl --input queries.jsonl
```
