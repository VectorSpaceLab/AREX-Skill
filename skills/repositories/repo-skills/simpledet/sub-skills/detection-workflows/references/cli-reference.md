# Entry-point reference

Use the bundled `run_workflow.py` wrapper to make the checkout root explicit:

```bash
python <skill-root>/scripts/run_workflow.py --repo-root /path/to/simpledet \
  --entrypoint test --config config/faster_r50v1_fpn_1x.py --dry-run
```

Remove `--dry-run` only after setup, cache, checkpoint, and backend gates pass.
The wrapper itself has no install/download/cleanup behavior; the selected
checkout entry point may still allocate GPUs and write experiments.

## Config path conversion

SimpleDet converts a path such as
`config/finetune/faster_r50v1_fpn_voc07_1x.py` to the import name
`config.finetune.faster_r50v1_fpn_voc07_1x`. Keep the config argument in that
path form when calling the wrapper.

## Training

Use `--entrypoint train` and `--config CONFIG`:

```bash
python <skill-root>/scripts/run_workflow.py --repo-root /path/to/simpledet \
  --entrypoint train --config config/faster_r50v1_fpn_1x.py --dry-run
```

The underlying workflow calls `get_config(is_train=True)`, constructs CUDA
contexts from `KvstoreParam.gpus`, reads configured roidb caches, and writes
logs/symbol/checkpoint files under the experiment name. It has no safe built-in
short-run flag; change a copied config for a bounded experiment.

## Bbox evaluation

Use `--entrypoint test`; `--epoch` overrides the config epoch:

```bash
python <skill-root>/scripts/run_workflow.py --repo-root /path/to/simpledet \
  --entrypoint test --config config/faster_r50v1_fpn_1x.py --epoch 6 --dry-run
```

The workflow reads each configured cache split, loads the checkpoint, applies
NMS and COCO bbox evaluation, and writes a split result JSON under the
experiment directory. It handles class-aware and class-agnostic box widths.

## Mask evaluation

Use `--entrypoint mask-test`:

```bash
python <skill-root>/scripts/run_workflow.py --repo-root /path/to/simpledet \
  --entrypoint mask-test --config config/mask_r50v1_fpn_1x.py --epoch 6 --dry-run
```

Mask execution requires polygon records, mask-specific symbol/custom operators,
pycocotools, compatible checkpoint heads, and CUDA. It writes bbox/segmentation
results and a test graph snapshot.

## Speed benchmark

Use `--entrypoint speed` with required `--shape SHORT LONG`:

```bash
python <skill-root>/scripts/run_workflow.py --repo-root /path/to/simpledet \
  --entrypoint speed --config config/faster_r50v1_fpn_1x.py \
  --shape 800 1333 --gpu 0 --count 100 --dry-run
```

The underlying benchmark builds a dummy static batch, performs one warmup
forward, times `count` passes, and prints average milliseconds. It still
requires a CUDA-capable MXNet context and may write an inference graph.

## Arguments and side effects

- `--config`: required for every entry point.
- `--epoch`: optional for `test` and `mask-test` only.
- `--shape`: required for `speed`.
- `--gpu`: speed GPU index, default `0`.
- `--count`: speed timed iterations, default `100`.
- `--dry-run`: wrapper-only; prints command/cwd without executing.

Training mutates weights; test/mask-test read checkpoints and write results;
speed writes a graph snapshot. Treat all non-dry-run commands as side-effecting.
