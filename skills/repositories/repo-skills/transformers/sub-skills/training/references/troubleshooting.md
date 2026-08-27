# Training Troubleshooting

Use this guide to diagnose common Transformers training failures. Prefer the smallest reproducer: instantiate `TrainingArguments`, run preprocessing on a few examples, collate one batch, then run one forward pass before launching full training.

## Missing Optional Dependencies

Symptoms:

- `ImportError` or optional dependency message when importing `Trainer`, `TrainingArguments`, collators, or model classes.
- Example script fails before parsing all arguments.

Actions:

- Install `torch` for PyTorch training.
- Install `accelerate` for distributed/device orchestration and no-trainer scripts.
- Install `datasets` for dataset-loading example scripts.
- Install `evaluate` or task metric packages when `compute_metrics` needs them.
- Keep reusable validation scripts from importing `Trainer` at module import time; report dependency requirements cleanly.

## `remove_unused_columns` Surprises

Symptoms:

- Collator receives missing raw fields.
- Model forward misses custom inputs.
- Dataset columns disappear before a custom collator can use them.

Cause:

- `Trainer` defaults `remove_unused_columns=True` and prunes columns not accepted by `model.forward(...)`.

Actions:

- Preprocess raw fields into model input keys before training.
- Set `remove_unused_columns=False` when the collator needs raw columns or target dictionaries.
- Ensure the collator returns only keys the model can consume unless the model forward accepts extras.
- For vision/detection/segmentation, preserving target dictionaries often requires `remove_unused_columns=False`.

## Missing Or Wrong Labels

Symptoms:

- Loss is missing or `Trainer` says the model did not return a loss.
- Evaluation has no metrics or labels are absent.
- QA or multi-label tasks drop one label tensor.

Actions:

- Confirm dataset examples include `labels` or task-specific label fields.
- Use `label_names=[...]` for multiple labels such as `start_positions` and `end_positions`.
- Do not name a model forward argument exactly `label`; use `labels` or explicit task-specific names.
- Ensure label dtype and shape match the model head and loss.
- For token/seq2seq tasks, pad ignored label positions with `-100`.

## Collator And Padding Mismatches

Symptoms:

- `ValueError` about tensor creation from ragged lists.
- Tokenizer complains about no pad token.
- Labels and inputs have incompatible lengths.
- GPU memory is much higher than expected.

Actions:

- Use `DataCollatorWithPadding` for dynamically padded classification/QA inputs.
- Use `DataCollatorForTokenClassification` for token labels.
- Use `DataCollatorForSeq2Seq` for summarization/translation labels.
- Use `DataCollatorForLanguageModeling` for CLM/MLM and set `mlm` deliberately.
- For decoder-only models without a pad token, consider `tokenizer.pad_token = tokenizer.eos_token` if semantically acceptable.
- Set `pad_to_multiple_of=8` only when useful for tensor cores and memory allows it.
- Collate a two-example batch manually before starting `Trainer`.

## Eval/Save Strategy Mismatch

Symptoms:

- `TrainingArguments` raises `ValueError` with `load_best_model_at_end=True`.
- Best model is not loaded or no metric is available.

Actions:

- Set `eval_strategy` to `"steps"` or `"epoch"`; it cannot stay `"no"` when loading the best model.
- Align `save_strategy` with `eval_strategy`, unless intentionally using best-only save behavior.
- If using steps, make `save_steps` a round multiple of `eval_steps`.
- Set `metric_for_best_model`, commonly `"eval_loss"` for a safe default.
- Set `greater_is_better=False` for losses and true for metrics where larger is better.

## Checkpoint Resume Problems

Symptoms:

- Training restarts from step 0.
- Resume path is ignored or not found.
- Optimizer/scheduler state mismatch.
- Best checkpoint disappeared.

Actions:

- Pass an actual checkpoint directory such as `outputs/run/checkpoint-1000` to `resume_from_checkpoint`.
- In scripts, use `--resume_from_checkpoint PATH` when supported.
- Check that `trainer_state.json`, optimizer state, scheduler state, and model files exist if exact continuation is required.
- Avoid overly aggressive `save_total_limit` until resume behavior is proven.
- Keep distributed strategy compatible between save and resume.
- If only weights are needed, load the model from the checkpoint directory rather than resuming the trainer state.

## Out Of Memory

Symptoms:

- CUDA OOM during forward, backward, evaluation, or save.
- OOM appears only with long samples or generation metrics.

Actions:

- Reduce `per_device_train_batch_size` first.
- Increase `gradient_accumulation_steps` to recover effective batch size.
- Enable `gradient_checkpointing=True` when supported.
- Use `bf16` or `fp16` only when hardware supports it.
- Use `dtype="auto"` when loading pretrained weights to avoid fp32 expansion.
- Reduce `max_length`, image size, audio duration, or generation length.
- Use dynamic padding and bucket/group by length if available.
- Lower eval batch size separately with `per_device_eval_batch_size`.
- Consider FSDP/DeepSpeed/offload for model-size OOM.

## Mixed Precision Failures

Symptoms:

- NaN loss.
- Unsupported dtype error.
- Training works in fp32 but fails in fp16/bf16.

Actions:

- Prefer `bf16` on hardware with stable bfloat16 support.
- Try fp32 baseline with precision flags disabled.
- Lower learning rate or add warmup if loss instability appears.
- Disable `torch_compile` while isolating numeric problems.
- Verify custom losses and metrics do not force incompatible dtypes.

## Distributed Launch Problems

Symptoms:

- Hang at startup.
- Multiple processes write conflicting outputs.
- NCCL, rendezvous, or rank errors.

Actions:

- Start with one process, then two, then full scale.
- For `torchrun`, confirm `--nproc_per_node` equals intended visible GPUs.
- Set a distinct master port if another job may be using the default.
- Inspect the earliest rank failure; later errors can be cascade shutdowns.
- Keep output paths unique per experiment.
- Verify package versions are identical across nodes.

## FSDP Problems

Symptoms:

- Auto-wrap does not wrap layers or wraps the wrong modules.
- Checkpoint save/load fails.
- Memory does not improve.

Actions:

- Confirm the exact transformer layer class name used in `fsdp_config`.
- Test without FSDP, then with minimal FSDP, then add activation checkpointing/offload.
- Validate checkpoint format and resume before long runs.
- Avoid changing FSDP, precision, compile, and gradient checkpointing simultaneously.

## DeepSpeed Problems

Symptoms:

- JSON config validation failure.
- Batch-size assertion failure.
- CUDA extension or optimizer import failure.
- Resume fails under ZeRO.

Actions:

- Validate DeepSpeed config JSON syntax.
- Ensure `train_batch_size`, `train_micro_batch_size_per_gpu`, and `gradient_accumulation_steps` match `TrainingArguments`, or use `auto` consistently.
- Confirm `deepspeed` and CUDA/PyTorch versions are compatible.
- Test ZeRO stage and offload settings with tiny sample limits.
- Verify checkpoint save/resume with the same world size and strategy when exact continuation is required.

## Hub Push Problems

Symptoms:

- Auth error.
- Repository name collision.
- Push happens during a smoke run.

Actions:

- Leave `push_to_hub=False` until the user confirms publishing.
- Set `hub_model_id` explicitly for shared namespaces or organizations.
- Ensure tokens are available through the user's normal Hugging Face auth flow.
- Use `trainer.save_model()` for local artifacts when publishing is not desired.

## Debugging Checklist To Return

When handing back a fix, include:

- Root cause category.
- Minimal code or command change.
- Dependency/hardware assumption.
- One smoke test command or one-batch validation step.
- Expected success signal such as finite loss, metric key, checkpoint directory, or clean argument normalization.
