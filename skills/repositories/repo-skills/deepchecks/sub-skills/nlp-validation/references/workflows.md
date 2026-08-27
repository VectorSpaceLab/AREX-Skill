# NLP Workflows

These recipes use tiny local examples and precomputed tables. They are safe to adapt offline and do not depend on external example files.

## 1) Text classification

Use `task_type='text_classification'` for single-label or multilabel text tasks.

```python
import numpy as np
import pandas as pd
from deepchecks.nlp import TextData
from deepchecks.nlp.suites import data_integrity, train_test_validation, model_evaluation

train_texts = [
    "great product and fast shipping",
    "poor quality and bad support",
    "great value and friendly service",
    "not worth the price",
    "easy setup and nice packaging",
    "very slow delivery",
    "excellent experience overall",
    "broken on arrival",
    "works as expected",
    "would buy again",
    "good quality for the price",
    "customer service was helpful",
]
train_labels = ["positive", "negative", "positive", "negative", "positive", "negative",
                "positive", "negative", "positive", "positive", "positive", "positive"]

train_metadata = pd.DataFrame({
    "source": ["web", "web", "app", "app", "web", "app", "web", "web", "app", "app", "web", "app"],
    "age_band": ["18-25", "26-35", "18-25", "26-35", "18-25", "26-35", "18-25", "26-35", "18-25", "26-35", "18-25", "26-35"],
})

train_properties = pd.DataFrame({
    "Text Length": [len(x) for x in train_texts],
    "Average Word Length": [round(sum(len(w) for w in x.split()) / len(x.split()), 2) for x in train_texts],
    "Language": ["en"] * len(train_texts),
    "tone_bucket": ["short" if len(x) < 25 else "long" for x in train_texts],
})

train_embeddings = np.column_stack([
    np.arange(len(train_texts), dtype=float),
    np.array([len(x) for x in train_texts], dtype=float),
    np.array([sum(map(len, x.split())) for x in train_texts], dtype=float),
    np.array([i % 3 for i in range(len(train_texts))], dtype=float),
])

train = TextData(
    raw_text=train_texts,
    label=train_labels,
    task_type="text_classification",
    metadata=train_metadata,
    categorical_metadata=["source", "age_band"],
    properties=train_properties,
    categorical_properties=["tone_bucket"],
    embeddings=train_embeddings,
    name="Train",
)
```

For a tiny no-download data-integrity run, pass a local tokenizer stub so `UnknownTokens` never reaches the Hugging Face default model.

```python
class TinyWhitespaceTokenizer:
    def __init__(self, texts):
        self.unk_token_id = 1
        self.is_fast = True
        self.model_max_length = 10**9
        self.special_tokens_map = {
            "cls_token": "[CLS]",
            "sep_token": "[SEP]",
            "pad_token": "[PAD]",
            "unk_token": "[UNK]",
        }
        self._vocab = {"[PAD]": 0, "[UNK]": 1, "[CLS]": 101, "[SEP]": 102}
        for text in texts:
            for token in text.split():
                self._vocab.setdefault(token, len(self._vocab) + 1)

    def tokenize(self, text):
        return text.split()

    def convert_tokens_to_ids(self, token):
        return self._vocab.get(token, self.unk_token_id)

    def __call__(self, texts, **kwargs):
        input_ids = []
        offsets = []
        for text in texts:
            ids = [self.convert_tokens_to_ids("[CLS]")]
            spans = [(0, 0)]
            cursor = 0
            for token in text.split():
                start = text.find(token, cursor)
                end = start + len(token)
                cursor = end + 1
                ids.append(self.convert_tokens_to_ids(token))
                spans.append((start, end))
            ids.append(self.convert_tokens_to_ids("[SEP]"))
            spans.append((0, 0))
            input_ids.append(ids)
            offsets.append(spans)
        return {"input_ids": input_ids, "offset_mapping": offsets}

suite = data_integrity(tokenizer=TinyWhitespaceTokenizer(train_texts)).run(train, with_display=False)
```

When you have a train/test split and precomputed predictions, use the other suite factories:

```python
test = TextData(
    raw_text=[
        "late delivery but decent quality",
        "excellent packaging and quick shipping",
        "support was rude and unhelpful",
        "fair price and good value",
        "arrived damaged and unusable",
        "works perfectly out of the box",
        "great performance and easy setup",
        "not recommended at all",
        "nice build quality",
        "very happy with the purchase",
        "helpful support and good results",
        "shipping was slower than expected",
    ],
    label=["negative", "positive", "negative", "positive", "negative", "positive",
           "positive", "negative", "positive", "positive", "positive", "negative"],
    task_type="text_classification",
    metadata=train_metadata.copy(),
    categorical_metadata=["source", "age_band"],
    properties=train_properties.copy(),
    categorical_properties=["tone_bucket"],
    embeddings=train_embeddings.copy(),
    name="Test",
)

train_predictions = list(train.label)
test_predictions = list(test.label)
train_probabilities = [[0.15, 0.85] if label == "positive" else [0.88, 0.12] for label in train.label]
test_probabilities = [[0.20, 0.80] if label == "positive" else [0.82, 0.18] for label in test.label]

train_test_validation(n_samples=12).run(train, test, with_display=False)
model_evaluation(n_samples=12).run(
    train,
    test,
    train_predictions=train_predictions,
    test_predictions=test_predictions,
    train_probabilities=train_probabilities,
    test_probabilities=test_probabilities,
    model_classes=["negative", "positive"],
    with_display=False,
)
```

## 2) Token classification

Token classification requires `tokenized_text` and label sequences with exactly the same lengths.

```python
from deepchecks.nlp import TextData
from deepchecks.nlp.suites import data_integrity, train_test_validation, model_evaluation

train_tokens = [
    ["Dan", "lives", "in", "New", "York"],
    ["He", "works", "at", "Google"],
    ["Mary", "visited", "Paris"],
    ["Tom", "joined", "OpenAI"],
    ["Amy", "moved", "to", "London"],
    ["They", "met", "in", "Berlin"],
    ["Sara", "studies", "at", "MIT"],
    ["John", "plays", "guitar"],
    ["Liam", "likes", "coffee"],
    ["Mia", "travels", "often"],
    ["Noah", "reads", "books"],
    ["Eve", "works", "remotely"],
]
train_labels = [
    ["B-PER", "O", "O", "B-LOC", "I-LOC"],
    ["O", "O", "O", "B-ORG"],
    ["B-PER", "O", "B-LOC"],
    ["B-PER", "O", "B-ORG"],
    ["B-PER", "O", "O", "B-LOC"],
    ["O", "O", "O", "B-LOC"],
    ["B-PER", "O", "O", "B-ORG"],
    ["B-PER", "O", "O"],
    ["B-PER", "O", "O"],
    ["B-PER", "O", "O"],
    ["B-PER", "O", "O"],
    ["B-PER", "O", "O"],
]

train = TextData(
    raw_text=[" ".join(tokens) for tokens in train_tokens],
    tokenized_text=train_tokens,
    label=train_labels,
    task_type="token_classification",
    name="Train",
)
```

Practical notes:

- `tokenized_text` is the canonical input for this task.
- Do not pass probabilities; token classification does not support them.
- Use `TrainTestPerformance` or `SingleDatasetPerformance` with token scorer names such as `f1_macro`, `precision_macro`, and `recall_macro`.

Example run:

```python
predictions = [list(row) for row in train.label]
train_test_validation(n_samples=12).run(train, test, with_display=False)
model_evaluation(n_samples=12).run(
    train,
    test,
    train_predictions=predictions,
    test_predictions=predictions,
    with_display=False,
)
```

## 3) Multilabel text classification

Multilabel text classification still uses `task_type='text_classification'`, but each label row is a binary vector.

```python
import numpy as np
from deepchecks.nlp import TextData

texts = [
    "clean build and fast delivery",
    "great taste but expensive",
    "easy to use and reliable",
    "delivery was late and packaging was damaged",
    "excellent support and value",
    "works well for daily tasks",
    "good design but poor battery",
    "very compact and lightweight",
    "nice features and stable performance",
    "too noisy for my office",
    "quick setup and intuitive controls",
    "not worth the money",
]
labels = np.array([
    [1, 0, 1],
    [1, 1, 0],
    [1, 0, 0],
    [0, 1, 1],
    [1, 0, 1],
    [1, 0, 0],
    [1, 1, 0],
    [1, 0, 0],
    [1, 0, 1],
    [0, 1, 0],
    [1, 0, 0],
    [0, 1, 1],
], dtype=int)

train = TextData(raw_text=texts, label=labels, task_type="text_classification", name="Train")
```

For model evaluation:

```python
predictions = labels.copy()
probabilities = np.clip(labels * 0.8 + 0.1, 0, 1)

result = model_evaluation(n_samples=12).run(
    train,
    train.copy(),
    train_predictions=predictions,
    test_predictions=predictions,
    train_probabilities=probabilities,
    test_probabilities=probabilities,
    model_classes=["bug", "feature", "quality"],
    with_display=False,
)
```

Practical notes:

- Each label row must have the same length.
- If `model_classes` is omitted, the runtime can fall back to positional labels.
- Probability rows do not need to sum to 1.

## 4) Metadata, properties, and embeddings

Use the same row order for all attached tables.

### Metadata

```python
metadata = pd.DataFrame({
    "source": ["web", "app", "web", "app"],
    "channel": ["organic", "paid", "organic", "paid"],
    "age_band": ["18-25", "26-35", "18-25", "26-35"],
})
text_data = TextData(raw_text=texts, metadata=metadata, categorical_metadata=["source", "channel"])
```

### Properties

```python
properties = pd.DataFrame({
    "Text Length": [len(text) for text in texts],
    "Average Word Length": [round(sum(len(w) for w in text.split()) / len(text.split()), 2) for text in texts],
    "Language": ["en"] * len(texts),
    "topic_bucket": ["short" if len(text) < 25 else "long" for text in texts],
})
text_data.set_properties(properties, categorical_properties=["topic_bucket"])
```

Safe property patterns:

- Prefer precomputed properties when you need deterministic offline smoke runs.
- If you intentionally calculate built-in properties, keep the property list small and cheap unless you explicitly want heavyweight models or corpora.
- Use `Text Length`, `Average Word Length`, `% Special Characters`, `% Punctuation`, or other simple local features when you only need a tiny offline proof of shape.

### Embeddings

```python
import numpy as np

embeddings = np.array([
    [0.1, 0.2, 0.3, 0.4],
    [0.4, 0.3, 0.2, 0.1],
    [0.2, 0.1, 0.4, 0.3],
    [0.3, 0.4, 0.1, 0.2],
])
text_data.set_embeddings(embeddings)
```

Safe embedding patterns:

- Use `set_embeddings()` or the constructor `embeddings=` parameter for offline runs.
- Use `calculate_builtin_embeddings()` only when you explicitly want the MiniLM/OpenAI embedding workflow.
- Keep the array shape exactly `(n_samples, embedding_dim)`.

## 5) Model evaluation workflow

The model-evaluation path usually needs two things:

1. labels on both train and test data
2. precomputed predictions, and sometimes probabilities

A practical no-model pattern looks like this:

```python
from deepchecks.nlp.suites import model_evaluation

suite = model_evaluation(n_samples=12)
result = suite.run(
    train_dataset=train,
    test_dataset=test,
    train_predictions=train_predictions,
    test_predictions=test_predictions,
    train_probabilities=train_probabilities,
    test_probabilities=test_probabilities,
    model_classes=["negative", "positive"],
    with_display=False,
)
```

Notes:

- `TrainTestPerformance` and `PredictionDrift` can work from predictions alone.
- `MetadataSegmentsPerformance` and `PropertySegmentsPerformance` usually need probabilities or a custom `score_per_sample` input.
- `ConfusionMatrixReport` is a single-dataset check for text classification.
- For token classification, keep probabilities out of the call.

## 6) No-download patterns

Use these when the goal is a deterministic smoke helper:

1. Build `TextData` from local lists, DataFrames, and ndarrays.
2. Attach precomputed metadata, properties, and embeddings.
3. Pass a local tokenizer stub to `data_integrity()` if you want `UnknownTokens` to stay offline.
4. Use `with_display=False` in any automation.
5. Avoid built-in generators that fetch models or corpora unless the workflow explicitly needs them.

A compact offline route for the smoke helper is:

```python
data_integrity(tokenizer=TinyWhitespaceTokenizer(train_texts)).run(train, with_display=False)
train_test_validation(n_samples=12).run(train, test, with_display=False)
```

This keeps the runtime path local while still exercising the deepchecks API shapes.
