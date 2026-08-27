# LDA Workflow and Tuning Notes

## Prepare inputs

1. Start with tokenized documents.
2. Build one `Dictionary` and filter extremes based on document count and domain
   knowledge.
3. Create `corpus = [dictionary.doc2bow(doc) for doc in texts]` or a streaming
   equivalent.
4. Pass `id2word=dictionary` or its id-to-token mapping so topics can be shown.

## Parameter strategy

- Start with a small, interpretable `num_topics` and increase only if topics are
  under-specified.
- Increase `passes` when the model has not converged; increase `iterations` when
  per-document inference is insufficient.
- Increase `chunksize` only when memory allows; it changes throughput and may
  influence online update behavior.
- Try `alpha='auto'` or an explicit prior only after a baseline with the default.
- Use `eval_every=None` for large training runs when frequent perplexity checks
  are too expensive; monitor coherence or held-out behavior separately.
- Use `random_state` for reproducible comparisons, but do not expect identical
  topic ordering across runs or platforms.

## Inspect topics

- `model.print_topics()` returns human-readable word-weight strings.
- `model.show_topics(formatted=False)` is easier to parse programmatically.
- `model.get_document_topics(bow)` returns a sparse topic mixture; adjust
  `minimum_probability` when small topics disappear from output.

## Evaluation cautions

Topic coherence depends on tokenization, dictionary filtering, `topn`, window
size, and coherence measure. Compare models only when those choices are held
constant. Qualitative inspection by a domain expert remains important.

## Failure recovery

- If all documents produce empty or near-empty topic distributions, inspect
  dictionary filtering and query BoW vectors.
- If training is too slow, reduce passes/iterations for a diagnostic, use
  `LdaMulticore` on one machine, and check BLAS performance.
- If a model cannot display terms, load the dictionary saved with the model or
  pass a matching `id2word` mapping.
