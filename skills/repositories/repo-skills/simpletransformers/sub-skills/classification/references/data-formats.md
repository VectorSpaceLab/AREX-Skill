# Classification Data Formats

## When to read

Read this before preparing `train_model()`, `eval_model()`, or `predict()` inputs for classification tasks. Use the bundled `scripts/validate_classification_data.py` to catch schema mistakes before model downloads or training.

## Single-text binary / multiclass

Training and evaluation data can be a Pandas DataFrame with columns:

| column | type | notes |
|---|---|---|
| `text` | string | input sequence |
| `labels` | integer | binary labels are `0`/`1`; multiclass labels start at `0` and should be contiguous class ids |

Prediction input is a list of strings:

```python
to_predict = ["Gandalf was a Wizard", "Sam was a Wizard"]
```

## Regression

Use the same single-text columns but set continuous float labels and enable regression:

```python
from simpletransformers.classification import ClassificationArgs, ClassificationModel
args = ClassificationArgs(regression=True, num_train_epochs=1)
model = ClassificationModel("roberta", "roberta-base", num_labels=1, args=args, use_cuda=False)
```

## Sentence-pair classification/regression

Training/eval DataFrames need columns:

| column | type | notes |
|---|---|---|
| `text_a` | string | first sequence |
| `text_b` | string | second sequence |
| `labels` | integer or float | class id or regression target |

Prediction input is a list of two-item lists:

```python
to_predict = [["Gimli fought with a battle axe", "Gimli used an axe"]]
```

Avoid DataFrames that contain both `text` and `text_a`/`text_b` unless you deliberately know which branch the library will use.

## Multi-label classification

Training/eval DataFrames need columns:

| column | type | notes |
|---|---|---|
| `text` | string | input sequence |
| `labels` | list[int] | multi-hot vector with only `0`/`1`; length should match `num_labels` |

CSV round-trips often turn lists into strings. Parse or validate them before calling `train_model()`.

## LayoutLM-style document classification

For `model_type` such as `layoutlm` or `layoutlmv2`, use text plus normalized bounding-box list columns:

| column | type | notes |
|---|---|---|
| `text` | string | whitespace tokenization should align with box lists |
| `labels` | int/float/list | task-dependent target |
| `x0`, `y0`, `x1`, `y1` | list[int] | one coordinate per word, normalized to `[0, 1000]`; require `x0 <= x1`, `y0 <= y1` |

Prediction inputs are list-like samples containing text plus the four coordinate lists. If pandas turns list columns into strings, convert them back to Python lists before prediction.

## Multimodal text+image classification

The public model uses a DataFrame with text, labels, and image identifiers. Default args names are:

| column | default arg | notes |
|---|---|---|
| `text` | `text_label` | text input |
| `labels` | `labels_label` | int class id, float regression target, or multilabel vector when `multi_label=True` |
| `images` | `images_label` | image filename(s) relative to the `image_path` argument used during model calls |

Keep image paths relative and validate them separately before running training. The bundled validator can optionally check existence under an image root, but it does not open or decode the image.

## Lazy loading

Lazy loading uses a file path instead of an in-memory DataFrame. Default delimiter is tab. Important args include:

- `lazy_loading=True`
- `lazy_delimiter="\t"`
- `lazy_text_column=0`, `lazy_labels_column=1`
- sentence-pair equivalents `lazy_text_a_column`, `lazy_text_b_column`
- `lazy_loading_start_line` for headers

Multi-label lazy loading is documented as not implemented. Treat user requests for multilabel lazy loading as unsupported unless they have confirmed a newer package version.

## Validation helper examples

```bash
python scripts/validate_classification_data.py --task single --input train.csv
python scripts/validate_classification_data.py --task sentence-pair --input pairs.jsonl
python scripts/validate_classification_data.py --task multilabel --input multilabel.jsonl --num-labels 6
python scripts/validate_classification_data.py --task layoutlm --input layout.jsonl
python scripts/validate_classification_data.py --task multimodal --input multimodal.csv --image-root images --check-image-exists
```

The helper accepts CSV or JSONL records. It reports row numbers, missing columns, invalid labels, malformed list columns, LayoutLM coordinate mismatches, and missing image files when requested.
