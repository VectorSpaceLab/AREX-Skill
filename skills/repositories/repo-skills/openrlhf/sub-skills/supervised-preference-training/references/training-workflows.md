# Training Workflows

OpenRLHF supervised/preference training is normally launched with DeepSpeed module entrypoints. Build commands for review first, then run only after GPU, dependency, data, and credential checks pass.

## Common Preflight Order

1. Pick the trainer: SFT (`train_sft`), reward model (`train_rm`), or DPO/IPO/cDPO (`train_dpo`).
2. Confirm model path/name and tokenizer behavior. `--model.model_name_or_path` is the source-backed flag for these CLIs.
3. Confirm data path/name, split, max samples, max length, and key names.
4. Choose memory strategy: micro-batch size, ZeRO stage, gradient checkpointing, LoRA/4-bit, packing, and optional offload.
5. Choose optimizer/scheduler/logging/checkpoint policy.
6. Dry-review the final command; actual training is an expensive GPU/network action.

## SFT Workflow

Use SFT for prompt/completion or chat fine-tuning:

```bash
deepspeed --module openrlhf.cli.train_sft \
  --model.model_name_or_path meta-llama/Meta-Llama-3-8B \
  --data.dataset Open-Orca/OpenOrca \
  --data.input_key question \
  --data.output_key response \
  --data.max_len 2048 \
  --train.batch_size 256 \
  --train.micro_batch_size 2 \
  --train.max_epochs 1 \
  --adam.lr 5e-6 \
  --ds.zero_stage 2 \
  --ds.param_dtype bf16 \
  --ds.attn_implementation flash_attention_2 \
  --ds.packing_samples \
  --model.gradient_checkpointing_enable \
  --ckpt.output_dir ./checkpoint/llama3-8b-sft \
  --ckpt.save_steps -1 \
  --logger.logging_steps 1 \
  --eval.steps -1
```

Source-backed SFT options:

- `--data.input_template` defaults to `User: {}\nAssistant: `; the CLI warns if the literal string lacks `{}` or if Bash newline escaping is probably wrong.
- `--data.apply_chat_template` asks the tokenizer to use its chat template; required by `--data.multiturn`.
- `--data.multiturn` enables compacted multiturn loss handling and asserts `--data.apply_chat_template`.
- `--model.pretrain_mode_enable` switches SFT loss handling toward continued pretraining.
- `--ds.packing_samples` packs samples and is strongly tied to FlashAttention-style attention; the CLI will set `flash_attention_2` when packing is enabled without a flash attention implementation.
- `--model.aux_loss_coef` is used for MoE auxiliary loss, as shown in the Mixtral LoRA recipe.

## SFT With LoRA

Use LoRA to reduce trainable parameters and memory pressure:

```bash
deepspeed --module openrlhf.cli.train_sft \
  --model.model_name_or_path mistralai/Mixtral-8x7B-v0.1 \
  --data.dataset Open-Orca/OpenOrca \
  --data.input_key question \
  --data.output_key response \
  --train.batch_size 128 \
  --train.micro_batch_size 4 \
  --ds.zero_stage 3 \
  --ds.lora.rank 64 \
  --ds.lora.alpha 64 \
  --ds.lora.target_modules all-linear \
  --model.aux_loss_coef 0.001 \
  --ds.packing_samples \
  --model.gradient_checkpointing_enable \
  --ckpt.output_dir ./checkpoint/mixtral-sft-lora
```

LoRA flags common to SFT/RM/DPO:

- `--ds.lora.rank` defaults to `0`; nonzero enables LoRA construction.
- `--ds.lora.alpha` defaults to `16`.
- `--ds.lora.dropout` defaults to `0`.
- `--ds.lora.target_modules` defaults to `all-linear`; pass specific module names only after inspecting the model architecture.
- `--ds.load_in_4bit` requests 4-bit loading and should be treated as dependency/hardware sensitive.

## Reward Model Workflow

Use reward-model training for pairwise preference data. The trainer compares chosen and rejected rewards and logs loss, accuracy, mean chosen reward, and mean rejected reward.

```bash
deepspeed --module openrlhf.cli.train_rm \
  --model.model_name_or_path OpenRLHF/Llama-3-8b-sft-mixture \
  --data.dataset OpenRLHF/preference_dataset_mixture2_and_safe_pku \
  --data.chosen_key chosen \
  --data.rejected_key rejected \
  --data.apply_chat_template \
  --data.max_len 8192 \
  --train.batch_size 256 \
  --train.micro_batch_size 1 \
  --train.max_epochs 1 \
  --adam.lr 9e-6 \
  --ds.zero_stage 3 \
  --ds.param_dtype bf16 \
  --ds.attn_implementation flash_attention_2 \
  --ds.packing_samples \
  --model.gradient_checkpointing_enable \
  --ckpt.output_dir ./checkpoint/llama3-8b-rm \
  --ckpt.save_steps -1 \
  --logger.logging_steps 1 \
  --eval.steps -1
```

Reward-model specifics:

- `--data.prompt_key` is optional; chosen/rejected keys are the critical pairwise fields.
- `--model.loss_type sigmoid` uses pairwise log-sigmoid loss; other values select log-exp loss in the trainer.
- `--model.margin_loss_enable` enables margin-aware pairwise loss when the dataset provides margins.
- `--model.compute_fp32_loss_enable` casts rewards to fp32 for loss computation.
- `--ds.value_head_prefix` defaults to `score`; README recommends this prefix for compatibility with `AutoModelForSequenceClassification` style reward heads.

## DPO, IPO, and cDPO Workflow

Use `train_dpo` for direct preference optimization against a reference model. If `--ref.model_name_or_path` is omitted, the CLI sets it to `--model.model_name_or_path`.

```bash
deepspeed --module openrlhf.cli.train_dpo \
  --model.model_name_or_path OpenRLHF/Llama-3-8b-sft-mixture \
  --ref.model_name_or_path OpenRLHF/Llama-3-8b-sft-mixture \
  --data.dataset OpenRLHF/preference_dataset_mixture2_and_safe_pku \
  --data.chosen_key chosen \
  --data.rejected_key rejected \
  --data.apply_chat_template \
  --data.max_len 8192 \
  --train.batch_size 256 \
  --train.micro_batch_size 1 \
  --train.max_epochs 1 \
  --adam.lr 5e-7 \
  --model.beta 0.1 \
  --model.label_smoothing 0.1 \
  --model.nll_loss_coef 0.05 \
  --ref.offload \
  --ds.zero_stage 3 \
  --ds.param_dtype bf16 \
  --ds.attn_implementation flash_attention_2 \
  --ds.packing_samples \
  --model.gradient_checkpointing_enable \
  --ckpt.output_dir ./checkpoint/llama3-8b-dpo \
  --ckpt.save_steps -1
```

DPO variants:

- `--model.beta` controls DPO reward scaling; example scripts use `0.1`.
- `--model.ipo_enable` switches the DPO loss implementation to IPO-style loss.
- `--model.label_smoothing` enables conservative DPO behavior when positive; example comments show `0.1` for cDPO.
- `--model.nll_loss_coef` adds NLL regularization, as referenced by CLI help comments.
- `--ref.offload` offloads the reference model through the evaluation DeepSpeed config and may reduce GPU memory pressure at speed cost.

## Checkpointing and Logging

- `--ckpt.output_dir` is the final model output directory used by `strategy.save_model` at the end of training.
- `--ckpt.path` is the periodic DeepSpeed checkpoint path (`./ckpt/checkpoints_sft`, `./ckpt/checkpoints_rm`, or `./ckpt/checkpoints_dpo` by default).
- `--ckpt.load_enable` resumes from `--ckpt.path` when it exists and restores consumed samples.
- `--ckpt.save_steps -1` means no periodic checkpoint save; trainers convert it to infinity.
- `--ckpt.save_hf` saves Hugging Face-format checkpoints at periodic save steps.
- `--ckpt.disable_ds` disables DeepSpeed-format periodic checkpointing, which can make training recovery harder.
- `--logger.wandb.key` enables Weights & Biases on rank 0; alternatively use `--logger.tensorboard_dir` for TensorBoard when W&B is not active.

## Current Flag Caveat

Some README snippets use older `--actor.model_name_or_path` spelling for SFT/RM examples. The current source entrypoints for `train_sft.py`, `train_rm.py`, and `train_dpo.py` define `--model.model_name_or_path`; prefer the source-backed flag in generated commands.
