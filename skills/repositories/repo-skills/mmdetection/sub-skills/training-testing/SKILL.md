---
name: training-testing
description: "Plan and validate MMDetection 3.3.0 training, resume, testing,
  evaluation, result dumping, and distributed or Slurm launch commands from
  configs without running them."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# training-testing

Use this sub-skill when the task involves launching or planning `tools/train.py`, `tools/test.py`, `dist_train.sh`, `dist_test.sh`, Slurm wrappers, resume behavior, `work_dir` outputs, command-line config overrides, `--auto-scale-lr`, CPU debugging, or result dumping.

## Route first

- Config inheritance, `auto_scale_lr` fields, model zoo checkpoint choice, and config edits: use `configuration-model-zoo` first, then return here for launch commands.
- Dataset roots, COCO/VOC/Cityscapes annotation layout, evaluator metrics, and metric-specific output prefixes: use `datasets-evaluation` first.
- New hooks, runners, loops, optimizers, schedulers, or custom registries: use `customization-extension` first.
- Environment import failures such as `ModuleNotFoundError: mmcv._ext`: ensure full `mmcv` is installed instead of `mmcv-lite`; then return here.

## Core workflow

1. Identify the config, checkpoint if testing, intended device topology, output `work_dir`, and any `--cfg-options` overrides.
2. For training, choose single-process, CPU debug, PyTorch distributed, or Slurm from [training workflows](references/training-workflows.md).
3. For evaluation, visualization, TTA, and prediction dumps, use [testing and evaluation](references/testing-evaluation.md).
4. Before giving a launch command, run the bundled dry-run planner to catch common flag mistakes:

```bash
python sub-skills/training-testing/scripts/build_train_test_command.py train CONFIG.py --work-dir work_dirs/EXP --auto-scale-lr
python sub-skills/training-testing/scripts/build_train_test_command.py test CONFIG.py CHECKPOINT.pth --gpus 8 --out results.pkl
```

5. If the user reports a failure, triage with [training/testing troubleshooting](references/troubleshooting.md).

## Command patterns

- Single GPU train: `python tools/train.py CONFIG.py --work-dir work_dirs/EXP [--resume [CKPT]] [--auto-scale-lr] [--cfg-options key=value ...]`.
- CPU debug train: `CUDA_VISIBLE_DEVICES=-1 python tools/train.py CONFIG.py --work-dir work_dirs/debug ...`; expect very slow execution.
- Distributed train: `CUDA_VISIBLE_DEVICES=0,1,2,3 PORT=29500 bash tools/dist_train.sh CONFIG.py 4 ...`.
- Slurm train: `GPUS=8 GPUS_PER_NODE=8 bash tools/slurm_train.sh PARTITION JOB CONFIG.py WORK_DIR ...`.
- Single GPU test: `python tools/test.py CONFIG.py CHECKPOINT.pth [--work-dir WORK_DIR] [--out results.pkl] [--show-dir DIR] [--tta]`.
- Distributed test: `PORT=29500 bash tools/dist_test.sh CONFIG.py CHECKPOINT.pth GPUS [--out results.pkl] ...`.

Always explain that shell wrappers are patterns tied to the user's checkout and cluster, while this skill's script only prints commands and validates arguments.
