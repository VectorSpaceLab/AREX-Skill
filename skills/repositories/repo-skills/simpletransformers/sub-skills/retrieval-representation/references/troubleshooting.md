# Retrieval and Representation Troubleshooting

## Missing optional dependencies

Symptoms:

- `ImportError: No module named faiss`
- `pytrec_eval not installed`
- BEIR loader/evaluator import failures

Recovery: install only the optional dependency needed by the selected workflow. Do not install FAISS/BEIR just to validate CSV schemas.

## Prediction passages or index missing

If prediction fails before scoring, confirm `prediction_passages`, saved passage datasets, and any FAISS index paths. A dense retriever cannot answer queries without candidate passages or embeddings.

## BEIR column mismatch

BEIR uses `_id`, `title`, `text` and qrels-style relevance mappings; Simple Transformers training docs use `query_text`, `gold_passage`, optional `title`. Convert deliberately rather than renaming columns ad hoc.

## Hard-negative shape errors

Hard-negative workflows need lists/fields matching the selected loss flags. Verify negatives are not identical to positives and that each query has enough negatives for `n_hard_negatives`.

## SequenceSummary compatibility

Retrieval imports may fail because shared custom model code imports removed Transformers aliases. Fix dependency compatibility before editing retrieval data.

## Expensive native checks

Representation/retrieval examples download models and datasets. Ask before running full native retrieval tests, BEIR evaluation, hard-negative mining, clustering, or FAISS index building.
