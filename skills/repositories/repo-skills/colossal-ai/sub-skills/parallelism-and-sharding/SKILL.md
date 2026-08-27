---
name: parallelism-and-sharding
description: "Plan ColossalAI tensor, pipeline, sequence, hybrid parallelism,
  ShardFormer model sharding, auto-parallel, and offload workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Parallelism and Sharding

Use this sub-skill when the task is about mapping GPUs to tensor/pipeline/sequence/data/expert parallelism, using ShardFormer, choosing `ShardConfig`, planning pipeline schedules, or diagnosing topology and sharding errors.

## Route Here

- Explain 1D/2D/2.5D/3D tensor parallelism, pipeline parallelism, sequence parallelism, zero-bubble, and hybrid topologies.
- Decide `tp_size`, `pp_size`, `sp_size`, `zero_stage`, microbatching, and divisibility constraints for `HybridParallelPlugin`.
- Use `ShardConfig`, `ShardFormer`, `ModelSharder`, and model policy concepts.
- Understand experimental auto-parallel, activation checkpointing, solver dependencies, and NVMe/offload caveats.
- Diagnose unsupported model policies, fused-kernel flags, and sequence-parallel incompatibilities.

## Reroute

- Process launch and environment variables: use `../installation-and-launch/SKILL.md`.
- Concrete `Booster` training loops and plugin object use: use `../booster-training/SKILL.md`.
- Colossal-Inference tensor or patched parallel generation commands: use `../inference-and-serving/SKILL.md`.
- Application-specific MoE/LLaMA/Chat/Eval scripts: use `../application-recipes/SKILL.md`.

## Fast Start

1. Confirm world size and GPU count.
2. Choose the largest hard partition first: pipeline stages, tensor shards, sequence shards, expert shards, then data parallel remainder.
3. Ensure the product of selected non-data parallel sizes divides world size.
4. Use `HybridParallelPlugin` for combined training topology and ShardFormer policies for model graph rewriting.
5. Validate with a tiny model or config advisor before using a real LLM.

## References and Helpers

- `references/parallelism-guide.md` explains topology choices and common hybrid patterns.
- `references/shardformer.md` covers ShardFormer, `ShardConfig`, model families, and optimization flags.
- `references/auto-parallel-and-offload.md` describes experimental auto-parallel, activation checkpointing, and NVMe/offload caveats.
- `references/troubleshooting.md` maps topology, NCCL, policy, sequence-parallel, and optional-kernel failures.
- `scripts/parallelism_config_advisor.py` checks world-size divisibility and suggests a data-parallel remainder.
- `scripts/shardformer_model_matrix.py` prints a self-contained model-family support checklist.

## Operating Rules

- Do not hide topology decisions inside a training-loop answer. State `tp_size`, `pp_size`, `sp_size`, `ep_size`, and data-parallel remainder.
- Do not enable flash attention, fused normalization, JIT fused kernels, or FP8 without checking optional dependencies and hardware.
- Treat auto-parallel and solver examples as experimental unless the user's environment matches the documented dependency path.
