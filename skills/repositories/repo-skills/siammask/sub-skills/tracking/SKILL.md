---
name: tracking
description: "Guides SiamMask demo, benchmark tracking, VOT/DAVIS/YouTube-VOS
  evaluation, and tracking hyperparameter tuning workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SiamMask Tracking and Evaluation

Use this sub-skill when the task is to run or reason about SiamMask inference-time workflows: an OpenCV demo, benchmark tracking outputs, VOT evaluation metrics, or hyperparameter tuning.

## Prerequisites

- Read the root [install/setup reference](../../references/install-and-setup.md) first.
- Verify the checkout and Python environment with the root `scripts/check_environment.py` helper.
- Prepare checkpoint files and datasets before launching native runs; this sub-skill does not download them.
- Use [../data-preparation/SKILL.md](../data-preparation/SKILL.md) if a dataset, VOT JSON, or `crop511`/benchmark layout is missing.
- Use [../training/SKILL.md](../training/SKILL.md) if the requested checkpoint must be trained or resumed.

## Main Routes

| User intent | What to do |
| --- | --- |
| "Run the demo" or "track the tennis sample" | Read [references/workflows.md](references/workflows.md#interactive-demo-flow), then use `scripts/run_tracking.py demo` in dry-run mode before adding `--run`. |
| "Evaluate/check a checkpoint on VOT" | Read [references/workflows.md](references/workflows.md#benchmark-test-flow) and [references/cli-reference.md](references/cli-reference.md#test-mode). Use `scripts/run_tracking.py test` with the right experiment, config, checkpoint, dataset, and mask/refine flags. |
| "Compute VOT metrics from result folders" | Read [references/workflows.md](references/workflows.md#vot-result-evaluation-flow). Use `scripts/run_tracking.py eval` after result directories exist. |
| "Tune penalty/window/lr/search region" | Read [references/workflows.md](references/workflows.md#hyperparameter-tuning-flow). Use `tune-vot` for VOT-style tuning; use `tune-vos` only with CUDA. |
| "Why did tracking fail?" | Read [references/troubleshooting.md](references/troubleshooting.md) and root [troubleshooting](../../references/troubleshooting.md). |

## Bundled Helper

Use [scripts/run_tracking.py](scripts/run_tracking.py) for command composition and optional execution. It:

- Accepts `--repo-root <siammask-checkout>` so it is not tied to the checkout used to create this skill.
- Selects experiment working directories such as `siammask_sharp`, `siammask_base`, or `siamrpn_resnet`.
- Prepends the checkout root and experiment directory to `PYTHONPATH`.
- Prints commands by default and only runs native code when `--run` is supplied.
- Warns about GUI, checkpoint, dataset, and CUDA requirements before execution.

Example dry-run:

```bash
python scripts/run_tracking.py --repo-root <siammask-checkout> test \
  --experiment siammask_sharp \
  --config config_vot18.json \
  --resume <checkpoint.pth> \
  --dataset VOT2018 --mask --refine --cpu
```

## Key Decisions

- Use `siammask_sharp` with `--mask --refine` for sharp segmentation masks.
- Use `siammask_base` with `--mask` when evaluating the base mask branch without refine.
- Use `siamrpn_resnet` without `--mask`/`--refine` for box-only tracking.
- For VOT reset-based evaluation, expect `baseline/<video>/<video>_001.txt` result files.
- For DAVIS/YouTube-VOS segmentation, enable mask mode and validate annotation/image layouts in the data-preparation sub-skill.
- Disable visualization on headless servers; use `--cpu` with `test` when CUDA is unavailable, but do not assume the interactive demo honors `--cpu` when CUDA is visible.
