---
name: hunyuan-video
description: "Use this operating skill for Tencent-Hunyuan/HunyuanVideo
  text-to-video setup, checkpoint layout, inference commands, Gradio launch, and
  CUDA/FP8/xDiT troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# HunyuanVideo Operating Skill

Use this skill when a task involves Tencent-Hunyuan/HunyuanVideo text-to-video generation, checkpoint setup, command construction, Gradio launch, or CUDA/FP8/xDiT troubleshooting. HunyuanVideo is a PyTorch repository for a large 13B-class video diffusion model with a 3D VAE, MLLM/CLIP text encoders, single-GPU sampling, FP8 weights, Gradio serving, and xDiT sequence-parallel inference.

## First decisions

1. If the user is blocked before generation because dependencies, CUDA, model files, or text encoders are missing, read `sub-skills/checkpoint-and-setup/SKILL.md`.
2. If the user needs a single-GPU sampling command, API call, prompt/seed/shape explanation, or output-file behavior, read `sub-skills/inference/SKILL.md`.
3. If the user mentions multi-GPU, `torchrun`, xDiT, `ulysses-degree`, `ring-degree`, FP8, `flash-attn`, `xfuser`, or memory planning, read `sub-skills/parallel-and-optimization/SKILL.md`.
4. If the user wants the browser UI, Gradio, `SERVER_NAME`, `SERVER_PORT`, or web-demo troubleshooting, read `sub-skills/web-demo/SKILL.md`.

## Required operating context

- HunyuanVideo generation requires Linux, CUDA-capable NVIDIA GPUs, PyTorch, and downloaded checkpoints. The repository documentation reports single-GPU testing on an 80GB GPU, with approximate minimum memory of 45GB for `544x960x129` and 60GB for `720x1280x129`.
- The default model root is `ckpts`; commands usually pass `--model-base ckpts` or rely on that default.
- Actual model sampling is not a CPU workflow. CPU-only checks can validate command construction, parser behavior, checkpoint layout, and documentation, but they do not prove generation.
- The generated helper scripts include safe preflight/build tools and explicit runner scripts. The build tools do not download checkpoints, start Gradio, or run long GPU sampling; the runners are real GPU/model jobs and should only be executed after preflights and approvals.

## Installation and smoke checks

This repo does not ship package metadata, so install from the checkout root with the documented runtime stack. Start from the repository root and install the pinned dependencies:

```bash
python -m pip install -r requirements.txt
```

If the task needs checkpoint downloads, also install the Hugging Face CLI helper documented in the checkpoint sub-skill. For xDiT multi-GPU work, add `flash-attn` and `xfuser` only when that route is actually needed.

Use the root diagnostic when a user asks whether the Python/CUDA environment is ready enough to start HunyuanVideo debugging:

```bash
python scripts/check_hunyuan_video_env.py --json --check-optional
python scripts/check_hunyuan_video_env.py --require-cuda
```

Read `references/troubleshooting.md` for cross-cutting install/import/GPU failures and `references/architecture-and-models.md` for model-component terminology.

## Common task routes

| User asks for | Read |
| --- | --- |
| "Where do I put HunyuanVideo weights?" | `sub-skills/checkpoint-and-setup/references/checkpoint-layout.md` |
| "Validate my checkpoint folder before sampling." | `sub-skills/checkpoint-and-setup/scripts/validate_checkpoint_layout.py` |
| "Build a command to generate a video from this prompt." | `sub-skills/inference/scripts/build_sample_command.py` and `sub-skills/inference/references/workflows.md` |
| "Why does `video_length=128` fail?" | `sub-skills/inference/references/troubleshooting.md` |
| "Use 4 or 8 GPUs with xDiT." | `sub-skills/parallel-and-optimization/references/parallel-and-fp8.md` |
| "Use FP8 weights." | `sub-skills/parallel-and-optimization/references/parallel-and-fp8.md` |
| "Run a Gradio demo safely on localhost." | `sub-skills/web-demo/scripts/build_gradio_command.py` |

## Verification boundaries

Safe checks: parser inspection, command-builder output, checkpoint-layout validation, dependency import checks, CUDA availability probes. Expensive checks: checkpoint download, full `sample_video.py` generation, FP8 generation, xDiT `torchrun`, Gradio service launch, and the native distributed attention test. Run expensive checks only when the user provides checkpoints, accepts GPU time, and understands memory requirements.

Before refreshing this skill for a newer checkout, read `references/repo-provenance.md`.
