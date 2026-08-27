# Training Reference

Use this reference to scaffold safe training workflows for `SentenceTransformerTrainer`, `CrossEncoderTrainer`, and `SparseEncoderTrainer` without copying large network-dependent examples.

## Prerequisites

Install the package with training dependencies before any trainer workflow:

```bash
pip install "sentence-transformers[train]"
```

The `train` extra supplies the trainer-facing stack such as `datasets` and `accelerate`. Add modality extras only when the training rows contain those modalities, for example `sentence-transformers[train,image]` for image data. Use tracker packages only when needed, such as `trackio`, `wandb`, `tensorboard`, or `mlflow`.

## Trainer classes

| Model type | Model class | Trainer | Training args | Typical use |
| --- | --- | --- | --- | --- |
| Dense bi-encoder | `SentenceTransformer` | `SentenceTransformerTrainer` | `SentenceTransformerTrainingArguments` | Embeddings, retrieval, STS, clustering, classification heads, distillation |
| Reranker / pair classifier | `CrossEncoder` | `CrossEncoderTrainer` | `CrossEncoderTrainingArguments` | Query-document reranking, pair classification, continuous pair scoring |
| Learned sparse retrieval | `SparseEncoder` | `SparseEncoderTrainer` | `SparseEncoderTrainingArguments` | SPLADE-style sparse retrieval and sparse distillation |

All three trainers follow the Hugging Face `Trainer` lifecycle and accept `model`, `args`, `train_dataset`, optional `eval_dataset`, optional `evaluator`, and a `loss` module or loss factory. Prefer the type-specific training-args class so sampler, router, and model-card fields are available.

## Dataset contract

- Trainers expect `datasets.Dataset` for one dataset or `datasets.DatasetDict` / dictionaries for multiple datasets.
- A label column must be named `label`, `labels`, `score`, or `scores`.
- Every non-label column is treated as an input. Column order matters more than column name.
- Drop metadata columns before training unless a custom collator explicitly consumes them.
- Convert CSV-loaded string labels to numeric labels before training.
- For `DatasetDict` or dictionary multi-task training, align each dataset with the loss that expects its row shape.

Common reshapes:

```python
dataset = dataset.select_columns(["query", "document", "label"])
dataset = dataset.rename_column("relevance", "label")
dataset = dataset.remove_columns(["id", "source", "timestamp"])
dataset = dataset.map(lambda row: {"label": float(row["label"])})
```

## Training arguments that matter

Start with simple, explicit arguments and change only for a known reason:

- `output_dir`: one run-specific directory, usually under `models/`.
- `num_train_epochs` or `max_steps`: choose one duration control; `max_steps` overrides epochs.
- `per_device_train_batch_size`: push high for in-batch-negative losses; keep lower for cross-encoder listwise losses.
- `learning_rate`: `2e-5` is a safe full-finetuning default; LoRA often needs `1e-4` to `5e-4`; static embeddings can need much higher rates.
- `warmup_steps`: a float below `1` is a fraction of total steps; this is preferred over deprecated `warmup_ratio` style.
- `bf16=True` or `fp16=True`: use trainer autocast, not pre-casting model weights to low precision.
- `eval_strategy`, `eval_steps`, `save_strategy`, `save_steps`: keep save/eval cadence aligned when `load_best_model_at_end=True`.
- `metric_for_best_model`: must exactly match the evaluator metric key; see `evaluation-reference.md`.
- `report_to`: set intentionally (`trackio`, `wandb`, `tensorboard`, `mlflow`, or `none`).
- `seed`: set for comparable runs, but do not promise bit-for-bit reproducibility across hardware.

Load models in fp32 where possible and let `bf16` or `fp16` autocast activations. Avoid `model_kwargs={"torch_dtype": "bfloat16"}` for training unless you intentionally accept optimizer-state precision trade-offs.

## Samplers

Import samplers from `sentence_transformers.base.sampler`:

```python
from sentence_transformers.base.sampler import BatchSamplers, MultiDatasetBatchSamplers
```

- `BatchSamplers.NO_DUPLICATES`: critical for `MultipleNegativesRankingLoss`, sparse MNRL, GIST-style losses, and cached variants so duplicate anchors/positives do not become false negatives.
- `BatchSamplers.GROUP_BY_LABEL`: required for batch triplet losses that need multiple examples per label in the same batch.
- `BatchSamplers.NO_DUPLICATES_HASHED`: use only when very large datasets make per-batch string comparison too slow.
- `MultiDatasetBatchSamplers.PROPORTIONAL`: default-like behavior; samples larger datasets more often.
- `MultiDatasetBatchSamplers.ROUND_ROBIN`: useful when each dataset should contribute evenly regardless of size.

Do not use non-default batch samplers with `IterableDataset` unless the trainer supports that exact setup; many sampler strategies require a known finite dataset length.

## Safe workflow scaffold

1. Identify model type and task: dense embedding, cross-encoder reranker/classifier, or sparse retrieval.
2. Inspect five to ten rows and normalize columns to the loss's expected shape.
3. Choose loss using `loss-routing.md`; choose evaluator using `evaluation-reference.md`.
4. Create the model in fp32 when feasible; set model-card metadata early if publishing.
5. Build training args with explicit sampler, eval/save cadence, metric key, tracker, and output directory.
6. Instantiate trainer and run `evaluator(model)` before training to capture a baseline.
7. Smoke-test with a tiny subset and `max_steps=1`.
8. Run training, load the best checkpoint when configured, then run the evaluator again.
9. Compare final metric to baseline and emit a clear `WIN`, `MARGINAL`, or `REGRESSION` verdict for downstream review.
10. Save locally and push to the Hub only after authentication and model-card fields are correct.

## Model-card metadata

Use the model-card data classes when the model should be published or audited:

- `SentenceTransformerModelCardData` for dense models.
- Cross-encoder and sparse workflows also generate model cards through their model/trainer stack; pass explicit metadata such as language, license, base model, datasets, tags, and intended use when available.
- If prompts are part of the trained model, set them on the model or model-card metadata before `save_pretrained()` so later `encode(prompt_name=...)` calls behave as expected.
- If a custom module is used, define it in an importable Python module before saving; inline `__main__` modules make the saved model hard to reload.

## Baseline and smoke-test practices

- Always run the evaluator before `trainer.train()`. A post-training score without a baseline is hard to interpret.
- Use `max_steps=1` plus tiny slices for an initial smoke test. This validates imports, dataset columns, loss forward pass, evaluator, checkpointing, and logging before long runs.
- For cross-encoders, add `EarlyStoppingCallback(early_stopping_patience=3)` when using step-wise evaluation and `load_best_model_at_end=True`; rerankers often peak before the final epoch.
- For sparse encoders, inspect `query_active_dims` and `document_active_dims` in addition to nDCG/MRR. Good retrieval metrics with dense sparse vectors is not a successful sparse model.

## Multi-dataset patterns

For multi-task dense or sparse training, pass a dataset mapping and a loss mapping with matching keys. Decide sampler behavior explicitly:

```python
args = SentenceTransformerTrainingArguments(
    output_dir="models/multi-task",
    multi_dataset_batch_sampler=MultiDatasetBatchSamplers.PROPORTIONAL,
)
trainer = SentenceTransformerTrainer(
    model=model,
    args=args,
    train_dataset={"retrieval": retrieval_ds, "sts": sts_ds},
    loss={"retrieval": retrieval_loss, "sts": sts_loss},
)
```

Use `ROUND_ROBIN` when small but important datasets must not be drowned out by a large dataset. Use `PROPORTIONAL` when dataset size should determine contribution.

## Source-script policy

The original training examples and the curated training skill templates are strong evidence, but most full scripts download models/datasets and launch real training. Treat them as reference patterns unless you intentionally copy and adapt a compact template into the runtime skill. This sub-skill bundles only `scripts/training_plan_check.py`, a static plan validator that does not train or download anything.
