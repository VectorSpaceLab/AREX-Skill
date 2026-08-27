---
name: classification
description: "Use Simple Transformers classification APIs for text,
  sentence-pair, multilabel, LayoutLM/document, multimodal, regression, ONNX,
  and reranking workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Simple Transformers Classification Sub-skill

Use this sub-skill when the user wants discriminative classification or
cross-encoder reranking with the public `simpletransformers.classification`
APIs. It is self-contained: do not send future agents to the source checkout,
repo docs, tests, or examples for routine usage.

## Owns

- Binary text classification with `ClassificationModel`.
- Multiclass text classification with `ClassificationModel(num_labels=N)`.
- Regression with `ClassificationModel(num_labels=1)` and
  `ClassificationArgs(regression=True)` or `args={"regression": True}`.
- Sentence-pair classification/regression using `text_a`, `text_b`, `labels`
  DataFrames and `predict([[text_a, text_b], ...])`.
- Multi-label text classification with `MultiLabelClassificationModel` and
  multi-hot list labels.
- LayoutLM/LayoutLMv2 document-style classification with `text`, `labels`,
  `x0`, `y0`, `x1`, `y1` list columns and normalized 0-1000 boxes.
- Multimodal text+image classification with `MultiModalClassificationModel`.
- Cross-encoder reranker-style use of `ClassificationModel.rerank()` and
  sentence-pair `predict()` scores.
- Classification model conversion helpers such as `convert_to_onnx()` and
  shared CPU-safe args for output/cache handling.

## Route elsewhere

- Named entity recognition and extractive question answering:
  [token-and-qa](../token-and-qa/SKILL.md).
- T5, Seq2Seq, language modeling, language generation, and text-to-text
  classification/question generation:
  [generative-workflows](../generative-workflows/SKILL.md).
- Dense retrieval, representation vectors, DPR, BEIR/MSMARCO data ownership,
  and retrieval-model reranking:
  [retrieval-representation](../retrieval-representation/SKILL.md).
- Package installation, shared `ModelArgs`, Streamlit viewer, CUDA policy, and
  cross-task output/cache conventions belong to the root skill.

## Read first

1. [API reference](references/api-reference.md) for constructor signatures,
   methods, return shapes, supported model-type strings, and compatibility
   notes.
2. [Data formats](references/data-formats.md) before preparing any DataFrame,
   lazy-loading file, LayoutLM box table, multimodal table, or reranking data.
3. [Workflows](references/workflows.md) for train/eval/predict recipes that do
   not require opening original examples.
4. [Troubleshooting](references/troubleshooting.md) when imports fail, data is
   silently misread, model downloads start unexpectedly, ONNX conversion fails,
   or multimodal/LayoutLM inputs are rejected.

## Safe defaults

Prefer explicit CPU-safe construction unless the user asks for GPU execution:

```python
from simpletransformers.classification import ClassificationArgs, ClassificationModel

args = ClassificationArgs()
args.no_save = True                 # avoid writing checkpoints in smoke runs
args.overwrite_output_dir = True    # required if reusing an output_dir
args.reprocess_input_data = True    # avoid stale cached features while debugging
args.max_seq_length = 128
args.scheduler = "constant_schedule"  # small smoke runs often do not need warmup

model = ClassificationModel(
    "roberta",
    "roberta-base",
    args=args,
    use_cuda=False,
)
```

For real training, let the user choose a writable `output_dir`, remove
`no_save=True`, and consider `evaluate_during_training`, `save_best_model`, and
checkpoint retention settings from the root configuration reference.

## Data validation helper

Before training or evaluating, validate tabular inputs with the bundled helper:

```bash
python scripts/validate_classification_data.py --help
python scripts/validate_classification_data.py --task single --input train.csv
python scripts/validate_classification_data.py --task sentence-pair --input pairs.csv
python scripts/validate_classification_data.py --task multilabel --input multilabel.jsonl --num-labels 6
python scripts/validate_classification_data.py --task layoutlm --input layout.jsonl
python scripts/validate_classification_data.py --task multimodal --input mm.csv --image-root images --check-image-exists
```

The script performs deterministic schema checks only. It does not import
Simple Transformers, download models, train, evaluate, or contact the network.
Use non-zero exits as data-preparation blockers.

## Required decision points

- **Single text vs sentence pair:** choose `text`/`labels` or
  `text_a`/`text_b`/`labels` explicitly. If a DataFrame contains both shapes,
  Simple Transformers will prefer `text`/`labels`; fix ambiguous columns first.
- **Label semantics:** binary and multiclass labels are integer class ids;
  regression labels are floats; multi-label labels are list-like multi-hot
  vectors of only `0`/`1` values.
- **Class count:** pass `num_labels` for multiclass, multilabel, and regression
  (`num_labels=1`). For custom string labels, set `labels_list`/`labels_map`
  where supported and verify the mapped predictions.
- **Long documents:** `ClassificationArgs.sliding_window=True` avoids hard
  truncation for long single-text classification; it is not implemented for
  multi-label and cannot be combined with lazy loading.
- **LayoutLM:** box lists must align with whitespace word count and contain
  normalized integer coordinates in `[0, 1000]` with `x0 <= x1` and `y0 <= y1`.
- **Multimodal:** the DataFrame path stores relative image filenames in
  `images`; `image_path` points to the directory containing those images.
  `MultiModalClassificationModel` only supports `model_type="bert"`.
- **Reranking:** `ClassificationModel.rerank()` is for cross-encoder scoring;
  retrieval dataset construction and dense retrieval ownership are routed to
  `retrieval-representation`.

## Minimal API map

- Text/sentence-pair/regression/LayoutLM:
  `ClassificationModel`, `ClassificationArgs`.
- Multi-label text: `MultiLabelClassificationModel`,
  `MultiLabelClassificationArgs`.
- Text+image multimodal: `MultiModalClassificationModel`,
  `MultiModalClassificationArgs`.
- Core methods: `train_model()`, `eval_model()`, `predict()`, `rerank()`,
  `convert_to_onnx()`.
- Custom classification losses recognized by `ClassificationModel` through
  `args.loss_type`: `"focal"`, `"dice"`, or `"tversky"` with `loss_args`.

## Verification status carried into this sub-skill

- The public signatures and dataclass fields in this sub-skill were checked
  against Simple Transformers 0.70.8 source and package-inspection evidence.
- A safe native candidate named `test_custom_model_post_init` is relevant to
  custom classification heads and Transformers compatibility.
- Full native classification tests and examples download Hugging Face models
  and run training; they are skipped by default unless the user explicitly
  approves time, network/model cache, and compute budget.

## Common next steps

1. Identify which classification family the user wants.
2. Validate the data schema using [data formats](references/data-formats.md)
   and the helper script.
3. Instantiate the right model class with `use_cuda=False` for CPU-only or
   smoke runs.
4. Run the smallest possible `train_model()`/`eval_model()`/`predict()` loop,
   then expand epochs, metrics, outputs, and backend settings only after schema
   and import issues are resolved.
5. If errors mention import aliases, MMBT, ONNX, cache reuse, pytrec, images,
   or LayoutLM boxes, consult [troubleshooting](references/troubleshooting.md)
   before changing model architecture.
