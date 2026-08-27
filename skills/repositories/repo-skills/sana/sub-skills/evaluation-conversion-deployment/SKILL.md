---
name: evaluation-conversion-deployment
description: "Plan Sana metrics, checkpoint conversion/export, Hugging Face
  upload/download utilities, `sana-run` SLURM launches, and deployment routes
  without running heavy jobs."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Evaluation, Conversion, and Deployment

Use this sub-skill when you need to plan a Sana evaluation, export, upload, or deployment command without executing the benchmark or conversion job.

## Use for
- Metric planning for FID/CLIP, GenEval, DPG-Bench, and ImageReward.
- Checkpoint export planning for image, video, and SVDQuant/Nunchaku pipelines.
- Safe inspection of `sana-run` and `sana-upload`.
- Deployment route selection for SGLang, ComfyUI, and Gradio demos.

## Do not use for
- Actual image/video generation; route to the image or video inference sub-skills.
- Training or dataset schema work; route to `training-data-configs`.

## Start here
- `references/metrics-and-benchmarks.md`
- `references/conversion-and-export.md`
- `references/cli-and-deployment.md`
- `references/troubleshooting.md`

## Safe planners
- `scripts/plan_metrics_command.py`
- `scripts/plan_conversion_command.py`
- `scripts/inspect_sana_cli.py`

## Operating notes
- Prefer a dry, command-planning pass before any benchmark, upload, or conversion.
- Require separate metric environments and datasets when a benchmark needs them.
- Treat HF tokens, SLURM credentials, and upload destinations as secrets.
- If a requested path is missing or a model family/precision combo is inconsistent, stop at planning and explain the gap rather than guessing.

## Provenance labels used while distilling
- `docs/metrics_toolkit.md`
- `docs/sglang.md`
- `docs/ComfyUI/comfyui.md`
- `docs/model_zoo.md`
- `docs/4bit_sana.md`
- `scripts/bash_run_inference_metric*.sh`
- `scripts/inference_*metric*.py`
- `tools/metrics/*`
- `tools/convert_scripts/*.py`
- `sana/cli/run.py`
- `sana/cli/upload2hf.py`
- `.github/workflows/ci.yaml`
