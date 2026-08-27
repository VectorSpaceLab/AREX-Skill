---
name: video-mllm
description: "Operate InternVideo2.5 and InternVideo3 video MLLM inference, SFT,
  evaluation, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# InternVideo video MLLM operating skill

Use this sub-skill when the task is about InternVideo2.5 or InternVideo3 video multimodal large language models: model choice, Hugging Face loading, text/image/video message construction, long-video reasoning, InternVideo3 SFT command shaping, benchmark evaluation readiness, or video-MLLM troubleshooting.

Do **not** use this sub-skill for InternVideo2 visual-only or video-text retrieval training, InternVideo-Next visual pretraining, or dataset schema validation except as a handoff to the sibling `datasets` sub-skill.

## Route by task

- **Quick inference or demo:** read `references/inference.md` first. It contains distilled model-loading and message-shape templates for InternVideo3 plus selection notes for InternVideo2.5 LRC/HiCo models.
- **InternVideo3 SFT/CPT setup:** read `references/internvideo3-sft.md`, then use the `datasets` sub-skill to validate meta JSON and JSONL annotations before constructing a launch command.
- **Benchmark planning:** read `references/evaluation.md` and classify each evaluation as GPU/data-heavy unless the user only asks for command inspection.
- **Failures:** read `troubleshooting.md` before changing dependencies, cache directories, frame limits, or evaluation data roots.

## Operating guardrails

1. Treat all full model runs, SFT jobs, and benchmark submissions as optional/unverified until the user provides checkpoints, benchmark data, storage, CUDA/FlashAttention readiness, and launch approval.
2. Use placeholders such as `<model-id-or-dir>`, `<annotation-meta.json>`, and `<work-dir>` in advice; do not leak local environment paths.
3. Prefer distilled command shapes over telling the user to run repository shell scripts. The source scripts are cluster- and dependency-specific and may install packages at runtime.
4. Distinguish inference chat schemas from SFT JSONL schemas: Hugging Face processor messages use `type: "video"` / `type: "image"`; InternVideo3 SFT JSONL uses `type: "video_url"` / `type: "image_url"` with `<VIDEO_CONTEXT>` / `<IMG_CONTEXT>` placeholders.

## Expected handoff

When done, report: selected generation/model, required runtime inputs, chosen message or SFT/eval schema, command shape or validation action, backend/data caveats, and unresolved gaps. Never claim that a heavy training or benchmark result was verified unless it was actually executed in the user-approved environment.
