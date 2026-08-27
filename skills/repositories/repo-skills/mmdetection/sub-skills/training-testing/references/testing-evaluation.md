# Testing and Evaluation

MMDetection 3.3.0 evaluation is driven by `tools/test.py`, which loads a config, merges `--cfg-options`, sets `cfg.load_from` to the checkpoint argument, optionally enables visualization or TTA, builds an MMEngine runner, appends `DumpDetResults` when `--out` is supplied, and calls `runner.test()`.

## Preflight checklist

| Check | Why it matters | Action |
|---|---|---|
| Config and checkpoint match | Architecture, classes, and metadata should match the saved weights | Use the checkpoint from the same experiment when possible |
| Dataset and evaluator are configured | Metrics come from `test_evaluator`; dataloading from `test_dataloader` | Route metric/dataset changes to datasets-evaluation |
| `--out` suffix is valid | `tools/test.py` asserts pickle output suffixes only | Use `.pkl` or `.pickle` |
| Visualization mode is safe | `--show` requires a GUI; `--show-dir` writes images without a GUI | Prefer `--show-dir` on servers |
| Distributed port is free | `dist_test.sh` defaults to port 29500 | Set `PORT` for concurrent jobs |

## Single GPU or CPU testing

```bash
python tools/test.py CONFIG.py CHECKPOINT.pth \
  --work-dir work_dirs/eval_EXP \
  --out work_dirs/eval_EXP/results.pkl
```

CPU smoke test:

```bash
CUDA_VISIBLE_DEVICES=-1 python tools/test.py CONFIG.py CHECKPOINT.pth \
  --work-dir work_dirs/cpu_eval
```

CPU evaluation is useful for debugging config and checkpoint loading, but it is slow for full detection benchmarks.

## Distributed testing

`tools/dist_test.sh` invokes PyTorch distributed launch and forwards trailing flags to `tools/test.py`.

```bash
PORT=29500 CUDA_VISIBLE_DEVICES=0,1,2,3 bash tools/dist_test.sh \
  CONFIG.py CHECKPOINT.pth 4 \
  --work-dir work_dirs/eval_EXP \
  --out work_dirs/eval_EXP/results.pkl
```

For multi-node testing, set `NNODES`, `NODE_RANK`, `MASTER_ADDR`, and a shared `PORT` just as in distributed training.

## Slurm testing

`tools/slurm_test.sh` runs `srun` and calls `python -u tools/test.py CONFIG CHECKPOINT --launcher=slurm ...`.

```bash
GPUS=8 GPUS_PER_NODE=8 CPUS_PER_TASK=5 bash tools/slurm_test.sh \
  PARTITION JOB_NAME CONFIG.py CHECKPOINT.pth \
  --work-dir work_dirs/eval_EXP \
  --out work_dirs/eval_EXP/results.pkl
```

Use `SRUN_ARGS` for account, QoS, time, or node selection arguments supplied by the cluster.

## Testing outputs

| Option | Output | Notes |
|---|---|---|
| `--work-dir DIR` | Evaluation metrics and runtime artifacts | Defaults to `./work_dirs/<config-stem>` if unset in config |
| `--out results.pkl` | Pickled predictions via `DumpDetResults` | Must end with `.pkl` or `.pickle`; useful for offline analysis |
| `--show` | Interactive painted images | Single-process debugging only; requires display server |
| `--show-dir DIR` | Painted images under the run output tree | Safer than `--show` on headless servers |
| `--tta` | Test-time augmentation wrapper | Adds default TTA pieces if missing, with warnings |
| `--cfg-options test_dataloader.batch_size=2` | Batch inference during test | Increase only if memory allows |

## Evaluation metrics and result dumping

Metrics are controlled by the config's `test_evaluator`, not by a standalone `--eval` flag. To change metrics, classwise reporting, or official-server output prefixes, pass config overrides or edit the config.

Examples:

```bash
python tools/test.py CONFIG.py CHECKPOINT.pth \
  --cfg-options test_evaluator.classwise=True
```

```bash
python tools/test.py CONFIG.py CHECKPOINT.pth \
  --cfg-options test_evaluator.outfile_prefix=work_dirs/coco_test/test
```

COCO test-dev style configs may emit JSON files such as `test.bbox.json` and `test.segm.json` from evaluator settings. Cityscapes test configs may emit png/txt submission artifacts. Route dataset-specific submission setup to `datasets-evaluation`.

## Visualization and TTA

Prefer `--show-dir` over `--show` unless the user has a local GUI session. `--show-dir` triggers the visualization hook and writes rendered images without needing an X server.

`--tta` wraps the model with `DetTTAModel`. If the config lacks `tta_model` or `tta_pipeline`, `tools/test.py` injects defaults and warns. For production TTA, inspect or define TTA config explicitly through `configuration-model-zoo`.

## No-ground-truth testing

MMDetection can run test-style inference without ground-truth annotations when the dataset is converted to COCO-style image records and the config's `test_dataloader`/`test_evaluator` are adjusted for the target output. Dataset conversion and evaluator edits belong to `datasets-evaluation`; this sub-skill handles the final `tools/test.py` command after the config is ready.
