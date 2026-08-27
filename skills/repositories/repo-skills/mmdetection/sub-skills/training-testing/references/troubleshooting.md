# Training and Testing Troubleshooting

## Fast diagnosis table

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: mmcv._ext` | `mmcv-lite` or incompatible compiled ops are installed | Install full `mmcv` matching the torch/CUDA stack |
| Training restarts from epoch 0 after interruption | Used fine-tuning `load_from` instead of resume | Use `--resume` with the same `work_dir`, or `--resume CHECKPOINT.pth` |
| Fine-tuning unexpectedly resumes old optimizer state | Used `--resume` for pretrained weights | Put `load_from` in the config and omit `--resume` |
| `--auto-scale-lr` raises missing key error | Config lacks `auto_scale_lr.enable` or `auto_scale_lr.base_batch_size` | Inspect inherited schedule config and add the expected block before using the flag |
| Distributed job hangs or address already in use | Port collision, mismatched `MASTER_ADDR`, or rank variables | Set a unique `PORT`; verify `NNODES`, `NODE_RANK`, and `MASTER_ADDR` on every node |
| Slurm job starts but no GPUs are used | Scheduler variables or partition resources are wrong | Check `GPUS`, `GPUS_PER_NODE`, `--gres`, partition, and cluster account flags |
| `--out` test command fails assertion | Output path does not end in `.pkl` or `.pickle` | Rename output file to a pickle suffix |
| Visualization fails with `cannot connect to X server` | `--show` on a headless machine | Use `--show-dir` instead |
| Checkpoint load reports class/head mismatch | Config class count or head definition differs from checkpoint | Update `num_classes`, dataset metainfo, or use a matching checkpoint |
| Metrics are missing | `test_evaluator` is absent, replaced, or configured for format-only output | Inspect evaluator config; route metric setup to datasets-evaluation |

## Resume and checkpoint state

MMDetection exposes two different checkpoint intents:

- `--resume`: continue an interrupted run, restoring model weights, optimizer state, scheduler state, and epoch/iteration counters.
- Config `load_from`: initialize weights for a new run, usually fine-tuning, without restoring optimizer/scheduler progress.

When `--resume` is passed with no value, MMDetection auto-resumes from the latest checkpoint in `work_dir`. When `--resume CHECKPOINT.pth` is passed, it resumes from that explicit checkpoint. Keep `work_dir` stable if relying on automatic latest-checkpoint discovery.

## `work_dir` outputs and surprises

`work_dir` priority is: CLI `--work-dir`, then `work_dir` inside the config, then `./work_dirs/<config-stem>`. Use an explicit `--work-dir` for reproducible commands and to avoid mixing outputs from different experiments.

Typical outputs include:

- training logs and JSON log records;
- checkpoints such as `epoch_*.pth` and `latest.pth`;
- validation and test metric records;
- visualization backend artifacts;
- painted images when `--show-dir` is used;
- pickle predictions when `--out` is used in testing.

## Distributed and Slurm port conflicts

`dist_train.sh` and `dist_test.sh` default to `PORT=29500`. Two jobs on the same host must not share the same visible devices and port.

Safe single-node pattern:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 PORT=29500 bash tools/dist_train.sh CONFIG_A.py 4 --work-dir work_dirs/job_a
CUDA_VISIBLE_DEVICES=4,5,6,7 PORT=29501 bash tools/dist_train.sh CONFIG_B.py 4 --work-dir work_dirs/job_b
```

For Slurm, set separate ports through config options when cluster networking uses the config's distributed parameters. Prefer `env_cfg.dist_cfg.port` for MMDetection 3.x / MMEngine-style configs; use `dist_params.port` only for older migrated configs that still define that key.

```bash
GPUS=4 bash tools/slurm_train.sh PARTITION job_a CONFIG_A.py work_dirs/job_a --cfg-options env_cfg.dist_cfg.port=29500
GPUS=4 bash tools/slurm_train.sh PARTITION job_b CONFIG_B.py work_dirs/job_b --cfg-options env_cfg.dist_cfg.port=29501
```

## Learning-rate scaling pitfalls

`--auto-scale-lr` is safe only when the config defines `auto_scale_lr.base_batch_size` for the schedule. Many standard configs use base batch size 16, but configs with names like `32x3` or `8x1` may define a different base size. Do not edit `base_batch_size` just to force the flag; instead align actual GPU count and dataloader batch size with the intended scaling rule.

If overriding `train_dataloader.batch_size`, either enable `--auto-scale-lr` with a valid `auto_scale_lr` block or manually adjust `optim_wrapper.optimizer.lr`.

## CPU caveats

CPU training and testing use the same scripts after `CUDA_VISIBLE_DEVICES=-1`, but they are slow and can mask GPU-only problems. For CPU smoke tests, reduce worker counts and choose tiny datasets or short loops through config overrides. Route loop customization to `customization-extension` if the user needs a custom debug loop.

## Checkpoint metadata and class names

Evaluation and visualization may depend on checkpoint metadata and dataset metainfo. If labels are wrong or class counts mismatch, inspect:

- `model.*.num_classes` in the config;
- dataset `metainfo` and annotation categories;
- whether checkpoint metadata contains class names from a different dataset;
- whether the loaded checkpoint belongs to a different architecture variant.

Use `datasets-evaluation` for dataset category fixes and `configuration-model-zoo` for selecting a compatible config/checkpoint pair.
