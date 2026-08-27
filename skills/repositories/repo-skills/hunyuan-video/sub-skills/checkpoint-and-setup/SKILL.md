---
name: checkpoint-and-setup
description: "Guides HunyuanVideo installation, CUDA dependency choices,
  checkpoint layout validation, text encoder preparation, and model-root
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# HunyuanVideo Checkpoint and Setup

Use this sub-skill when the task is about installing HunyuanVideo, preparing `ckpts/`, validating model files, diagnosing missing text encoders/VAE/DIT weights, or deciding whether CUDA hardware is sufficient before generation.

## Read first

- `references/installation.md` for Python, CUDA, Docker, and dependency guidance.
- `references/checkpoint-layout.md` for the expected checkpoint tree and text encoder preprocessing.
- `references/troubleshooting.md` for setup failures and memory/backend triage.
- `scripts/validate_checkpoint_layout.py` to validate file presence without downloading or loading weights.

## Safe workflow

1. Confirm the environment has the repo-pinned dependencies and CUDA if generation is required. From the root skill, run:

```bash
python scripts/check_hunyuan_video_env.py --check-optional
```

2. Validate model files before launching a long generation job:

```bash
python sub-skills/checkpoint-and-setup/scripts/validate_checkpoint_layout.py --model-base ckpts
```

3. If using FP8, validate the companion map file too:

```bash
python sub-skills/checkpoint-and-setup/scripts/validate_checkpoint_layout.py --model-base ckpts --require-fp8 --dit-weight ckpts/hunyuan-video-t2v-720p/transformers/mp_rank_00_model_states_fp8.pt
```

4. Route to `../inference/SKILL.md` for single-GPU command construction, `../parallel-and-optimization/SKILL.md` for FP8/xDiT commands, or `../web-demo/SKILL.md` for Gradio launch.

## Important constraints

- `--model-base` defaults to `ckpts`; if that directory does not exist, the canonical sampling script fails before model loading.
- The default constants also read a `MODEL_BASE` environment variable at import time. Keep `MODEL_BASE` and `--model-base` consistent when customizing paths.
- Full generation is not proven by parser or layout checks. It requires downloaded checkpoint files, CUDA, and enough VRAM.
- The repository documents Linux, Python 3.10.9, PyTorch 2.6.0, CUDA 12.4 or 11.8, flash-attn, and optional xDiT.
