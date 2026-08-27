# Training API Reference

This reference summarizes the Transformers training APIs most often needed by coding agents. It is distilled from the inspected Transformers `5.13.0.dev0` docs, examples, and trainer tests.

## Optional Dependency Boundary

- Base `import transformers` can work without PyTorch, but training classes are optional-dependency gated.
- `Trainer`, `Seq2SeqTrainer`, `TrainingArguments`, PyTorch `AutoModelFor*` classes, and most collators require `torch`.
- Example scripts commonly require `datasets`; metrics often require `evaluate`; distributed and no-trainer routes commonly require `accelerate`.
- Prefer explicit failure messages: "install `torch` and training extras" rather than importing `Trainer` at module import time in reusable scripts.

## Core Classes

### `TrainingArguments`

Use `TrainingArguments(...)` to configure a `Trainer` run. Important groups:

- Output: `output_dir`, `overwrite_output_dir`, `save_total_limit`, `save_safetensors`.
- Batch size: `per_device_train_batch_size`, `per_device_eval_batch_size`, `gradient_accumulation_steps`, `auto_find_batch_size`.
- Training duration: `num_train_epochs`, `max_steps`, `learning_rate`, `weight_decay`, `warmup_steps`, `lr_scheduler_type`.
- Evaluation/logging/saving: `eval_strategy`, `eval_steps`, `save_strategy`, `save_steps`, `logging_strategy`, `logging_steps`.
- Best checkpoint: `load_best_model_at_end`, `metric_for_best_model`, `greater_is_better`.
- Precision/performance: `fp16`, `bf16`, `tf32`, `gradient_checkpointing`, `torch_compile`, `torch_compile_backend`, `torch_compile_mode`.
- Data/model interface: `remove_unused_columns`, `label_names`, `include_inputs_for_metrics`, `prediction_loss_only`.
- Distributed/integration: `fsdp`, `fsdp_config`, `deepspeed`, `ddp_find_unused_parameters`, `local_rank`.
- Reproducibility/reporting: `seed`, `data_seed`, `report_to`, `run_name`, `logging_dir`.
- Publishing: `push_to_hub`, `hub_model_id`, `hub_strategy`, `hub_private_repo`, `hub_token`.

Validation behaviors to know:

- `eval_strategy="steps"` requires step cadence; `eval_steps` can fall back to `logging_steps` when valid.
- `load_best_model_at_end=True` requires evaluation and compatible saving. `save_strategy` must match `eval_strategy` unless saving only the best checkpoint, and step-based saves must be a round multiple of evaluations.
- `torch_compile_backend` or `torch_compile_mode` implies `torch_compile=True`.
- `do_eval` becomes true when evaluation strategy is not `"no"`.
- `label_names` is needed for custom or multiple label tensors; avoid using a forward argument named exactly `label`.

### `Seq2SeqTrainingArguments`

Use for summarization, translation, speech seq2seq, and other generation-during-eval tasks. It extends `TrainingArguments` with generation-aware options such as:

- `predict_with_generate=True` for generation metrics.
- Generation length/beam controls such as `generation_max_length` and `generation_num_beams` when appropriate.
- Pair with `Seq2SeqTrainer` and a seq2seq data collator.

### `Trainer`

Typical constructor fields:

```python
Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    processing_class=tokenizer_or_processor,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)
```

Key methods:

- `trainer.train()` starts training.
- `trainer.train(resume_from_checkpoint="checkpoint-dir")` resumes from a checkpoint.
- `trainer.evaluate()` runs evaluation.
- `trainer.predict(test_dataset)` runs prediction.
- `trainer.save_model()` saves model plus processing assets when available.
- `trainer.push_to_hub()` uploads model artifacts when Hub configuration and auth are valid.

Interface constraints:

- Dataset items must contain fields accepted by `model.forward(...)` after `remove_unused_columns` pruning.
- Labels must be named consistently (`labels` for most tasks; custom names via `label_names`).
- `processing_class` supersedes older tokenizer-only patterns and lets `Trainer` save tokenizer/processor assets.

### `Seq2SeqTrainer`

Use when evaluation or prediction needs generated sequences. Pair with:

- `AutoModelForSeq2SeqLM` or compatible speech/text seq2seq model.
- `DataCollatorForSeq2Seq`.
- `Seq2SeqTrainingArguments(predict_with_generate=True, ...)`.
- Metrics that decode generated token IDs and labels.

## Data Collators

Choose the collator based on the batch shape, not just the model family.

- `DefaultDataCollator`: stacks already padded numeric fields; minimal transformation.
- `DataCollatorWithPadding(tokenizer)`: dynamically pads tokenized classification/QA-like samples.
- `DataCollatorForLanguageModeling(tokenizer, mlm=False)`: causal LM; labels are usually shifted/created for language modeling.
- `DataCollatorForLanguageModeling(tokenizer, mlm=True, mlm_probability=0.15)`: masked LM.
- `DataCollatorForSeq2Seq(tokenizer, model=model)`: pads inputs and labels for summarization/translation; handles label pad IDs.
- `DataCollatorForTokenClassification(tokenizer)`: pads token labels with ignored label IDs.
- Custom subclass of `DataCollatorWithPadding` or `DataCollatorMixin`: use when examples contain extra fields, paired preference samples, multimodal arrays, or nonstandard labels.

Validation checklist:

- The collator must return tensors with keys that the model accepts.
- Dynamic padding needs `tokenizer.pad_token` or equivalent processor padding support.
- For labels, padding token values should match loss ignore conventions, commonly `-100` for token-level/generation labels.
- If the collator needs raw fields that `Trainer` would prune, set `remove_unused_columns=False` or preprocess those fields into model inputs before training.

## Safe Smoke Script

This sub-skill bundles `scripts/training_args_smoke.py`. It has no network behavior and does not import `Trainer`. It attempts to instantiate `TrainingArguments`, prints normalized decisions, and reports optional dependency failures cleanly.

Run from the skill root or adjust the path:

```bash
python scripts/training_args_smoke.py --help
python scripts/training_args_smoke.py \
  --output_dir outputs/smoke \
  --eval_strategy steps --eval_steps 50 \
  --save_strategy steps --save_steps 100 \
  --load_best_model_at_end \
  --metric_for_best_model eval_loss \
  --report_to none
```

Use it to catch argument mismatches before running `Trainer` or an example script.

## Common Argument Patterns

### Minimal Local Smoke

```python
TrainingArguments(
    output_dir="outputs/smoke",
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    max_steps=3,
    eval_strategy="no",
    save_strategy="no",
    report_to="none",
)
```

### Evaluation And Best Checkpoint

```python
TrainingArguments(
    output_dir="outputs/run",
    eval_strategy="steps",
    eval_steps=100,
    save_strategy="steps",
    save_steps=100,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    greater_is_better=False,
    save_total_limit=2,
    report_to="none",
)
```

### Memory-Constrained GPU

```python
TrainingArguments(
    output_dir="outputs/memory",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=16,
    gradient_checkpointing=True,
    bf16=True,
    optim="adamw_torch",
    report_to="none",
)
```

### Hub Publishing

```python
TrainingArguments(
    output_dir="outputs/model-name",
    push_to_hub=True,
    hub_model_id="namespace/model-name",
    hub_strategy="every_save",
)
```

Only enable Hub push when auth and repository ownership are intentional. For dry runs, leave `push_to_hub=False` and `report_to="none"`.
