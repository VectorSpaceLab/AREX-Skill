# CLI Reference

This reference summarizes source-backed `argparse` flags for `openrlhf.cli.train_sft`, `openrlhf.cli.train_rm`, and `openrlhf.cli.train_dpo`. It is not a complete replacement for `--help`, but it captures the flags most often needed to construct safe training plans.

## Launch Pattern

Use DeepSpeed module launches for training:

```bash
deepspeed --module openrlhf.cli.train_sft [flags]
deepspeed --module openrlhf.cli.train_rm [flags]
deepspeed --module openrlhf.cli.train_dpo [flags]
```

Running these commands is expensive and may download models/datasets. For planning, use the bundled command builder instead.

## Shared Core Flags

| Area | Flags |
| --- | --- |
| Model | `--model.model_name_or_path`, `--model.gradient_checkpointing_enable`, `--model.gradient_checkpointing_reentrant`, `--model.aux_loss_coef` |
| Training size | `--train.batch_size`, `--train.micro_batch_size`, `--train.max_epochs`, `--train.seed`, `--train.full_determinism_enable` |
| Optimizer | `--optim adam|muon`, `--adam.lr`, `--adam.betas`, `--adam.eps`, `--adam.weight_decay`, `--muon.lr`, `--muon.momentum` |
| Scheduler/clip | `--lr_scheduler`, `--lr_warmup_ratio`, `--min_lr_ratio`, `--max_norm` |
| DeepSpeed | `--ds.zero_stage`, `--ds.param_dtype`, `--ds.zpg`, `--ds.adam_offload`, `--ds.overlap_comm`, `--ds.tensor_parallel_size`, `--ds.use_universal_ckpt`, `--ds.deepcompile` |
| Kernels | `--ds.attn_implementation`, `--ds.experts_implementation`, `--ds.use_liger_kernel`, `--ds.ring_attn_size`, `--ds.ring_attn_head_stride` |
| Packing | `--ds.packing_samples` |
| LoRA/quant | `--ds.load_in_4bit`, `--ds.lora.rank`, `--ds.lora.alpha`, `--ds.lora.dropout`, `--ds.lora.target_modules` |
| Data | `--data.dataset`, `--data.dataset_probs`, `--data.dataset_split`, `--data.max_samples`, `--data.max_len`, `--eval.dataset`, `--eval.split` |
| Tokenizer/chat | `--data.input_template`, `--data.apply_chat_template`, `--data.tokenizer_chat_template`, `--data.disable_fast_tokenizer` |
| IO workers | `--data.dataloader_num_workers` |
| Checkpoints | `--ckpt.output_dir`, `--ckpt.path`, `--ckpt.save_steps`, `--ckpt.save_hf`, `--ckpt.disable_ds`, `--ckpt.max_num`, `--ckpt.max_mem`, `--ckpt.load_enable` |
| Evaluation/logging | `--eval.steps`, `--logger.logging_steps`, `--logger.wandb.key`, `--logger.wandb.org`, `--logger.wandb.group`, `--logger.wandb.project`, `--logger.wandb.run_name`, `--logger.tensorboard_dir` |
| Hub | `--use_ms` |

## SFT-Specific Flags

| Flag | Default / Notes |
| --- | --- |
| `--data.input_key` | Default `input`; prompt/source field for SFT. |
| `--data.output_key` | Default `None`; response/target field for prompt-completion SFT. |
| `--data.input_template` | Default `User: {}\nAssistant: `; must include `{}` to be used. |
| `--data.multiturn` | Requires `--data.apply_chat_template`. |
| `--model.pretrain_mode_enable` | Uses pretraining-style loss behavior. |
| `--train.max_epochs` | Default `2` in source. |
| `--adam.lr` | Default `5e-6` in source. |
| `--train.batch_size` | Default `128`; global batch size. |
| `--train.micro_batch_size` | Default `8`; per-GPU micro-batch size. |
| `--ds.zero_stage` | Default `2`. |
| `--data.max_len` | Default `2048`. |

## Reward-Model-Specific Flags

| Flag | Default / Notes |
| --- | --- |
| `--data.prompt_key` | Optional prompt field for preference data. |
| `--data.chosen_key` | Default `chosen`. |
| `--data.rejected_key` | Default `rejected`. |
| `--ds.value_head_prefix` | Default `score`; used on saved model config. |
| `--model.loss_type` | Default `sigmoid`; non-`sigmoid` selects log-exp loss in the trainer. |
| `--model.margin_loss_enable` | Enables margin-aware pairwise loss. |
| `--model.compute_fp32_loss_enable` | Computes loss with fp32 rewards. |
| `--train.max_epochs` | Default `1`. |
| `--adam.lr` | Default `9e-6`. |
| `--train.batch_size` | Default `128`; global batch size. |
| `--train.micro_batch_size` | Default `1`; per-GPU micro-batch size. |
| `--ds.zero_stage` | Default `2`, though example recipes use ZeRO-3. |
| `--data.max_len` | Default `512`, though example recipes use longer contexts. |

## DPO/IPO/cDPO-Specific Flags

| Flag | Default / Notes |
| --- | --- |
| `--ref.model_name_or_path` | Default `None`; CLI copies `--model.model_name_or_path` when omitted. |
| `--ref.offload` | Offloads reference model using eval DeepSpeed config. |
| `--data.prompt_key` | Optional prompt field for preference data. |
| `--data.chosen_key` | Default `chosen`. |
| `--data.rejected_key` | Default `rejected`. |
| `--model.beta` | Default `0.1`; DPO loss temperature/reward scaling. |
| `--model.ipo_enable` | Enables IPO loss variant. |
| `--model.label_smoothing` | Default `0.0`; positive values implement cDPO-style label smoothing. |
| `--model.nll_loss_coef` | Default `0`; adds NLL regularization. |
| `--train.max_epochs` | Default `1`. |
| `--adam.lr` | Default `1e-5`; example DPO recipe uses `5e-7`. |
| `--train.batch_size` | Default `128`; global batch size. |
| `--train.micro_batch_size` | Default `8`; example DPO recipe uses `1`. |
| `--eval.split` | Default `test` for DPO; SFT/RM default to `train`. |

## Packing, RingAttention, and FlashAttention

- `--ds.packing_samples` is defined in SFT/RM/DPO entrypoints.
- If packing is enabled without a flash attention implementation, the CLI warns and sets `args.ds.attn_implementation = "flash_attention_2"`.
- `--ds.ring_attn_size > 1` asserts that packing is enabled.
- RingAttention requires optional dependencies and should be routed to operations for install/runtime readiness checks.

## Checkpoint Defaults by Entrypoint

| Entrypoint | Default `--ckpt.path` | Final save |
| --- | --- | --- |
| SFT | `./ckpt/checkpoints_sft` | Saves final model to `--ckpt.output_dir`. |
| RM | `./ckpt/checkpoints_rm` | Saves final model to `--ckpt.output_dir` and records `value_head_prefix`. |
| DPO | `./ckpt/checkpoints_dpo` | Saves final policy model to `--ckpt.output_dir`. |

`--ckpt.load_enable` attempts to resume from `--ckpt.path` if that path exists. Periodic checkpointing depends on `--ckpt.save_steps`; `-1` disables periodic saves by converting to infinity inside the trainers.

## Logger Defaults

| Entrypoint | Default W&B project | Run-name prefix |
| --- | --- | --- |
| SFT | `openrlhf_train_sft` | `sft_...` |
| RM | `openrlhf_train_rm` | `rm_...` |
| DPO | `openrlhf_train_dpo` | `exp_...` |

W&B only initializes when `--logger.wandb.key` is set. TensorBoard initializes from `--logger.tensorboard_dir` when W&B is not active.
