---
name: distributed-and-performance
description: "Guides agents configuring and troubleshooting Axolotl multi-GPU,
  DeepSpeed, FSDP, Ray, SLURM, parallelism, OOM, kernels, profiling, and
  performance tuning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Distributed and Performance

Use this sub-skill when the task mentions multi GPU Axolotl, DeepSpeed ZeRO, FSDP or FSDP QLoRA, Ray Train, SLURM/HPC/cloud launch, multi-node networking, context parallelism, tensor parallelism, expert parallelism, OOM, Flash Attention, Liger, Cut Cross Entropy, profiling, or distributed checkpoint save/load issues.

## Read First

- [references/distributed-training.md](references/distributed-training.md) for launcher choice, DeepSpeed vs FSDP vs Ray tradeoffs, FSDP2/HSDP/N-D parallelism, SLURM/multi-node patterns, and checkpoint implications.
- [references/performance-options.md](references/performance-options.md) for precision, attention backends, sample packing, gradient/activation/layer offload, LoRA kernels, Liger, Cut Cross Entropy, expert kernels, FP8, and profiling knobs.
- [references/troubleshooting.md](references/troubleshooting.md) for NCCL, CUDA/Torch/backend mismatches, DeepSpeed/FSDP conflicts, Ray setup, OOM triage, and sharded checkpoint recovery.
- [scripts/check_distributed_config.py](scripts/check_distributed_config.py) for safe static YAML checks before `axolotl preprocess`; it never downloads models, imports Axolotl, starts training, or modifies files.

## Quick Workflow

1. Identify the launch topology first: single process, one-node multi-GPU, Ray cluster, torchrun multi-node, SLURM batch, or cloud/HPC scheduler.
2. Choose one primary sharding stack: FSDP2 for new PyTorch-native sharding and FSDP+QLoRA, DeepSpeed ZeRO for existing DeepSpeed configs, Ray only as an orchestration layer, and N-D parallelism for advanced FSDP+TP/CP/EP meshes.
3. Set topology fields coherently: `deepspeed`, `fsdp_version`, `fsdp_config`, `dp_shard_size`, `dp_replicate_size`, `tensor_parallel_size`, `context_parallel_size`, `expert_parallel_size`, `use_ray`, and `ray_num_workers`.
4. Tune memory and throughput next: `bf16`, `fp16`, `tf32`, `fp8`, `attn_implementation`, `sample_packing`, `gradient_checkpointing`, `activation_offloading`, `layer_offloading`, kernel plugin flags, and batch/accumulation sizes.
5. Run `python scripts/check_distributed_config.py config.yaml --world-size N` for static conflicts, then validate in the user's Axolotl environment with `axolotl preprocess config.yaml` before launching `axolotl train`.
6. For method-specific loss, reward, dataset, adapter, or model-family fields, route to the sibling training, data, and model-loading sub-skills before changing distributed settings.

## Boundaries

- This sub-skill owns distributed launcher choices, DeepSpeed config mapping, FSDP/FSDP2/HSDP/Ray tradeoffs, N-D parallelism, backend prerequisites, memory/performance flags, profiling, and safe static config checks.
- Route training objective recipes and method-specific YAML fields to `sft-and-pretraining`, `preference-tuning`, or `rl-and-rewards`.
- Route dataset format, `type: chat_template`, column mapping, and YAML schema mechanics to `data-and-configs`.
- Route `base_model`, tokenizer/processor, LoRA/QLoRA adapter details, quantization compatibility, and architecture quirks to `model-loading-and-adapters`.
- Route basic CLI command catalogs, installation, `axolotl fetch`, `agent-docs`, and operational smoke commands to the root Axolotl skill or `cli-and-operations` when present.

## Evidence Notes

This guidance is distilled from Axolotl distributed, multi-node, FSDP QLoRA, sequence/N-D parallelism, optimization, attention, precision, NCCL, Ray, HPC, checkpoint, source mixin, integration, example, and multigpu test evidence. The inspection environment proved package metadata and namespace import only; do not claim live distributed training, GPU kernels, model downloads, or full ML runtime verification unless the user runs those checks separately.
