# Troubleshooting

Use this reference when training, evaluation, dataset preparation, or plan validation fails.

## Install and import failures

### `ModuleNotFoundError: datasets` or trainer imports fail

Install the training extra:

```bash
pip install "sentence-transformers[train]"
```

The base package supports inference, but trainer workflows need extra dependencies such as `datasets` and `accelerate`.

### Multimodal rows fail to load or tokenize

Install the modality extras that match the data:

- Images: `sentence-transformers[train,image]`
- Audio: `sentence-transformers[train,audio]`
- Video: `sentence-transformers[train,video]`

For multimodal model-type decisions, route to the model sub-skill first; return here for trainer/evaluator/loss wiring.

### Tracker or Hub integrations fail

- Trackio: install `trackio`; it uses Hugging Face authentication.
- W&B: install and authenticate `wandb`, or set the expected API key in the environment.
- TensorBoard and MLflow: install the selected integration and set `report_to` explicitly.
- Hub push: authenticate with write permission and catch push errors so local training still completes.

## Dataset and API misuse

### `ValueError: dataset has N columns but loss expects M`

All non-label columns are inputs. Drop metadata and reorder input columns:

```python
dataset = dataset.select_columns(["query", "document", "label"])
dataset = dataset.remove_columns(["id", "source"])
```

Label columns must be named `label`, `labels`, `score`, or `scores`. Rename custom labels before training.

### Metrics do not improve

Most common causes:

1. Column order or label detection is wrong.
2. The loss does not match the data shape.
3. Negatives are too easy or false negatives are corrupting the signal.
4. `metric_for_best_model` does not match the evaluator key.
5. `BatchSamplers.NO_DUPLICATES` is missing for in-batch-negative losses.
6. The base model is mismatched to the task or language.
7. The dataset is too small for the selected contrastive loss.

Run `scripts/training_plan_check.py` and print a few dataset rows before debugging hyperparameters.

### Eval is perfect from step zero

The train and eval sets may overlap, or positives are forced into an unrealistic reranking candidate set. Check split construction and decide whether `always_rerank_positives` should be `True` or `False` for the evaluation goal.

### Training hangs at first eval

If `eval_strategy` is `steps` or `epoch`, provide a non-empty `eval_dataset` when required by the trainer, or set `eval_strategy="no"` and rely on explicit evaluator calls.

## Loss and sampler failures

### `CachedMultipleNegativesRankingLoss` or `CachedSpladeLoss` crashes

Cached losses orchestrate their own forward/backward passes. Disable `gradient_checkpointing=True` when using `Cached*` losses.

### Contrastive retrieval gets worse

Set `batch_sampler=BatchSamplers.NO_DUPLICATES` for MNRL, sparse MNRL, cached MNRL, and GIST losses. Duplicate anchors or positives inside a batch become false negatives.

### Batch triplet loss does not learn

Use `BatchSamplers.GROUP_BY_LABEL` and ensure each batch contains multiple examples per label.

### Multi-GPU startup hangs

- Ensure custom datasets implement stable `__len__`.
- Avoid tiny datasets with `NO_DUPLICATES` across many processes; valid batches may be impossible.
- Verify PyTorch/CUDA compatibility and distributed environment variables outside the skill content.

## CrossEncoder-specific failures

### BCE shape mismatch

Use `CrossEncoder(..., num_labels=1)` with `BinaryCrossEntropyLoss`. Use `num_labels>=2` with `CrossEntropyLoss` for multi-class classification.

### Reranker nDCG collapses after listwise or distillation training

For listwise, pairwise, and distillation losses that need raw ranking scores, construct the model with an identity activation. Saturating sigmoid-style activations can destroy rank ordering. Keep the default sigmoid behavior for BCE-style binary training.

### Pair dataset but user wants a reranker

Do not assume listwise training. If rows are `(query, passage, label)` with binary labels, route to `BinaryCrossEntropyLoss`. If rows are only `(query, positive)`, mine negatives. If rows are lists of candidates with labels/scores, use listwise losses and reranking evaluators.

## SparseEncoder-specific failures

### Sparse vectors are dense

Symptoms: `query_active_dims` or `document_active_dims` are in the thousands.

Fixes:

1. Confirm `SpladeLoss` wraps the inner loss.
2. Increase `query_regularizer_weight` or `document_regularizer_weight`.
3. Train long enough for the regularizer scheduler to ramp.
4. Confirm the model is a SPLADE/fill-mask-compatible sparse model.

### Sparse metric improves but deployment is not sparse

Treat this as a regression unless active dimensions are healthy. A learned sparse model should maintain useful nDCG/MRR and sparse active dimensions.

### Active dimensions are near zero

Regularization may be too strong, training may be too short, or the learning rate may be too low. Lower regularizer weights and inspect the first smoke-test batches.

## Resource and backend limits

### CUDA out of memory

Try, in order:

1. Reduce `per_device_train_batch_size`.
2. Use cached losses for MNRL-style dense/sparse training instead of gradient accumulation when in-batch negatives matter.
3. Use `gradient_accumulation_steps` for non-contrastive losses.
4. Enable `gradient_checkpointing=True` when not using cached losses.
5. Shorten `max_seq_length`.
6. Use LoRA/PEFT for large bases.
7. Move to a larger GPU or multi-GPU run.

### Loss is `NaN` or `Inf`

Drop learning rate first, add or increase warmup, switch fp16 to bf16 when supported, inspect labels for NaN/strings, check empty text rows, and add gradient clipping only after data and LR are sane.

### External services or optional backends fail

Training and evaluation should not require vector databases, ONNX, OpenVINO, Elasticsearch, OpenSearch, Qdrant, or FAISS unless the user selected those paths. Route backend export problems to the backend export sub-skill. For hard-negative mining with `use_faiss=True`, install FAISS or set `use_faiss=False`.

## Model-card and saved-model issues

### Model card missing or incomplete

Pass explicit model-card metadata: base model, dataset names, language, license, intended use, tags, and evaluation results. If prompts are used, save them with the model so `encode(prompt_name=...)` works after reload.

### Saved model with custom module cannot reload

Do not define custom `nn.Module` classes only inside the training script. Put them in an importable module before saving, or use built-in sentence-transformers modules.

## Preflight command

Before writing a long training script, run:

```bash
python sub-skills/evaluation-and-training/scripts/training_plan_check.py --help
```

Then validate the proposed model/data/loss/evaluator route. This catches common mismatches but does not replace a real `max_steps=1` smoke test.
