---
name: parallelism-moe
description: "Design DeepSpeed pipeline parallelism, MoE layers, sequence
  parallelism, AutoSP, and activation checkpointing for training workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Parallelism, MoE, and Checkpointing

Use this sub-skill when a task involves DeepSpeed training parallelism beyond basic ZeRO: pipeline parallel models, MoE layers, expert tensor parallelism, Ulysses or HF sequence parallelism, AutoSP, or activation checkpointing.

## Route by Task

- **Pipeline parallelism**: use `references/workflows.md#pipeline-parallelism` for `PipelineModule`, `LayerSpec`, `TiedLayerSpec`, `ProcessTopology`, and `PipelineEngine.train_batch()` / `eval_batch()` loops.
- **MoE and expert parallelism**: use `references/workflows.md#moe-and-expert-parallelism` for `deepspeed.moe.layer.MoE`, expert-parallel sizing, optimizer param groups, tuple outputs, PR-MoE, and expert tensor parallelism.
- **Sequence parallelism**: use `references/workflows.md#sequence-parallelism` for `DistributedAttention`, Ulysses HF registration, dataloader sharding, loss aggregation, and AutoSP.
- **Activation checkpointing**: use `references/workflows.md#activation-checkpointing` for `deepspeed.checkpointing.configure()` and checkpoint placement with model/pipeline parallelism.
- **API signatures**: run `scripts/inspect_parallelism_api.py --help`, then use it to print import availability and signatures without launching distributed jobs.

## Boundaries

- Stay here for `PipelineModule`, `LayerSpec`, `TiedLayerSpec`, `ProcessTopology`, `PipelineEngine`, MoE layers, MoE optimizer groups, sequence-parallel APIs, AutoSP, and activation checkpointing.
- Use the training-configuration sub-skill for basic ZeRO configuration, optimizer/offload tuning not specific to MoE, and standard `deepspeed.initialize()` config assembly.
- Use the inference/injection sub-skill for inference tensor parallelism and kernel injection.
- Use ops/tooling guidance for extension builds, fused op installation, NVMe, or environment build failures.

## References

- `references/api-reference.md` lists the installed signatures and source-backed API responsibilities.
- `references/workflows.md` gives compact design workflows and minimal patterns.
- `references/troubleshooting.md` maps common parallelism failures to likely fixes.
