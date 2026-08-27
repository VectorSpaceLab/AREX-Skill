# Troubleshooting

## Import and installation failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError` for BERTopic or its base dependencies | The package is not installed in the active Python environment, or the environment is incomplete | Install the BERTopic package and its base scientific stack before running this workflow. |
| `ImportError` for `numpy`, `scipy`, `pandas`, `scikit-learn`, or `joblib` | Core numeric dependencies are missing or incompatible | Repair the scientific Python stack first; these workflows depend on sparse matrices and scikit-learn vectorizers. |
| Import succeeds but a tokenizer helper is missing | The corpus-specific tokenizer library is optional | Install only the tokenizer package you actually need, such as a language segmenter, instead of broad extras. |
| BERTopic fitting tries to download embedding models you do not want | A training path was used instead of a vectorizer-only refresh path | For topic-word tuning only, prefer `update_topics(...)` with precomputed documents or use the bundled smoke script. |

## API misuse and invalid input

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Empty vocabulary or empty topic words | `stop_words`, `min_df`, `max_features`, or the tokenizer removed too much | Relax one knob at a time and confirm the vocabulary is non-empty before adding another restriction. |
| `update_topics` fails because the model is not fitted | `update_topics(...)` was called before the model had learned topics | Fit BERTopic first, then refresh the representation. |
| `update_topics` gives wrong results after remapping topics | Topic list length or document ordering does not match the fitted corpus | Keep the document order stable and pass `topics=` only when you are sure the mapping is aligned. |
| The second positional argument to `update_topics` behaves like images instead of topics | The signature is `docs, images=None, topics=None, ...` | Use `topics=...` explicitly instead of relying on positional arguments. |
| The custom tokenizer seems ignored or inconsistent | `token_pattern` was left active or the tokenizer is not deterministic | Pass `token_pattern=None` and keep tokenization rules stable across fit/update calls. |
| `ngram_range` looks valid but no phrases appear | Stop words or frequency thresholds remove the phrases before scoring | Lower the stopword pressure or relax `min_df`. |
| `max_features` is too small | The vocabulary ceiling is cutting off meaningful topic words | Raise `max_features` or pair it with a milder `min_df`. |
| `top_n_words` is very large and the model slows down | Sparse extraction with many words can be expensive | Keep `top_n_words` modest unless the downstream use case truly needs long topic lists. |

## Online vocabulary workflow issues

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `update_bow` fails on the first batch | `partial_fit` was not called first | Call `partial_fit(batch)` before `update_bow(batch)` for every stream batch. |
| The matrix shape drifts unexpectedly across batches | Batch sizes or row bookkeeping changed between updates | Keep the batch structure consistent, or let BERTopic manage the online path end to end. |
| Low-frequency words never disappear | `delete_min_df` is unset or too low | Set a positive `delete_min_df` and verify the cleanup threshold is meaningful for the stream. |
| Useful terms disappear too quickly | `delete_min_df` is too aggressive or `decay` is too high | Reduce the cleanup threshold or soften the decay. |
| Removed terms later reappear and change the vocabulary | This is expected behavior | Cleanup is not permanent; new data can reintroduce a word if it becomes frequent again. |

## Backend and dependency gotchas

- The vectorizer and c-TF-IDF path is CPU/sparse-matrix based; it does not require a GPU.
- `OnlineCountVectorizer` depends on sparse matrix operations from SciPy; missing SciPy breaks cleanup and bag-of-words updates.
- `CountVectorizer` will raise on invalid ranges, empty analyzers, or incompatible stopword/tokenizer combinations.
- Importing BERTopic classes also requires the package's base dependencies, including `joblib`; if the package import fails before you reach the vectorizer classes, repair the base install first.
- The package may still expose optional placeholders for unrelated backends; those are not required for this workflow.

## When to retry vs. when to stop

Retry with a smaller synthetic corpus if:

- the vocabulary is empty,
- one parameter is too aggressive, or
- the tokenizer needs a quick correction.

Stop and repair the environment if:

- base scientific imports fail,
- BERTopic cannot import at all, or
- SciPy sparse operations are unavailable.
