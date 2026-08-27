---
name: "evaluation-and-metrics"
description: "Guides MMGeneration evaluation commands, metric selection, and
  inception-stat preparation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation and Metrics

Use this sub-skill when the user wants to score generated images, precompute real-image statistics, or understand the repo's evaluation scripts and metric classes.

## Typical triggers

- "How do I evaluate this checkpoint?"
- "How do I compute FID or IS?"
- "How do I precompute inception stats?"
- "How do I run online vs offline evaluation?"
- "Why does distributed evaluation reject this metric?"

## Include here

- `tools/evaluation.py`
- `tools/dist_eval.sh`, `tools/slurm_eval.sh`, `tools/slurm_eval_multi_gpu.sh`
- `tools/utils/inception_stat.py`
- `tools/utils/translation_eval.py`
- `mmgen.core.evaluation` builders, hooks, and metrics
- FID, IS, PPL, PR, SWD, MS-SSIM, and GaussianKLD usage
- online/offline evaluation mode differences

## Exclude here

- Training launchers and resume behavior -> `training-and-distribution`
- Image sampling demos -> `inference-and-sampling`
- Config registry editing -> `configuration-and-extension`
- Latent editing and packaging -> `applications-and-deployment`

## Read these files first

- `references/workflows.md`
- `references/troubleshooting.md`
- `../../references/api-reference.md`
- `../../references/cli-reference.md`
- `../../references/model-overview.md`
- `../../references/data-formats.md`

## What good guidance looks like

A future agent should be able to:

1. Pick the right metric and command family for a GAN or translation model.
2. Decide when online evaluation is faster than disk-backed evaluation.
3. Explain what cached inception statistics are for and when they are needed.
4. Recognize which metrics can run in the distributed path.
5. Understand when a metric helper returns a tensor, a dict, or a scalar.

## Common failure modes

- A distributed run asks for a metric the distributed path does not support.
- Inception-stat extraction needs a different runtime or cached model file.
- Translation evaluation is pointed at the wrong target domain.
- The helper is told to sample images only, but the caller expects a metric score.
- A metric config uses a missing cached Inception/VGG asset.

For concrete recovery steps, read `references/troubleshooting.md`.
