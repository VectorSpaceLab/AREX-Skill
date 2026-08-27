# Core Trainer Troubleshooting

## Wrong Dataset Columns

Symptoms:

- `KeyError` for `text`, `prompt`, `chosen`, `rejected`, `completion`, or custom reward columns.
- Trainer silently drops fields needed by reward functions.

Fix:

- SFT text data needs the configured `dataset_text_field`, defaulting to `text`.
- SFT prompt-completion data needs `prompt` and `completion` when relying on automatic completion masking.
- DPO and Reward training need `chosen` and `rejected` pairs, usually with `prompt` for DPO.
- GRPO and RLOO need `prompt`; custom rewards can also use extra columns such as `answer`, `task_type`, or labels.
- Keep `remove_unused_columns=False` for GRPO/RLOO when rewards need non-prompt columns.
- Route schema conversion and chat-message normalization to `../data-and-rewards/`.

## Missing `reward_funcs`

Symptoms:

- `GRPOTrainer` or `RLOOTrainer` construction fails or has no meaningful reward signal.

Fix:

- Pass at least one reward function, model id, or reward model.
- For callable rewards, return one scalar or `None` per completion.
- If using multiple rewards, set `reward_weights` only when the list length exactly matches the number of rewards.

## GRPO or RLOO Rewards Return `None`

Symptoms:

- Warnings that all reward functions returned `None` for a row.
- Metrics contain missing reward values or training signal is zero for some task types.

Fix:

- Confirm `remove_unused_columns=False` so routing fields such as `task_type` reach the reward function.
- Verify every reward returns a list with the same length as `completions`.
- Returning `None` is valid for a reward that does not apply to a sample, but each row needs at least one non-`None` reward.
- For mixed task types, add task-specific rewards plus a fallback reward that returns a safe numeric value for otherwise unscored rows.
- Debug reward functions outside training on a tiny batch before launching long runs.

## Sequence Length, Padding, and Truncation

Symptoms:

- Out-of-memory during tokenization or training.
- Important answer text disappears after truncation.
- Reward model accuracy is poor because `chosen`/`rejected` tails are cut off.
- Generation trainers produce many clipped completions.

Fix:

- Reduce `max_length` for SFT/DPO/Reward when memory is the bottleneck; increase it when labels are being truncated.
- For GRPO/RLOO, tune `max_completion_length` separately from prompt length and inspect clipped completion metrics.
- Enable `mask_truncated_completions=True` in GRPO/RLOO only when truncated completions should be excluded from the loss.
- Ensure tokenizers/processors have a pad token; generation trainers use left padding for prompts and right padding for completions internally.
- Use `packing=True` for SFT only when the data is compatible with packed training.

## PEFT, Quantization, and Optional Packages

Symptoms:

- Import errors for `peft`, `bitsandbytes`, `flash_attn`, or vLLM.
- Quantized loading fails without LoRA.
- `padding_free=True` or FlashAttention settings fail at runtime.

Fix:

- Install optional packages only when the workflow requires them.
- Use `ModelConfig(use_peft=True, load_in_4bit=True)` or `load_in_8bit=True` only with PEFT-compatible training.
- Keep `padding_free=False` unless compatible attention kernels are installed.
- Route installation and multi-backend details to `../scaling-and-backends/`.

## Model Download and Hub Credentials

Symptoms:

- HTTP 401/403, gated model errors, or missing tokenizer/model files.
- `trust_remote_code` errors for custom model repositories.

Fix:

- Confirm the model id, revision, and access permissions.
- Authenticate with the Hub outside the skill content when gated models are required.
- Set `trust_remote_code=True` only for model repositories that require custom code and are trusted.
- For offline or private setups, pass a local model directory without hard-coding machine-specific paths into reusable scripts.

## Long Training and GPU Memory

Symptoms:

- Training appears hung while generation is slow.
- CUDA out-of-memory, low GPU utilization, or generation batches too large.

Fix:

- Start with a tiny dataset slice and one logging step before launching full training.
- Lower `per_device_train_batch_size`, increase `gradient_accumulation_steps`, or reduce `max_length`/`max_completion_length`.
- For GRPO/RLOO, reduce `num_generations` or ensure the effective batch size is divisible by it.
- Consider PEFT, quantization, FSDP, DeepSpeed, or vLLM only after the single-process trainer setup is correct; route those choices to `../scaling-and-backends/`.
