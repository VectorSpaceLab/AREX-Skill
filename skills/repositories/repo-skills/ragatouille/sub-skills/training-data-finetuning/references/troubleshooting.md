# Troubleshooting

## Invalid Raw Data Arity

Symptom:
- `ValueError("Raw data must be a list of pairs or triplets of strings.")`.
- Python unpacking errors inside `TrainingDataProcessor`.

Cause:
- Rows are not length 2 or 3, or mixed row shapes appear in one `raw_data` list.

Recovery:
- Split data into separate `pairs`, `labeled_pairs`, and `triplets` batches.
- For length-3 labeled rows, pass `pairs_with_labels=True`.
- For explicit triplets, pass `pairs_with_labels=False` and usually `num_new_negatives=0`.
- Run `scripts/validate_training_data.py` with `--mode auto` before calling RAGatouille.

## Non-String Queries

Symptom:
- `ValueError("Queries must be a strings.")`.

Cause:
- The first element of a raw row is not a string.

Recovery:
- Convert query IDs or structured query objects to text before training.
- Keep metadata outside `raw_data`; preserve it in a separate mapping if needed.

## Invalid Labels

Symptoms:
- `ValueError("Invalid value for label: ...")` during `RAGTrainer.prepare_training_data`.
- `ValueError("Label ... must correspond to either positive_label or negative_label!")` during processing.

Cause:
- A labeled pair's third column does not equal `positive_label` or `negative_label`.

Recovery:
- Normalize labels before passing data.
- Set `positive_label` and `negative_label` explicitly when labels are strings or non-default integers.
- Do not use `pairs_with_labels=True` for explicit triplets.

## No Training Triplets

Symptoms:
- Warning that no triplets were generated with `mine_hard_negatives=True`, followed by fallback to random negatives.
- `ValueError("No training triplets were generated.")` when mining is disabled.
- Empty `triples.train.colbert.jsonl`.

Common causes:
- Pairs have positives but the collection has no distinct negatives.
- Labeled pairs have no negative rows for a query.
- Explicit triplets contain empty positive or negative lists.
- A tiny corpus leaves no candidates after excluding positives and known negatives.
- Hard-negative `min_rank` skips most or all available candidates.

Recovery options:
- Add a broader `all_documents` corpus or call `add_documents` before preparation.
- Set `mine_hard_negatives=False` to sample random negatives from a broad corpus.
- Lower `hard_negative_minimum_rank` only if near-neighbor false positives are acceptable.
- Provide explicit triplets with curated negatives and set `num_new_negatives=0`.
- Use a larger corpus; hard negatives are least reliable on very small collections.

## Hard-Negative Downloads and Dependencies

Symptoms:
- Slow startup or network access during `prepare_training_data`.
- `sentence_transformers` model download failures.
- Voyager or Torch-related import/runtime errors.
- Missing `psutil` errors from dependency stacks such as `fast-pytorch-kmeans`.

Cause:
- `mine_hard_negatives=True` constructs `SimpleMiner`, which loads a dense embedding model and builds a Voyager index.

Recovery:
- Use `mine_hard_negatives=False` for offline or lightweight validation.
- Install/check `sentence-transformers`, `voyager`, `torch`, and `psutil` before hard mining.
- Start with `hard_negative_model_size="small"`; `"base"` and `"large"` use more memory and bandwidth.
- Use the trainer's `language_code` deliberately: unsupported codes route to multilingual E5 models.

## LangChain Compatibility During Imports

Symptom:
- Import errors involving `langchain.retrievers.document_compressors.base`.

Cause:
- RAGatouille `0.0.9post2` expects a legacy-compatible LangChain package set; latest LangChain `1.x` no longer exposes that import path.

Recovery:
- Use a legacy-compatible LangChain set when importing full RAGatouille.
- For pure raw-data validation, use the bundled validator because it does not import RAGatouille.

## CUDA and Training Expectations

Symptoms:
- Full training is skipped or fails on CPU-only machines.
- CUDA out-of-memory errors.
- Long-running or stalled training jobs.

Cause:
- `train()` delegates to ColBERT training and is intended for a suitable GPU environment with model checkpoints available.

Recovery:
- Treat `prepare_training_data` as the safe step and `train()` as expensive runtime work.
- Smoke-test with tiny `maxsteps` only on suitable hardware.
- Reduce `batch_size`, `doc_maxlen`, or `dim` for memory pressure.
- Use `accumsteps` to simulate larger batches without raising per-step memory.
- Skip native full-training tests in lightweight verification; they are GPU/expensive candidates.

## Output File Problems

Symptoms:
- `train()` cannot find `triples.train.colbert.jsonl`.
- Output directory contains queries and corpus but no useful triples.

Recovery:
- Ensure `prepare_training_data(..., data_out_path=...)` completed before `train()`.
- Confirm all three files exist: `queries.train.colbert.tsv`, `corpus.train.colbert.tsv`, `triples.train.colbert.jsonl`.
- Count JSONL lines; zero lines means the raw examples did not produce trainable triplets.
- Keep `data_out_path` stable between preparation and training.

## `all_documents` With Processed Chunks

Symptom:
- Hard-negative or random sampling ignores chunk dictionaries passed via `all_documents`.

Cause:
- `RAGTrainer.prepare_training_data` only adds string entries from `all_documents`; dict `content` extraction is used for raw example passages, not for `all_documents`.

Recovery:
- Convert corpus chunks before passing them:
  ```python
  all_documents = [chunk["content"] for chunk in chunks]
  ```

## Standalone Script Side Effects

Symptom:
- Training scripts behave unexpectedly when imported by tests or multiprocessing workers.

Recovery:
- Put execution behind `if __name__ == "__main__": main()`.
- Keep data loading, preparation, and training in functions so tests can call only the safe data-prep pieces.
