# NLP API Reference

This reference distills the Deepchecks NLP APIs verified from source, docs, tests, and installed-package signatures. It is intended for future agents operating without the source checkout.

## Imports

```python
from deepchecks.nlp import TextData, Suite
from deepchecks.nlp.suites import data_integrity, train_test_validation, model_evaluation, full_suite
from deepchecks.nlp.checks import (
    ConfusionMatrixReport,
    LabelDrift,
    MetadataSegmentsPerformance,
    PredictionDrift,
    PropertyDrift,
    PropertyLabelCorrelation,
    PropertySegmentsPerformance,
    SingleDatasetPerformance,
    TextEmbeddingsDrift,
    TextPropertyOutliers,
    TrainTestPerformance,
    TrainTestSamplesMix,
)
```

## `TextData` constructor

Verified signature:

```python
TextData(
    raw_text=None,
    tokenized_text=None,
    label=None,
    task_type=None,
    name=None,
    embeddings=None,
    metadata=None,
    categorical_metadata=None,
    properties=None,
    categorical_properties=None,
)
```

### Practical argument guide

| Argument | Accepted forms | Practical notes |
|---|---|---|
| `raw_text` | Sequence of strings. | Use for text classification and text-only validation. For token classification, keep `tokenized_text` as the source of truth. |
| `tokenized_text` | Sequence of sequences of strings. | Required for `task_type='token_classification'`. The current runtime does **not** accept raw text alone for token classification. |
| `label` | Single-label: sequence of strings or ints. Multilabel: sequence of sequences of 0/1. Token classification: sequence of token labels aligned to tokens. | If `label` is provided, `task_type` must also be provided. Missing labels can be represented by `None` / `NaN`. |
| `task_type` | `text_classification`, `token_classification`, or `other`. | Use `text_classification` for single-label and multilabel tasks. `other` is only for unlabeled text-only flows. |
| `name` | String or `None`. | Display name shown in suite output. |
| `metadata` | `pandas.DataFrame` or a local CSV path. | Row count and row order must match the text rows. |
| `categorical_metadata` | List of metadata column names. | Optional. If omitted, Deepchecks infers categorical metadata columns. |
| `properties` | `pandas.DataFrame` or a local CSV path. | Row count and row order must match the text rows. |
| `categorical_properties` | List of custom property column names. | Only needed for custom property columns. Built-in categorical properties such as `Language` are recognized automatically. |
| `embeddings` | `numpy.ndarray`, `pandas.DataFrame`, or a local `.npy` path. | Must have shape `(n_samples, embedding_dim)` and match the text order. |

### TextData shape rules

- All attached tables/arrays must have the same number of rows as the text data.
- Ordering must be consistent across `raw_text` / `tokenized_text`, labels, metadata, properties, and embeddings.
- For token classification, the length of each label sequence must match the corresponding token sequence exactly.
- For multilabel text classification, each row must have the same label width.

### Useful runtime helpers

| API | Purpose |
|---|---|
| `set_metadata(metadata, categorical_metadata=None)` | Attach or replace metadata after construction. |
| `set_properties(properties, categorical_properties=None)` | Attach or replace properties after construction. |
| `set_embeddings(embeddings)` | Attach or replace embeddings after construction. |
| `calculate_builtin_properties(...)` | Generate Deepchecks text properties. May need optional extras or cached model files. |
| `calculate_builtin_embeddings(...)` | Generate Deepchecks embeddings. Can download models or call external APIs. |
| `sample(n_samples, ...)` | Return a sampled `TextData`. |
| `describe(...)` | Create a quick visual overview of labels, metadata, and properties. |
| `is_multi_label_classification()` | Detect multilabel text classification. |

## Supported task formats

### Text classification

Single-label format:

```python
labels = ["positive", "negative", "positive"]
# or integer labels
labels = [0, 1, 0]
```

Multilabel format:

```python
labels = [
    [1, 0, 1],
    [0, 1, 0],
    [1, 1, 0],
]
```

Practical notes:

- Use `task_type='text_classification'` for both single-label and multilabel data.
- For multilabel data, `model_classes` should have the same width as each label row.
- If `model_classes` is omitted for multilabel data, the runtime can fall back to positional class ids.

### Token classification

Token classification uses aligned token sequences and IOB-like labels:

```python
tokenized_text = [
    ["Dan", "lives", "in", "New", "York"],
    ["He", "works", "at", "Google"],
]
labels = [
    ["B-PER", "O", "O", "B-LOC", "I-LOC"],
    ["O", "O", "O", "B-ORG"],
]
```

Practical notes:

- `tokenized_text` is required.
- Labels must be the same length as the corresponding token list.
- Predictions use the same shape as labels.
- Probabilities are not supported for token classification.

## Suite factories

Verified signatures:

```python
data_integrity(n_samples=None, random_state=42, **kwargs) -> Suite
train_test_validation(n_samples=None, random_state=42, **kwargs) -> Suite
model_evaluation(n_samples=None, random_state=42, **kwargs) -> Suite
full_suite(**kwargs)
```

### What each suite is for

| Suite | Best use | Notes |
|---|---|---|
| `data_integrity` | Single-dataset text sanity checks. | Good first pass for labels, tokenization, special characters, duplicates, and property/annotation issues. |
| `train_test_validation` | Train/test or train/inference comparison. | Use when you have two TextData objects and want drift, label mismatch, embeddings drift, or sample-mix checks. |
| `model_evaluation` | After model predictions are available. | Use for performance, prediction drift, and weak-segment checks. |
| `full_suite` | Broad first-pass overview. | It composes the other NLP suites and can surface unsupported-check failures if the input is partial. |

## `Suite.run(...)`

NLP suite run signature:

```python
result = suite.run(
    train_dataset=None,
    test_dataset=None,
    with_display=True,
    train_predictions=None,
    test_predictions=None,
    train_probabilities=None,
    test_probabilities=None,
    model_classes=None,
    random_state=42,
)
```

### Single-dataset checks

```python
result = check.run(
    dataset,
    model=None,
    with_display=True,
    predictions=None,
    probabilities=None,
    model_classes=None,
    random_state=42,
)
```

### Train/test checks

```python
result = check.run(
    train_dataset,
    test_dataset,
    model=None,
    with_display=True,
    train_predictions=None,
    test_predictions=None,
    train_probabilities=None,
    test_probabilities=None,
    model_classes=None,
    random_state=42,
)
```

Practical notes:

- NLP relies heavily on precomputed predictions and probabilities. The `model` parameter is present for interface compatibility, but the safe and common path is to pass prediction arrays directly.
- Always use `with_display=False` in automation, smoke scripts, and CI-style validation when you do not need notebook widgets.

## Predictions and probabilities

### Text classification

- **Predictions**: one label per sample, either strings or ints.
- **Probabilities**: one probability vector per sample, shape `(n_samples, n_classes)`.
- Probability columns must follow the `model_classes` order.
- For binary classification, the vector still has two columns.

Example:

```python
predictions = ["negative", "positive", "positive"]
probabilities = [[0.8, 0.2], [0.1, 0.9], [0.3, 0.7]]
```

### Multilabel text classification

- **Predictions**: binary vectors per sample, shape `(n_samples, n_classes)`.
- **Probabilities**: score vectors per sample, shape `(n_samples, n_classes)`.
- Probability rows do not need to sum to 1, but each value should be in `[0, 1]`.

Example:

```python
predictions = [[1, 0, 1], [0, 1, 0]]
probabilities = [[0.9, 0.2, 0.8], [0.1, 0.7, 0.3]]
```

### Token classification

- **Predictions**: sequence of token labels with the same lengths as the input token lists.
- **Probabilities**: not supported.
- If you pass `model_classes`, omit `O` if you want the runtime to keep only entity classes in downstream metrics; the runtime ignores `O` for token metrics.

Example:

```python
predictions = [
    ["B-PER", "O", "O", "B-LOC", "I-LOC"],
    ["O", "O", "B-ORG"],
]
```

## Properties, metadata, and embeddings

### Metadata

- Use `metadata` for structured sample-level fields such as source, author, time bucket, or segment.
- Set `categorical_metadata` when you want to be explicit about which columns are categorical.
- The row count and row order must match the text rows exactly.

### Properties

- Use `properties` for extracted or precomputed text features.
- Built-in properties can be attached manually or calculated with `calculate_builtin_properties(...)`.
- `categorical_properties` applies to custom properties only.
- Built-in categorical properties such as `Language` are recognized automatically.

Safe built-in property groups to know:

- Default cheap properties: `Text Length`, `Average Word Length`, `Max Word Length`, `% Special Characters`, `% Punctuation`, `Language`, `Sentiment`, `Subjectivity`, `Average Words Per Sentence`, `Reading Ease`, `Lexical Density`
- Long or heavier defaults: `Toxicity`, `Fluency`, `Formality`, `Unique Noun Count`
- Additional built-ins exposed by `include_properties`: `English Text`, `URLs Count`, `Unique URLs Count`, `Email Addresses Count`, `Unique Email Addresses Count`, `Unique Syllables Count`, `Reading Time`, `Sentences Count`, `Average Syllable Length`

`calculate_builtin_properties(...)` signature snapshot:

```python
calculate_builtin_properties(
    include_properties=None,
    ignore_properties=None,
    include_long_calculation_properties=False,
    ignore_non_english_samples_for_english_properties=True,
    device=None,
    models_storage=None,
    batch_size=16,
    cache_models=False,
    use_onnx_models=True,
)
```

### Embeddings

- Use `embeddings` for precomputed vectors attached at construction time.
- Or call `set_embeddings(...)` later.
- Embeddings must stay aligned to the text rows and use shape `(n_samples, embedding_dim)`.

`calculate_builtin_embeddings(...)` signature snapshot:

```python
calculate_builtin_embeddings(
    model='miniLM',
    file_path='embeddings.npy',
    device=None,
    long_sample_behaviour='average+warn',
    open_ai_batch_size=500,
)
```

Practical notes:

- `model='miniLM'` uses the `sentence_transformers` stack and can download the default MiniLM model.
- `model='open_ai'` uses the OpenAI API and network access.
- For offline or smoke usage, prefer precomputed embeddings instead of calling the built-in generator.

## Individual check notes

| Check | Practical note |
|---|---|
| `TextPropertyOutliers` | Requires properties already attached to the `TextData`. |
| `PropertyLabelCorrelation` | Useful for shortcut-learning checks, but not supported for token classification. |
| `TextEmbeddingsDrift` | Requires embeddings on both datasets. |
| `TrainTestPerformance` | Main train/test performance check; works with text, multilabel, and token tasks using the right prediction shapes. |
| `SingleDatasetPerformance` | Single-split performance summary. |
| `PredictionDrift` | Compares prediction distributions between train and test. |
| `MetadataSegmentsPerformance` / `PropertySegmentsPerformance` | Weak-segment analysis; by default relies on predicted probabilities or explicit per-sample scores. |
| `ConfusionMatrixReport` | Single-dataset confusion matrix for text classification. |

## No-download guidance

To keep the runtime local and deterministic:

- Prefer precomputed metadata, properties, and embeddings.
- Pass a local tokenizer stub when you want `UnknownTokens` to run offline.
- Avoid `calculate_builtin_embeddings()` and heavyweight `calculate_builtin_properties()` paths unless you explicitly want model or corpus downloads.
- Use `with_display=False` for automation and smoke runs.
