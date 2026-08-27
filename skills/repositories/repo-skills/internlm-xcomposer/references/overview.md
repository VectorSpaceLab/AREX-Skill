# InternLM-XComposer Overview

## When to read

Read this when you need to identify which InternLM-XComposer family/version or sub-skill should own a task.

## Repository shape

InternLM-XComposer is a multi-version multimodal model repository. The root is not a single Python distribution. It collects model instructions, examples, fine-tuning scripts, evaluation recipes, and related projects.

| Area | Main user-facing workflows | Owning sub-skill |
| --- | --- | --- |
| XComposer 2.5 root | Image/video/multi-image chat, high-resolution understanding, webpage generation, article writing, LMDeploy/AWQ, Gradio, supervised fine-tune | `model-inference`, `finetuning` |
| XComposer 2.0 / 1.0 | Legacy chat, 4KHD/VL inference, AutoGPTQ 4-bit, legacy fine-tuning, classic benchmark scripts | `model-inference`, `finetuning`, `evaluation-and-projects` |
| XComposer 2.5 Reward | Reward scoring, pairwise comparison, rank ordering, preference-pair training and evaluation | `reward-model` |
| XComposer 2.5 OmniLive | Audio ASR/classification, base VLM, memory-backed video QA, SRS/FastAPI/Gradio deployments, video/audio/streaming benchmarks | `omnilive`, `evaluation-and-projects` |
| ShareGPT4V | ShareGPT4V package install, ShareCaptioner, data preparation, converters, evaluation scripts, research-use license caveats | `evaluation-and-projects` |
| DualFocus | DualFocus package install, benchmark data preparation, local/Slurm evaluation commands, converters | `evaluation-and-projects` |

## Model family reminders

- XComposer 2.5 uses `internlm/internlm-xcomposer2d5-7b` for current general VLM/composition workflows.
- XComposer 2.5 4-bit examples use `internlm/internlm-xcomposer2d5-7b-4bit` with LMDeploy AWQ.
- XComposer 2.5 Reward uses `internlm/internlm-xcomposer2d5-7b-reward` and exposes score/compare/rank methods through `trust_remote_code=True`.
- XComposer 2.5 OmniLive uses `internlm/internlm-xcomposer2d5-ol-7b` and, after local download, expects component directories such as `audio/`, `base/`, `adapter/`, `memory/`, and `merge_lora/`.
- XComposer2 4KHD and VL use older model IDs such as `internlm/internlm-xcomposer2-4khd-7b` and `internlm/internlm-xcomposer2-vl-7b`.
- XComposer 1.0 uses model IDs such as `internlm/internlm-xcomposer-7b` and `internlm/internlm-xcomposer-vl-7b`.

## High-risk operations

Treat these as execution-time operations, not skill-runtime assumptions:

- downloading 7B model weights or benchmark datasets;
- running long training, fine-tuning, or benchmark jobs;
- launching network listeners, SRS, FastAPI, Gradio, or Node frontend services;
- calling GPT/OpenAI judges or external leaderboard submission servers;
- installing CUDA extensions such as `flash-attn` without matching torch/CUDA/driver evidence.

The bundled `scripts/` helpers in this skill are intentionally safe planners, validators, and renderers. The repaired `entrypoints/` bundles under selected sub-skills are real source-derived runnable entrypoints; they should be used only after explicit execution approval because they can load large models, start training, bind services, or write large outputs.
