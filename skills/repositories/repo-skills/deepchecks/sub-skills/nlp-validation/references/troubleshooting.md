# NLP Troubleshooting

If Deepchecks itself or the active environment will not import, start with [root troubleshooting](../../../references/troubleshooting.md). This reference focuses on NLP-specific extras, downloads, labels, shapes, and runtime caveats.

## Quick isolation sequence

```python
# 1. Text and label hygiene
assert len(raw_text or tokenized_text) > 0
assert label is None or len(label) == len(text_rows)

# 2. Task hygiene
assert task_type in {"text_classification", "token_classification", "other"}

# 3. Table / vector alignment
assert metadata is None or len(metadata) == len(text_rows)
assert properties is None or len(properties) == len(text_rows)
assert embeddings is None or len(embeddings) == len(text_rows)

# 4. Prediction / probability shape hygiene
assert predictions is None or len(predictions) == len(text_rows)
assert probabilities is None or len(probabilities) == len(text_rows)
```

## Extras and import failures

| Symptom or message fragment | Likely cause | Fix | Validate |
|---|---|---|---|
| Missing `deepchecks.nlp` import | `deepchecks[nlp]` is not installed in the active interpreter. | Install the NLP extra in that environment. | `python -c "import deepchecks.nlp"` |
| Missing NLP property helpers | `deepchecks[nlp-properties]` is not installed or the runtime lacks its optional packages. | Install the NLP properties extra, then retry. | `python -c "from deepchecks.nlp import TextData"` |
| Missing token classification scorer support | `seqeval` is missing. | Install the NLP extra or the token metrics dependency. | `python -c "import seqeval"` |
| `ImportError` for `transformers`, `sentence_transformers`, `tiktoken`, or `fasttext` | Optional NLP dependencies are absent. | Install the relevant NLP extra or the missing package. | `python -c "import transformers, sentence_transformers, tiktoken, fasttext"` |
| `ImportError` for `nltk` resources during property calculation | Required corpora are not present yet. | Avoid the property, precompute it offline, or allow the relevant corpus cache to be populated intentionally. | Re-run the property after installing the corpus or using the smoke helper's precomputed tables. |

## Tokenizer and model downloads

| Symptom or message fragment | Likely cause | Fix | Validate |
|---|---|---|---|
| Default `UnknownTokens` tries to download `bert-base-uncased` | No tokenizer was supplied, so the check fell back to Hugging Face. | Pass a local tokenizer object or stub to the suite/check constructor. | Run the smoke helper with the local tokenizer path. |
| `calculate_builtin_embeddings()` starts fetching MiniLM weights | The built-in embedding generator uses `sentence_transformers`. | Use `set_embeddings()` with a precomputed array instead. | `assert embeddings.shape[0] == len(text_rows)` |
| `calculate_builtin_embeddings(model='open_ai')` needs network or API credentials | OpenAI embeddings are an external API workflow. | Keep the smoke path offline by using precomputed embeddings. | Avoid the OpenAI branch in local validation. |
| Property calculation downloads fastText or transformer assets | Built-in properties such as `Language`, `Toxicity`, `Fluency`, or `Formality` need external resources. | Use `set_properties()` for precomputed values, or calculate only the cheap local properties you explicitly need. | Keep the smoke data tiny and local. |

## Task type and label errors

| Symptom or message fragment | Likely cause | Fix | Validate |
|---|---|---|---|
| `task_type must be set when label is provided` | Labels were supplied without a task type. | Set `task_type='text_classification'` or `task_type='token_classification'`. | Rebuild the `TextData`. |
| `tokenized_text must be provided for token_classification task type` | Token classification was requested without tokenized text. | Pass tokenized tokens explicitly. | `assert tokenized_text is not None` |
| `raw_text and tokenized_text sequences must have the same length` | The two text lists were misaligned. | Rebuild both lists from the same row order. | `len(raw_text) == len(tokenized_text)` |
| `label must be a Sequence of strings or ints ...` | Text-classification labels are the wrong shape or type. | Use a 1D sequence for single-label tasks or a 2D binary matrix for multilabel tasks. | Inspect `type(label[0])`. |
| `multilabel was identified. It must be a Sequence of Sequences of 0 or 1` | Multilabel rows contain non-binary values. | Convert each row to 0/1 vectors. | `set(np.unique(labels)) <= {0, 1}` |
| `label must be the same length as tokenized_text` | A token label row has the wrong token count. | Make each label row align token-for-token with the input. | Compare the token and label lengths per sample. |
| `task_type ... is not supported` | A typo or unsupported task string was used. | Use the exact lowercase task names from the API reference. | `print(task_type)` |
| `Received unsorted model_classes` | Classification classes are not sorted. | Sort the class list and keep probability columns in the same order. | `model_classes == sorted(model_classes)` |
| `O label was removed from model_classes` | Token metrics ignore the outside tag. | Keep `O` out of your downstream `model_classes` if you want an exact metrics label list. | Re-run with entity-only classes. |

## Alignment and shape errors

| Symptom or message fragment | Likely cause | Fix | Validate |
|---|---|---|---|
| `received Metadata with X rows, expected Y` | Metadata rows do not match the text rows. | Rebuild metadata from the same filtered/split rows as the text. | `len(metadata) == len(text_rows)` |
| `received Properties with X rows, expected Y` | Properties rows do not match the text rows. | Rebuild or reindex the properties table. | `len(properties) == len(text_rows)` |
| `Embeddings type <class 'list'> is not supported` | `set_embeddings()` received a list instead of an array, DataFrame, or `.npy` path. | Convert to `np.ndarray` or a DataFrame. | `isinstance(embeddings, np.ndarray)` |
| `received Embeddings with X rows, expected Y` | Embeddings row count does not match the text rows. | Recompute or re-slice the array using the same row order. | `embeddings.shape[0] == len(text_rows)` |
| `Check requires predictions ... same as dataset` | Prediction length does not match the dataset length. | Regenerate predictions after any filtering/splitting. | `len(predictions) == len(text_rows)` |
| `Check requires classification probabilities ... sum to 1` | Text-classification probability rows are not normalized. | Normalize each row before passing them. | `np.allclose(np.sum(probabilities, axis=1), 1)` |
| `Check requires multi-label classification probabilities ... values must lay between 0 and 1` | Multilabel probabilities are outside the allowed range. | Clip or rescale the scores to `[0, 1]`. | `probabilities.min() >= 0 and probabilities.max() <= 1` |
| `For token classification probabilities are not supported` | Probabilities were passed to a token-classification check. | Remove the probability arguments. | Keep only token-level predictions. |
| `Metadata type <class 'dict'> is not supported` or `Properties type <class 'dict'> is not supported` | The constructor expects a DataFrame or local path, not a dict. | Convert the object to a DataFrame before passing it. | `isinstance(metadata, pd.DataFrame)` |

## Performance caveats

| Symptom | Likely cause | Fix |
|---|---|---|
| Slow property calculation | Heavy built-ins such as `Toxicity`, `Fluency`, `Formality`, or `Unique Noun Count` are enabled. | Prefer precomputed properties, or limit `include_properties` to cheap local features. |
| Long runtime for embeddings | The built-in embedding generator is downloading or encoding with a large model. | Use `set_embeddings()` with precomputed vectors for smoke runs. |
| Property checks return `NaN` for some samples | An English-only or corpus-based property could not be calculated for those rows. | Use precomputed values, or accept the missing values and restrict the check scope. |
| A suite runs but some checks are unsupported or not-ran | The chosen suite needs inputs you did not provide. | Inspect `result.get_not_ran_checks()` and either supply the missing artifacts or accept the partial result. |
| Notebook/widget rendering is noisy | Display mode is on in an automation context. | Set `with_display=False`. |

The bundled smoke helper intentionally uses tiny synthetic data. If you run a full suite on that data, drift or weak-segment checks may warn or fail even when the API path is correct.

## Recovery patterns

### Token classification without probabilities

Use token labels only and expect the token metrics to drive the result.

```python
result = model_evaluation(n_samples=12).run(
    train_dataset=train,
    test_dataset=test,
    train_predictions=train_predictions,
    test_predictions=test_predictions,
    with_display=False,
)
```

### Offline properties and embeddings

Use precomputed tables instead of the built-in generators.

```python
train = TextData(
    raw_text=texts,
    label=labels,
    task_type="text_classification",
    metadata=metadata,
    properties=properties,
    embeddings=embeddings,
)
```
