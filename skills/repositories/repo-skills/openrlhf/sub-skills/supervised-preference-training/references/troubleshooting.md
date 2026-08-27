# Troubleshooting

Use this guide before launching expensive SFT, reward-model, DPO, IPO, or cDPO training commands.

## Model and Dataset Paths

Symptoms:

- Model or dataset fails to resolve.
- Training unexpectedly downloads large artifacts.
- Private Hugging Face repository access fails.

Checks:

- Confirm `--model.model_name_or_path` and `--ref.model_name_or_path` are local paths or intended hub IDs.
- Confirm `--data.dataset` points to an intended local dataset or hub dataset.
- If using ModelScope via `--use_ms`, route environment and hub configuration questions to operations.
- Do not claim full runtime readiness from import-only package verification; GPU dependencies and remote access still need validation.

## Wrong Dataset Keys

Symptoms:

- Key errors during dataset formatting.
- Empty prompts, completions, chosen responses, or rejected responses.
- DPO/RM loss is nonsensical because chosen/rejected fields are reversed.

Checks:

- SFT requires `--data.input_key` and often `--data.output_key` unless using a pretraining-style format.
- RM/DPO require `--data.chosen_key` and `--data.rejected_key`; `--data.prompt_key` is optional and schema-dependent.
- Route schema inspection, conversion scripts, and multiturn examples to the `data-preparation` sub-skill.
- For SFT `--data.multiturn`, ensure `--data.apply_chat_template` is present; the CLI asserts this requirement.

## Chat Template and Input Template

Symptoms:

- Prompt text contains literal `\n` instead of line breaks.
- CLI warns that `{}` is missing from `--data.input_template`.
- Multiturn data fails immediately.

Checks:

- Bash commands needing newlines should use shell quoting such as `$'User: {}\nAssistant: '`.
- If `--data.input_template` lacks `{}`, the CLI sets it to `None` after warning.
- Use `--data.apply_chat_template` when the tokenizer has the intended chat template and especially for multiturn SFT/RM/DPO.

## OOM and DeepSpeed Choices

Symptoms:

- CUDA OOM during model load, forward pass, or optimizer step.
- Reference model in DPO doubles memory pressure.
- Checkpointing or optimizer state consumes unexpectedly high memory.

Mitigations:

- Reduce `--train.micro_batch_size`; remember `--train.batch_size` is global batch size.
- Increase `--ds.zero_stage` to `3` for larger models; example RM/DPO and Mixtral LoRA recipes use ZeRO-3.
- Add `--model.gradient_checkpointing_enable` to trade compute for memory.
- Use LoRA (`--ds.lora.rank`, `--ds.lora.alpha`, `--ds.lora.target_modules`) to reduce trainable parameters.
- Consider `--ds.adam_offload` or DPO `--ref.offload` only after acknowledging speed/IO trade-offs.
- For MoE models such as Mixtral, consider `--model.aux_loss_coef` to include balancing loss.

## FlashAttention, Liger, RingAttention, and Packing

Symptoms:

- Import errors for optional kernels.
- RingAttention assertion failure.
- Slow packed training or attention implementation warnings.

Checks:

- `--ds.packing_samples` benefits from FlashAttention; the CLI warns and sets `flash_attention_2` when packing is enabled without a flash attention implementation.
- `--ds.ring_attn_size > 1` requires `--ds.packing_samples` and optional RingAttention dependencies.
- `--ds.use_liger_kernel` is optional and dependency-sensitive.
- Route installation, CUDA/torch/flash-attn compatibility, and cluster/runtime checks to `operations-and-utilities`.

## LoRA Target Modules

Symptoms:

- LoRA setup fails because target modules are not found.
- Training silently adapts too many or too few modules.

Checks:

- Default `--ds.lora.target_modules all-linear` is broad and source-backed.
- Specific target names must match the model architecture; inspect model module names before narrowing.
- Nonzero `--ds.lora.rank` enables LoRA; `--ds.lora.alpha` and `--ds.lora.dropout` tune scaling/regularization.
- `--ds.load_in_4bit` is dependency- and hardware-sensitive; treat it as an operations preflight item.

## Checkpoint Save and Resume

Symptoms:

- No periodic checkpoints appear.
- Resume does not pick up previous progress.
- Hugging Face-format checkpoint is missing.

Checks:

- `--ckpt.output_dir` receives the final saved model.
- `--ckpt.path` is where periodic DeepSpeed checkpoints are saved and loaded.
- `--ckpt.save_steps -1` disables periodic checkpointing; use a positive interval for recovery points.
- `--ckpt.load_enable` is required to resume from `--ckpt.path` when it exists.
- `--ckpt.save_hf` only affects periodic checkpoint saves; final save still uses `--ckpt.output_dir`.
- `--ckpt.disable_ds` disables DeepSpeed periodic checkpoints and can reduce recovery options.

## Logger Credentials

Symptoms:

- W&B login prompts or authentication failures.
- TensorBoard logs not created.

Checks:

- W&B initializes only when `--logger.wandb.key` is set; avoid embedding secrets in reusable scripts.
- If W&B is not enabled, set `--logger.tensorboard_dir` for local TensorBoard logging.
- Set `--logger.wandb.project`, `--logger.wandb.group`, and `--logger.wandb.run_name` for organized experiments.

## Reward-Model Loss and Margin Confusion

Symptoms:

- RM loss differs from expected paper/config.
- Margin values are ignored.
- Reward head naming causes downstream loading confusion.

Checks:

- `--model.loss_type sigmoid` selects pairwise log-sigmoid loss; other values select log-exp loss in the current trainer implementation.
- `--model.margin_loss_enable` must be set for margin values to affect the loss.
- `--model.compute_fp32_loss_enable` can reduce numeric issues by computing reward loss in fp32.
- `--ds.value_head_prefix score` is the default and is also recommended by README for sequence-classification style reward loading.

## DPO Beta, IPO, cDPO, and NLL Choices

Symptoms:

- DPO updates are too weak/strong.
- User asks for IPO or conservative DPO but command is plain DPO.
- NLL regularization expected but missing.

Checks:

- `--model.beta` controls DPO loss scaling; example DPO script uses `0.1`.
- Add `--model.ipo_enable` for IPO.
- Add `--model.label_smoothing VALUE` for cDPO-style conservative DPO; example comments show `0.1`.
- Add `--model.nll_loss_coef VALUE` for NLL regularization.
- Use a separate `--ref.model_name_or_path` when the desired reference differs from the trainable policy; otherwise the CLI defaults it to the policy model.

## Source/README Flag Mismatch

Symptoms:

- Commands copied from README fail argument parsing.
- `--actor.model_name_or_path` is unrecognized for SFT/RM.

Resolution:

- Prefer current source-backed `--model.model_name_or_path` for `train_sft`, `train_rm`, and `train_dpo`.
- Treat README/example shell recipes as workflow evidence but verify final commands against the current CLI reference.
