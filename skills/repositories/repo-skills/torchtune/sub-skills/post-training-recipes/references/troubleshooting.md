# Troubleshooting Post-Training Recipes

Use this matrix before launching or debugging torchtune training recipes. It prioritizes safe diagnosis over running expensive jobs.

## Safety And Cost

| Risk | Signal | Safe action |
| --- | --- | --- |
| Expensive training starts unexpectedly | User asks to “try” a recipe without confirming hardware/data/checkpoint/output | Build a dry command only; ask before executing. |
| Gated model download or private dataset | Config points to gated Hugging Face/Kaggle/model paths or remote datasets | Confirm credentials and access; do not embed tokens in commands. |
| Large checkpoint writes | `output_dir` points to temporary or shared location without quotas checked | Ask for durable output path and disk budget. |
| Cluster job submission | `sbatch`, `srun`, or multi-node torchrun requested | Produce template/dry command; ask before submitting. |

## CLI And Registry Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Invalid file name` from `tune cp` | Recipe/config name not in registry | Run `tune ls` and choose exact registry name. |
| `--config` required | Missing config argument | Add `--config <registry-config-or-local-yaml>`. |
| Recipe import failure via Python | Attempted `import recipes` | Use `tune run`, `tune cp`, registry names, or runpy behavior through the CLI. |
| Torchrun flags ignored | Flags placed after recipe/config | Move launcher flags before recipe name. |
| Recipe not distributed error | Single-device recipe with torchrun options | Switch to distributed recipe/config or remove launcher flags. |

## Config / Component Mismatches

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Config validates but runtime fails loading model | Checkpoint format, model builder, tokenizer, or `model_type` mismatch | Align `model._component_`, checkpointer component, tokenizer, checkpoint files, and model family. |
| Unknown component path | Optional package missing or typo in `_component_` | Confirm import path and install only the needed optional package. |
| Dataset transform errors | Dataset component does not match data schema | Route to `../data-and-datasets/SKILL.md`; validate JSONL/message/preference fields. |
| Optimizer constructor error | Optimizer was swapped but stale optimizer fields remain | Remove incompatible fields, e.g. use `~optimizer.foreach` when replacing AdamW with bitsandbytes optimizer. |
| QAT recipe rejects quantizer | Quantizer is a post-training quantizer rather than QAT quantizer | Use a QAT quantizer component for QAT finetuning; use post-training quantizer later in quantize/eval flow. |

## Checkpoint, Output, And Resume

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Missing checkpoint file | `checkpoint_files` does not match directory contents | Inspect expected shard names and update `checkpoint_files`. |
| Tokenizer load failure | Tokenizer path from different model family or missing gated artifact | Align tokenizer with model/checkpoint family and confirm access. |
| Resume starts from wrong state | `resume_from_checkpoint=True` without matching recipe state | Resume only from compatible torchtune output with recipe state and checkpoint artifacts. |
| LoRA resume fails | Adapter checkpoint or recipe checkpoint path missing | Set adapter and recipe checkpoint fields expected by the recipe/checkpointer. |
| DPO policy/reference confusion | `ref_checkpointer` points to policy output or wrong base | Decide frozen reference explicitly and document why. |
| PPO output path errors | PPO saves policy/value artifacts in subfolders and output dir was not prepared | Create/confirm output directory structure before launch. |

See `../training-utilities-and-rlhf/SKILL.md` for deeper checkpointer and resume mechanics.

## Precision, Device, And Memory

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| bf16 support error | Hardware/backend does not support bf16 | Use supported hardware, switch to `dtype=fp32` if feasible, or choose a smaller config. |
| fp16 rejected | Recipe does not support full fp16 | Use `bf16` or `fp32` according to recipe messages. |
| CUDA OOM | Model/config too large for memory | Reduce `batch_size`, increase `gradient_accumulation_steps`, enable activation checkpointing, choose LoRA/QLoRA, or distribute. |
| QLoRA slower than expected | 4-bit base quantization adds overhead | Consider `compile=True` only if the specific recipe/runtime supports it; use LoRA for smaller models. |
| QAT compile error | QAT recipe path rejects compile | Set `compile=False`. |
| CPU offload too slow | Optimizer/FSDP offload bottleneck | Increase GPU work per optimizer step or use more suitable hardware. |

## Optional Dependencies

| Feature | Optional dependency / concern | Safe handling |
| --- | --- | --- |
| bitsandbytes optimizer | `bitsandbytes` package and compatible backend | Confirm install and remove incompatible optimizer fields. |
| W&B logging | `wandb` package and login | Use DiskLogger by default unless user requests W&B. |
| Comet logging | `comet_ml` package and login | Use DiskLogger by default unless user requests Comet. |
| QLoRA / QAT quantization | torchao/NF4/QAT support and compatible PyTorch | Confirm installed versions and hardware before launch. |
| Dev async GRPO | async RL extras may be required | Treat as experimental; verify optional extras before use. |

## DPO / PPO / KD / QAT Specific Issues

| Method | Failure mode | Fix |
| --- | --- | --- |
| DPO | Dataset is SFT/chat instead of paired preference | Use a preference dataset component and chosen/rejected schema. |
| DPO | Reference model accidentally trainable or same as policy output | Keep reference checkpointer frozen and intentional. |
| PPO | Missing reward/value/reference checkpoints | Check all PPO checkpointer sections, not just `checkpointer`. |
| PPO | `optimizer_in_bwd=True` with incompatible accumulation | Follow recipe note that it may require `gradient_accumulation_steps=1`. |
| KD | Teacher/student tokenizer or vocab mismatch | Choose compatible teacher/student families or adapt tokenizer/model config carefully. |
| KD | `kd_ratio` extreme produces poor class/KD balance | Sweep conservatively using dry commands first. |
| QAT | Expecting final quantized artifact immediately after training | QAT finetune outputs QAT-trained weights; run quantize conversion later. |
| QAT-LoRA | `quantize_base=True` with QAT LoRA | QAT LoRA code rejects some base quantization combinations; use QAT LoRA config patterns. |

## Safe Escalation Path

1. Reproduce with `tune cat`, `tune validate`, or dry command construction, not a training run.
2. Inspect exact registry recipe/config names with `tune ls`.
3. Copy config and make minimal edits.
4. Validate YAML shape.
5. Confirm hardware, credentials, dataset, checkpoints, output, and optional packages.
6. Ask for explicit approval before executing `tune run`, `srun`, or `sbatch`.
