# NLP and generation troubleshooting

## NLTK download is blocked

**Symptom**: `client(...)` hangs or raises a proxied fetch/pathsec error.

**Fix**:
- Run `scripts/prepare_nltk_corpora.py --check` to identify missing corpora.
- Pre-download corpora in a trusted environment.
- Use `NLTK_ALLOW_PROXIED_URLOPEN=1` only when the proxy is trusted.
- For non-NLP smoke checks only, monkey-patch `client.required_installations = lambda self: None` before constructing the client.

## Text classification uses the wrong label column

**Symptom**: training fails or learns labels from the wrong field.

**Fix**: pass `label_column="..."` whenever the label column is not exactly `label`.

## Summarization says the target is missing

**Symptom**: the dataset has summaries, but the method cannot find the expected target.

**Fix**: pass the actual summary column name through `label_column`. The default is `summary`.

## `generate_text` opens the wrong file

**Symptom**: GPT-2 generation reads the client dataset path instead of the user's prompt.

**Fix**: call `generate_text(file_data=False, prefix="...")` for prompt-only generation.

## Transformer model download is blocked

**Symptom**: T5, GPT-2, NER, or InceptionV3 load fails because the model is absent from cache.

**Fix**:
- Stage the model cache first.
- Use a network-approved environment.
- Do not claim the workflow ran if only the API-surface smoke helper was executed.

## `classify_text` or `get_summary` before training

These prediction helpers rely on `client.models['text_classification']` or `client.models['summarization']`. Train the corresponding query first or check that the key is present in `client.models`.

## Validation parameters fail early

The source raises explicit exceptions for invalid `test_size`, `epochs`, `batch_size`, `max_text_length`, `top_k`, `buffer_size`, `embedding_dim`, and `units`. Fix the argument value before debugging model internals.
