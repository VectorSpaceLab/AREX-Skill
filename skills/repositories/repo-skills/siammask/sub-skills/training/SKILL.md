---
name: training
description: "Guides CUDA-only SiamMask base/refine and SiamRPN training,
  checkpoint resume, experiment configs, and training setup validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SiamMask Training

Use this sub-skill when the task is to train or resume SiamMask/SiamRPN models, inspect experiment configs, plan data requirements, or debug CUDA/batch/checkpoint issues.

## Hard Requirement

The native training scripts call CUDA APIs unconditionally (`model.cuda()` and `DataParallel(...).cuda()`). Treat CUDA as required with no CPU substitute for real training. CPU-only work can validate configs and commands, but it does not verify training runtime.

## Prerequisites

- Read root [install/setup](../../references/install-and-setup.md) and [model overview](../../references/model-overview.md).
- Run the root environment probe with `--expect-cuda yes` before real training.
- Prepare training data through [../data-preparation/SKILL.md](../data-preparation/SKILL.md). The configs expect `crop511` directories and JSON indexes.
- Obtain `resnet.model` or an appropriate base checkpoint before training from scratch/refine.

## Main Routes

| User intent | What to do |
| --- | --- |
| Train SiamMask base | Read [references/workflows.md](references/workflows.md#siammask-base-training) and use `scripts/run_training.py base` in dry-run mode first. |
| Train the refine/sharp model | Read [references/workflows.md](references/workflows.md#siammask-refinesharp-training); provide `--pretrained <base-checkpoint>`. |
| Train the SiamRPN baseline | Read [references/workflows.md](references/workflows.md#siamrpn-resnet-training) and use `scripts/run_training.py siamrpn`. |
| Inspect config/data paths | Read [references/config-reference.md](references/config-reference.md); the bundled runner summarizes dataset roots and JSON paths before launching. |
| Debug training failure | Read [references/troubleshooting.md](references/troubleshooting.md). |

## Bundled Helper

Use [scripts/run_training.py](scripts/run_training.py) to compose commands and inspect config paths. It:

- Defaults to dry-run and prints the command, cwd, `PYTHONPATH`, and config dataset summary.
- Sets `PYTHONPATH` to include checkout root and experiment directory.
- Supports `base`, `refine`, and `siamrpn` modes.
- Lets you set `--gpu <CUDA_VISIBLE_DEVICES>` before execution.
- Only starts training when `--run` is supplied.

Example dry-run:

```bash
python scripts/run_training.py --repo-root <siammask-checkout> --gpu 0,1,2,3 base \
  --config config.json --batch 64 --workers 20 --epochs 20
```

Add `--run` before `base` only after the user approves a long CUDA training job.

## Do Not

- Do not claim training is verified from CPU imports or command help.
- Do not start full training without checking disk space, dataset availability, checkpoint paths, and user approval.
- Do not reuse refine checkpoints with base-only configs or box-only SiamRPN flags.
- Do not hide missing dataset roots; training scripts will otherwise fail after allocating GPU/data-loader resources.
