# Training Troubleshooting

Use this guide before starting expensive BEIR/SentenceTransformers training and when adapting BEIR examples to user data.

## Qrels Reference Missing Corpus IDs

Symptoms:

- `load_train()` logs `Error: Key <doc_id> not present in corpus!` and silently creates fewer examples.
- `load_ir_evaluator(..., max_corpus_size=...)` raises `KeyError` when mandatory relevant docs are selected.
- Training sample count is unexpectedly small or zero.

Cause:

- Positive qrels entries reference document ids that are absent from the loaded corpus.

Fix:

- Preflight `positive_doc_ids - corpus.keys()` before calling training helpers.
- Repair dataset ids or filter qrels intentionally, then report how many positives were dropped.
- Use `python scripts/training_data_smoke.py` as a pattern for explicit validation.

## Empty Dev Set Error

Symptom:

```text
ValueError: Dev Set Empty!, Cannot evaluate on Dev set.
```

Cause:

- `TrainRetriever.load_ir_evaluator()` rejects empty `dev_queries`.

Fix:

- Load a real dev split or create a held-out validation split.
- If no dev set exists and the user accepts no metric-based checkpoint selection, use `retriever.load_dummy_evaluator()` and set expectations clearly.
- Consider fewer or no periodic evaluation steps if evaluation is too expensive.

## `max_corpus_size` Too Small

Symptom:

```text
ValueError: Your maximum corpus size should atleast contain N corpus ids
```

Cause:

- The evaluator must include every unique positive document id from dev qrels. `max_corpus_size` is smaller than that mandatory set.

Fix:

- Set `max_corpus_size >= len(unique_positive_dev_doc_ids)`.
- If reducing evaluator size, filter dev queries/qrels deliberately before calling `load_ir_evaluator()`.
- Do not treat this as a random sampling problem; relevant docs are mandatory.

## Triplet Tuple Shape Problems

Symptoms:

- SentenceTransformers loss fails later with confusing batch or feature errors.
- Examples contain ids rather than text.
- Margin-MSE labels do not match examples.

Cause:

- `load_train_triplets()` does not validate tuple length or element type; it wraps each item as `InputExample(texts=triplet)`.

Fix:

- Validate that each triplet has exactly three strings before calling BEIR.
- Resolve ids to query, positive passage, and negative passage text first.
- For `MarginMSELoss`, set the label to `positive_teacher_score - negative_teacher_score` for the same positive and negative passages.
- For multiple-negatives objectives, avoid duplicate texts inside batches when possible.

## PyTorch, SentenceTransformers, and Transformers Compatibility

Symptoms:

- Import errors around `transformers.AdamW`.
- `SentencesDataset` or `InputExample` import paths differ.
- CUDA, AMP, or tokenizer errors appear before training starts.

Cause:

- BEIR 2.2.0 training code depends on SentenceTransformers, PyTorch, and Transformers APIs that can move or deprecate across versions.

Fix:

- Run a lightweight import and smoke check before full training.
- If `transformers.AdamW` is unavailable, pass a compatible optimizer class explicitly to `retriever.fit()` rather than editing BEIR source.
- Disable `use_amp` when device or model dtype support is uncertain.
- Keep package changes isolated to the user's environment and record versions in experiment notes.

## Long Training, Downloads, and GPU Requirements

Symptoms:

- Training appears stuck while downloading datasets or model weights.
- CPU training is extremely slow.
- Out-of-memory errors occur after increasing batch size or sequence length.

Cause:

- BEIR training examples are full experiments: they download datasets, model weights, hard-negative files, and run multi-epoch transformer training.

Fix:

- Confirm network, credentials, cache directories, and hardware before starting.
- Start with a tiny sample, low `epochs`, low `batch_size`, and `use_amp=False` unless GPU mixed precision is verified.
- Treat MS MARCO hard-negative and BPR/Margin-MSE examples as reference patterns, not quick smoke tests.
- Scale `batch_size`, `max_seq_length`, and `evaluation_steps` based on actual memory and evaluator runtime.

## Output Checkpoint Path and Evaluator Scheduling

Symptoms:

- Checkpoints overwrite a prior run.
- No best model is saved or checkpoint selection is meaningless.
- Periodic evaluation dominates training time.

Cause:

- `output_path`, `save_best_model`, evaluator type, and `evaluation_steps` were not planned together.

Fix:

- Use a user-owned run directory with dataset, model, loss, and timestamp or version in the name.
- Check if `output_path` exists and ask before overwriting when the run is valuable.
- Use a real IR evaluator when `save_best_model=True` should mean best retrieval quality.
- Increase `evaluation_steps` or use a smaller dev subset when evaluator cost is too high.

## Loss Mismatch

Symptoms:

- Metrics regress despite successful training.
- Dot-product retrieval performs poorly after cosine-style training, or vice versa.
- `MarginMSELoss` labels are all `1` or `0`.

Cause:

- Loss, label semantics, and downstream score function are misaligned.

Fix:

- Pair qrels plus `MultipleNegativesRankingLoss` is the default simple path.
- Use `MarginMSELoss` only with teacher score margins.
- Use `BPRLoss` only for binary-code retriever objectives.
- Align training similarity with downstream retrieval scoring (`cos_sim` versus `dot`) and document the choice in the run plan.
