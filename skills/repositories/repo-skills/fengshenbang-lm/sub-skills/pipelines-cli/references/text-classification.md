# Text Classification Pipeline

## What this surface covers

Use `TextClassificationPipeline` for single-sentence or pair classification with a Hugging Face/Fengshen sequence-classification model. The public class lives at:

```python
from fengshen.pipelines.text_classification import TextClassificationPipeline
```

The console route is:

```bash
fengshen-pipeline text_classification predict|train ...
```

Real prediction or training may download model weights, tokenizers, and datasets. Use help/parser checks before model execution.

## Prediction shape

The README-style single command is:

```bash
fengshen-pipeline text_classification predict \
  --model IDEA-CCNL/Erlangshen-Roberta-110M-Similarity \
  --text '今天心情不好[SEP]今天很开心'
```

Expected output is a Transformers text-classification result such as:

```text
[{'label': 'not similar', 'score': 0.9988}]
```

Notes:

- `--text` is one string. The public example uses `[SEP]` inside the string for a pair-classification model.
- For structured training data, use separate fields and set `--texta_name` / `--textb_name`.
- `--device -1` means CPU. Non-negative devices use the Transformers/PyTorch device route and require matching CUDA runtime.

## Training with a public Hugging Face dataset

The console `train` path calls `datasets.load_dataset(args.datasets)` and passes the returned dataset dict into `TextClassificationPipeline.train(datasets)`.

Example pattern:

```bash
fengshen-pipeline text_classification train \
  --model IDEA-CCNL/Erlangshen-Roberta-110M-Similarity \
  --datasets IDEA-CCNL/AFQMC \
  --texta_name sentence1 \
  --textb_name sentence2 \
  --label_name label \
  --max_length 128 \
  --gpus 0
```

Use this only when the dataset is intentionally fetched or already cached. For local JSONL without AFQMC, use the local route below.

## Local JSONL without AFQMC download

Generate a tiny fixture:

```bash
python scripts/make_classification_fixture.py --out-dir ./fengshen-classification-fixture
```

Fixture schema, one JSON object per line:

```json
{"id": 0, "sentence": "今天心情很好", "sentence2": "今天很开心", "label": 1}
{"id": 1, "sentence": "天气很好", "sentence2": "我想吃火锅", "label": 0}
```

Important: for the pipeline collator, `label` should already be an integer class id. If your source labels are strings, map them to ids before training or use a dataset transform that converts them.

The generic console command does not expose `datasets.load_dataset('json', data_files=...)`. Use a short Python route for local files:

```python
import argparse
from datasets import load_dataset
from fengshen.pipelines.text_classification import TextClassificationPipeline

parser = argparse.ArgumentParser()
parser.add_argument('--model', required=True)
parser = TextClassificationPipeline.add_pipeline_specific_args(parser)
args = parser.parse_args([
    '--model', 'MODEL_OR_LOCAL_DIR',
    '--texta_name', 'sentence',
    '--textb_name', 'sentence2',
    '--label_name', 'label',
    '--max_length', '128',
    '--gpus', '0',
])

datasets = load_dataset('json', data_files={
    'train': './fengshen-classification-fixture/train.json',
    'validation': './fengshen-classification-fixture/dev.json',
    'test': './fengshen-classification-fixture/test.json',
})
pipe = TextClassificationPipeline(args=args, model=args.model)
pipe.train(datasets)
```

This route still downloads the model unless `MODEL_OR_LOCAL_DIR` is a local model directory or a cached model id.

## Field and argument guide

| Concept | Default / example | Notes |
|---|---|---|
| First text | `sentence` | Set with `--texta_name`. Required for every sample. |
| Second text | `sentence2` | Set with `--textb_name`. Can be an empty string or absent for single-text classification. |
| Label | `label` | Set with `--label_name`. Must be numeric for the pipeline collator. |
| Id | `id` | Not used by the pipeline collator, but useful for traceability and compatible with example scripts. |
| Max length | `--max_length 128` or `512` | Passed to tokenizer with max-length padding/truncation. |
| Model type | inferred from config | If config has `fengshen_model_type`, the pipeline maps it to a Fengshen custom class; otherwise it uses Hugging Face auto sequence classification. Route mapping issues to `model-zoo`. |
| Trainer/checkpoint flags | `--gpus`, `--max_epochs`, `--strategy`, `--dirpath`, etc. | Added by PyTorch Lightning, UniversalCheckpoint, and model utility helpers. Route detailed training-argument debugging to `data-training`. |

## Common adaptation decisions

- If the user says “do not download AFQMC,” do not pass `--datasets IDEA-CCNL/AFQMC`; create or use local JSONL and load it through the Python `datasets.load_dataset('json', data_files=...)` route.
- If labels are strings, add an explicit label-to-id preprocessing step. The standalone classification example can infer labels, but `TextClassificationPipeline` itself expects tensorable numeric labels.
- If pair fields are named `sentence1` and `sentence2`, set `--texta_name sentence1 --textb_name sentence2`.
- If only one text field exists, keep `--textb_name` at a field that is absent or empty and ensure every row has the first text field.
- For model-selection failures involving `fengshen_model_type`, tokenizers, or custom model classes, route to `model-zoo`.
