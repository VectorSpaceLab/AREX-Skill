# Training Arguments

This reference distills the 2.5 `finetune.py` argument dataclasses and the source shell-template defaults. Values below are planning defaults, not a guarantee that the current host has the required checkpoints, packages, GPUs, or memory.

## Core model and data arguments

| Argument | Source default / shell value | Practical meaning |
| --- | --- | --- |
| `--model_name_or_path` | code default empty; shell uses `internlm/internlm-xcomposer2d5-7b` | Hugging Face model id or local base checkpoint directory. Required for real training. |
| `--data_path` | `data.txt` | Either a JSON list or a `data.txt` manifest. See `data-formats.md`. |
| `--given_num` | code default `False`; shell sets `True` | In manifest mode, `True` interprets second column as thousands of samples; `False` interprets it as a ratio. |
| `--batch_size` | code default `4`; shell uses `2` | Internal `Sample_dataset.get_item()` packing count, not Hugging Face `per_device_train_batch_size`. Use `1` for tiny fixtures. |
| `--resolution` | `560` | 2.5 image preprocessing resolution used by the HD transform. This replaces old 2.0-style `img_size` habits. |
| `--hd_num` | `18` | Number of dynamic sub-image patches. Lower it when image training runs out of memory. |
| `--max_length` | code default `8192`; shell uses `16384` | Maximum conversation token length in model config/training args. Reduce for memory-constrained or tiny runs. |
| `--label_names` | `['samples']` | Internal Trainer/data-collator contract; do not remove unless rewriting the collator/model forward path. |

## Full versus LoRA template defaults

| Setting | Full-parameter template | LoRA template | Notes |
| --- | --- | --- | --- |
| `--use_lora` | `False` | `True` | Switches PEFT wrapping on/off. |
| `--fix_vit` | `False` | `True` | Full mode unfreezes `model.vit`; LoRA mode freezes it. |
| `--fix_sampler` | `False` | `True` | Controls the visual projection / sampler (`vision_proj`) trainability. |
| `--learning_rate` | `1e-5` | `5e-5` | Adapter-only training uses a larger source default. |
| `--output_dir` | `output/finetune` | `output/finetune_lora` | Use explicit paths per experiment. |
| `--bf16` | `True` | `True` | Requires suitable hardware/runtime. Switch only after auditing dtype support. |
| `--gradient_checkpointing` | `True` | `True` | Saves memory at compute cost. |
| `--per_device_train_batch_size` | `1` | `1` | Keep this at `1` unless the collator/model path supports larger Trainer batches. |
| `--gradient_accumulation_steps` | `8` | `8` | Source effective-batch control; lower for tiny smoke commands. |
| `--save_strategy` | `epoch` | `epoch` | Shell templates save once per epoch. |
| `--save_total_limit` | `1` | `1` | Avoids many large checkpoints. |
| `--report_to` | `none` | `none` | No WandB/TensorBoard reporting by default. |

Common optimization arguments from the source shell templates:

```text
--num_train_epochs 1
--weight_decay 0.1
--adam_beta2 0.95
--warmup_ratio 0.01
--lr_scheduler_type cosine
--logging_steps 1
--evaluation_strategy no
```

## LoRA-specific arguments

| Argument | Default | Meaning |
| --- | --- | --- |
| `--lora_r` | `64` | LoRA rank. Lower for smaller adapters; higher increases capacity and memory. |
| `--lora_alpha` | `64` | LoRA scaling factor. Usually kept aligned with rank unless tuning deliberately. |
| `--lora_dropout` | `0.05` | Dropout in LoRA modules. |
| `--lora_target_modules` | `attention.wqkv`, `attention.wo`, `feed_forward.w1`, `feed_forward.w2`, `feed_forward.w3` | Exact module-name fragments used by PEFT to attach adapters. Preserve these for source-equivalent tuning. |
| `--lora_bias` | `none` | Controls whether bias tensors are saved with LoRA state. Other parser-recognized values are `all` and `lora_only`. |
| `--lora_weight_path` | empty string | Parsed but not consumed by the current training flow. It is not a functional resume/load flag unless the trainer is patched. |

When `--use_lora True`, the trainer freezes `model.model` base parameters, builds a PEFT `LoraConfig`, prints trainable parameters, and enables input gradients when gradient checkpointing is on.

## Launcher and backend arguments

| Backend choice | Command shape | Notes |
| --- | --- | --- |
| DeepSpeed ZeRO-2 | `torchrun ... finetune.py ... --deepspeed ds_config_zero2.json` | This is the source-template path. The repaired skill bundles the config at `entrypoints/xcomposer25/ds_config_zero2.json`; launch wrappers pass that path automatically. The config uses auto fp16/bf16, auto batch sizes, and ZeRO stage 2 without optimizer offload. |
| FSDP | `torchrun ... finetune.py ... --fsdp "full_shard auto_wrap"` | Manual Trainer alternative. Remove `--deepspeed`; add model-specific FSDP details only after runtime confirmation. |
| Single-process debug | `python finetune.py ...` | Useful only for argument inspection or extremely small local smoke tests. Real model training is GPU-heavy. |

Distributed fields used by torchrun:

```text
--nproc_per_node <gpus-per-node>
--nnodes <node-count>
--node_rank <current-node-rank>
--master_addr <rendezvous-host>
--master_port <free-port>
```

For single-node work, use `--nnodes 1 --node_rank 0 --master_addr localhost` and set `--nproc_per_node` to the actual number of visible GPUs.

## Save behavior

`safe_save_model_for_hf_trainer()` changes what is written:

- DeepSpeed ZeRO-3 mode asks DeepSpeed for a consolidated 16-bit state dict.
- LoRA non-ZeRO-3 mode saves LoRA parameters and optional bias tensors according to `--lora_bias`.
- Full non-ZeRO-3 mode saves the full model state dict.

Plan disk space accordingly; full checkpoints are much larger than adapter outputs.
