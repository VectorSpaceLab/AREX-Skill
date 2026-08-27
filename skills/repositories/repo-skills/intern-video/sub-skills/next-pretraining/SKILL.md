---
name: next-pretraining
description: "Operate InternVideo-Next stage1 and stage2 visual pretraining
  workflows, architecture, data, and failure modes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# InternVideo-Next pretraining operating skill

Use this sub-skill when the task is about InternVideo-Next: stage1/stage2 pretraining, visual foundation model architecture, model-zoo selection, CLIP/SigLIP teacher distillation, diffusion loss, JEPA-style masks, DeepSpeed/DDP command shaping, or FlashAttention caveats.

Do **not** use this sub-skill for InternVideo2.5/3 video MLLM chat/SFT/evaluation or InternVideo2 video-text retrieval. Use the sibling `datasets` sub-skill for annotation validation before constructing a pretraining run.

## Read order

1. `references/workflows.md` for stage selection, model names, command shapes, data-list formats, architecture boundaries, and model zoo notes.
2. `troubleshooting.md` before changing FlashAttention, DeepSpeed, dataset loaders, checkpoint loading, or stage2 target-encoder behavior.
3. If data files are not yet validated, hand off to the `datasets` sub-skill and use its bundled validator for annotation/list sanity checks.

## Operating guardrails

- Full InternVideo-Next pretraining is GPU/distributed, data-heavy, and not verified by this skill. Treat commands as construction guidance until the user supplies datasets, teacher/checkpoint weights, and approved CUDA/cluster resources.
- Do not present CPU imports as proof of model readiness: core model files import FlashAttention, FusedMLP, and fused RMSNorm components.
- Keep stage1 and stage2 distinct. Stage2 can initialize from a stage1 checkpoint and uses a frozen target encoder/momentum update, while stage1 uses an external teacher plus diffusion/reconstruction losses.
- Use placeholders for paths and launch variables; do not expose local environment paths.

## Expected handoff

Report the selected stage, model variant, teacher/checkpoint expectations, data-list format, launch shape, required backend, validation status, and unresolved gaps such as missing FlashAttention or unavailable stage1 checkpoint.
