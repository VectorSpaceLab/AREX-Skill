---
name: rendering-evaluation
description: "Guides gaussian-splatting rendering, metrics, pretrained-model
  evaluation, and output validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Rendering and Evaluation

Use this sub-skill when the task is to render a trained model, compute metrics, evaluate pretrained outputs, or understand the output layout produced by `render.py`, `metrics.py`, or `full_eval.py`.

## Read First

- Read [references/rendering-workflows.md](references/rendering-workflows.md) for the standard render and pretrained-model flows.
- Read [references/evaluation-workflows.md](references/evaluation-workflows.md) for paper-style benchmark orchestration and safe skip decisions.
- Read [references/cli-reference.md](references/cli-reference.md) for verified `render.py`, `metrics.py`, and `full_eval.py` flags.
- Read [references/troubleshooting.md](references/troubleshooting.md) for model-layout, LPIPS, config-merge, and benchmark failures.
- Run [scripts/validate_model_outputs.py](scripts/validate_model_outputs.py) when checking whether a model directory is ready for rendering or metrics.

## What This Sub-Skill Covers

- Rendering a trained model into train/test PNG outputs.
- Computing PSNR, SSIM, and LPIPS from saved renders.
- Evaluating pretrained models by pointing `render.py` back to the source dataset with `-s`.
- Interpreting `cfg_args` merge behavior and output directory conventions.
- Understanding when `full_eval.py` is too expensive to run and how to construct the command instead.

## What This Sub-Skill Excludes

- Training and checkpoint management. Route those to [../training/SKILL.md](../training/SKILL.md).
- Raw image conversion and depth preparation. Route those to [../data-preparation/SKILL.md](../data-preparation/SKILL.md).
- SIBR viewer build/run details. Route those to [../viewers/SKILL.md](../viewers/SKILL.md).
- CUDA installation and extension build errors. Route those to [../setup-and-backends/SKILL.md](../setup-and-backends/SKILL.md).

## Typical Flow

1. Verify the model folder with the bundled validator.
2. Render train/test splits with `render.py`.
3. Inspect the PNG directories.
4. Run `metrics.py` if the GT/render layout is present.
5. Use `full_eval.py` only when the user explicitly wants the full benchmark orchestration.

## Output Expectations

A future agent should be able to answer:

- Is this model directory ready to render?
- Which `render.py` flags should be used for a pretrained model?
- Why did metrics fail to find the output layout?
- What does `full_eval.py` expect as input, and when should it be skipped?
