# Training and evaluation workflows

This reference gives self-contained MMOCR train/test/evaluation decision rules. It does **not** require the original source checkout. Use caller-valid paths for `CONFIG`, `CHECKPOINT`, `WORK_DIR`, and outputs. Prefer the installed-package route through OpenMIM (`mim train mmocr ...`, `mim test mmocr ...`) when the caller has MMOCR installed as a package; use the bundled smoke script in this sub-skill before any expensive run.

## Safe sequence

1. Run [`../scripts/mmocr_config_smoke.py`](../scripts/mmocr_config_smoke.py) on the config.
2. Confirm the model family, dataset type, evaluator type, and `default_scope=mmocr`.
3. Confirm the dataset and checkpoint are available in the caller's environment.
4. Choose the lightest launch route: CPU/debug, one GPU, multi-GPU, or Slurm.
5. Only then start training or testing with the caller's installed MMOCR/OpenMIM tooling.

## Config smoke

```bash
python scripts/mmocr_config_smoke.py --config CONFIG --require-default-scope
```

Useful variants:

```bash
python scripts/mmocr_config_smoke.py --config CONFIG --json
python scripts/mmocr_config_smoke.py --config CONFIG \
  --cfg-options train_cfg.max_epochs=1 train_cfg.val_interval=1
python scripts/mmocr_config_smoke.py --config CONFIG \
  --cfg-options 'optim_wrapper.optimizer.lr=1e-4'
```

The smoke script only loads and summarizes the config. It does not build models, datasets, runners, distributed groups, or checkpoint objects.

## One-device training

Use this when the caller has a valid config and data layout and wants a normal single-process run.

```bash
mim train mmocr CONFIG --work-dir WORK_DIR
```

CPU/debug route:

```bash
CUDA_VISIBLE_DEVICES=-1 mim train mmocr CONFIG --work-dir WORK_DIR \
  --cfg-options train_cfg.max_epochs=1 train_cfg.val_interval=1
```

GPU route:

```bash
CUDA_VISIBLE_DEVICES=0 mim train mmocr CONFIG --work-dir WORK_DIR
```

Common options:

| Need | Option | Check first |
|---|---|---|
| Resume an interrupted training run | `--resume` | `WORK_DIR` contains the latest compatible training checkpoint. |
| Start/fine-tune from weights | set `load_from` in config or override it | Checkpoint family matches `model.type` and task. |
| Temporary config edit | `--cfg-options key=value ...` | Run the same override through the smoke helper first. |
| Automatic mixed precision | `--amp` | Family is marked AMP-compatible in [`model-zoo.md`](model-zoo.md). |
| Scale learning rate | `--auto-scale-lr` | Config contains `auto_scale_lr.base_batch_size`. |

## One-device testing and evaluation

Testing needs both the config and checkpoint.

```bash
mim test mmocr CONFIG CHECKPOINT --work-dir WORK_DIR
```

Save prediction artifacts for offline analysis:

```bash
mim test mmocr CONFIG CHECKPOINT --work-dir WORK_DIR --save-preds
```

Save visualizations without GUI:

```bash
mim test mmocr CONFIG CHECKPOINT --work-dir WORK_DIR --show-dir VIS_DIR
```

Recognition test-time augmentation only when the config has TTA fields:

```bash
mim test mmocr CONFIG CHECKPOINT --work-dir WORK_DIR --tta
```

Always route pure prediction-on-images tasks to [`ocr-inference`](../../ocr-inference/SKILL.md); this sub-skill is for config/checkpoint evaluation against datasets.

## Distributed and multi-GPU route

Use distributed training/testing only when the caller has compatible GPUs, a matching PyTorch/MMCV build, enough memory, and a free rendezvous port.

```bash
PORT=29501 CUDA_VISIBLE_DEVICES=0,1,2,3 \
  mim train mmocr CONFIG --gpus 4 --launcher pytorch --work-dir WORK_DIR
```

```bash
PORT=29501 CUDA_VISIBLE_DEVICES=0,1,2,3 \
  mim test mmocr CONFIG CHECKPOINT --gpus 4 --launcher pytorch --work-dir WORK_DIR
```

Operational notes:

- Choose a unique `PORT` for each concurrent distributed run.
- CPU smoke success does not prove CUDA/NCCL readiness.
- If the task is only to inspect a config, do not launch distributed training.
- Multi-node jobs need a scheduler or explicit distributed environment supplied by the caller.

## Slurm route

Use Slurm only inside a valid cluster environment with an authorized partition, GPU allocation, and `srun` access. OpenMIM can pass launcher options through to MMOCR, but site-specific submission wrappers vary; require the caller's cluster policy before constructing a final command.

Typical shape:

```bash
GPUS=8 GPUS_PER_NODE=8 CPUS_PER_TASK=5 SRUN_ARGS="..." \
  mim train mmocr CONFIG --launcher slurm --work-dir WORK_DIR
```

For testing:

```bash
GPUS=8 GPUS_PER_NODE=8 CPUS_PER_TASK=5 SRUN_ARGS="..." \
  mim test mmocr CONFIG CHECKPOINT --launcher slurm --work-dir WORK_DIR
```

If the caller is working in a source checkout that exposes official shell launchers, those launchers are equivalent operational wrappers, but this generated skill does not require or link to them.

## Offline artifacts and visualization

| Goal | Preferred route | Notes |
|---|---|---|
| Save predictions | `mim test ... --save-preds` | Produces prediction artifacts under the resolved work directory. |
| Paint evaluation images | `mim test ... --show-dir VIS_DIR` | Works on headless machines because it writes files instead of opening a window. |
| Browse transformed dataset samples | Use the data-preparation sub-skill first | Dataset browsing requires valid data files and may need headless output settings. |
| Analyze scheduler curves | Inspect config fields with the smoke helper first | Plotting is optional and should not block config validation. |

## Handoff between sub-skills

- Dataset or annotation failures: use [`data-preparation`](../../data-preparation/SKILL.md).
- Image/folder OCR prediction tasks: use [`ocr-inference`](../../ocr-inference/SKILL.md).
- Custom model, transform, registry, or visualizer development: use [`model-api-components`](../../model-api-components/SKILL.md).

## Stop conditions

Stop before launching a run when:

- The smoke helper cannot load the config.
- The config family does not match the checkpoint family.
- Required dataset files are missing.
- The task needs CUDA, distributed launch, or Slurm but the caller has not provided compatible hardware/service details.
- The command would download checkpoints or datasets and the user has not approved network/cache use.
