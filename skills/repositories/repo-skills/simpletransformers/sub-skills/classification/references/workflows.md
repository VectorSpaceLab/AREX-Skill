# Classification Workflows

## CPU smoke workflow

Use this when a user needs to prove schema/API wiring before spending time on large models.

```python
import pandas as pd
from simpletransformers.classification import ClassificationArgs, ClassificationModel

train_df = pd.DataFrame(
    [["Example sentence for class 1", 1], ["Example sentence for class 0", 0]],
    columns=["text", "labels"],
)
eval_df = train_df.copy()

args = ClassificationArgs()
args.no_save = True
args.overwrite_output_dir = True
args.reprocess_input_data = True
args.max_seq_length = 32
args.train_batch_size = 2
args.eval_batch_size = 2
args.num_train_epochs = 1
args.scheduler = "constant_schedule"

model = ClassificationModel("roberta", "roberta-base", args=args, use_cuda=False)
model.train_model(train_df)
result, outputs, wrong = model.eval_model(eval_df)
predictions, raw_outputs = model.predict(["A new short sentence"])
```

This still downloads `roberta-base` unless the model is cached. For no-network data checks, run the validator script instead of constructing the model.

## Multiclass / regression changes

- Multiclass: pass `num_labels=N` and use integer labels `0..N-1`.
- Regression: pass `num_labels=1` and `args={"regression": True}` or `ClassificationArgs(regression=True)`; labels should be floats.
- For custom label strings, create an explicit mapping and keep it with the model artifacts.

## Sentence-pair classification

Use `text_a`, `text_b`, `labels` columns. Predictions are nested pairs, not concatenated strings.

```python
pairs = pd.DataFrame(
    [["The sky is blue", "The sky has color", 1], ["Cats purr", "Rocks fly", 0]],
    columns=["text_a", "text_b", "labels"],
)
model = ClassificationModel("roberta", "roberta-base", args={"no_save": True}, use_cuda=False)
model.train_model(pairs)
model.predict([["A", "B"], ["C", "D"]])
```

## Multi-label workflow

```python
from simpletransformers.classification import MultiLabelClassificationModel

train_df = pd.DataFrame(
    [["first", [1, 0, 1]], ["second", [0, 1, 0]]],
    columns=["text", "labels"],
)
model = MultiLabelClassificationModel(
    "roberta",
    "roberta-base",
    num_labels=3,
    args={"no_save": True, "overwrite_output_dir": True, "num_train_epochs": 1},
    use_cuda=False,
)
model.train_model(train_df)
model.predict(["new text"])
```

If label vectors came from CSV, convert them from strings to lists first.

## LayoutLM/document classification workflow

1. Normalize all coordinates to `0..1000` relative to page width/height.
2. Ensure one x/y box per whitespace token in `text`.
3. Validate with `validate_classification_data.py --task layoutlm`.
4. Use a LayoutLM model type/name and CPU for smoke tests.

Do not use LayoutLM as a generic long-document classifier. Use `sliding_window=True` for ordinary long text if the selected model family supports it.

## Multimodal workflow

1. Build rows with text, labels, and image filename(s).
2. Keep image paths relative to `image_path`.
3. Validate metadata and image existence separately.
4. Instantiate `MultiModalClassificationModel("bert", <bert-name>, ...)`.

MMBT/multimodal classes depend on deprecated Transformers modules in some environments. If imports fail before data validation, handle dependency compatibility first.

## Reranking workflow

For cross-encoder reranking, classification can score query-passage pairs. Use this when the user already has candidate passages. Use [retrieval-representation](../../retrieval-representation/SKILL.md) when the task must build an index, encode passages, mine hard negatives, or evaluate BEIR/MSMARCO metrics.

## Saving and cache policy

- For smoke tests: `no_save=True`, unique temporary `output_dir`, `reprocess_input_data=True`.
- For real runs: choose persistent `output_dir`, keep `best_model_dir`, and set checkpoint retention intentionally.
- If a result looks stale, clear or change `cache_dir` / `dataset_cache_dir` rather than assuming the model is wrong.
