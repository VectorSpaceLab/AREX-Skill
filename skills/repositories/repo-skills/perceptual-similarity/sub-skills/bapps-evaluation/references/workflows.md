# BAPPS Evaluation Workflows

## Purpose

Read this when you need the exact command shape for BAPPS 2AFC or JND scoring.

## Standard validation split scoring

The wrapper script mirrors the old validation workflow but uses the bundled helper:

```bash
python skills/disco/perceptual-similarity/sub-skills/bapps-evaluation/scripts/eval_valsets.sh
```

Default behavior:

- `DATASET_ROOT=dataset`
- `DATASET_MODE=2afc`
- `MODEL=lpips`
- `NET=alex`
- `BATCH_SIZE=50`
- `VERSION=0.1`

Set `USE_GPU=1` if your environment has a CUDA-capable Torch build.

## Direct helper usage

Score the official validation splits directly:

```bash
python skills/disco/perceptual-similarity/sub-skills/bapps-evaluation/scripts/score_bapps.py \
  --dataset_mode 2afc \
  --dataset_root dataset \
  --model lpips \
  --net alex
```

Score a tiny smoke fixture:

```bash
python skills/disco/perceptual-similarity/scripts/make_tiny_bapps_fixture.py --output-root /tmp/perceptual-similarity-fixture
python skills/disco/perceptual-similarity/sub-skills/bapps-evaluation/scripts/score_bapps.py \
  --dataset_mode 2afc \
  --dataset_root /tmp/perceptual-similarity-fixture/dataset \
  --datasets tiny \
  --model lpips \
  --net alex
```

## Metric choices

- `lpips` — learned LPIPS metric with linear heads.
- `baseline` — trunk features without the learned head.
- `l2` — Euclidean distance in Lab or RGB.
- `ssim` — DSSIM-style distance using a modern SSIM implementation.

Useful flags:

- `--net squeeze|alex|vgg`
- `--colorspace Lab|RGB`
- `--from_scratch`
- `--train_trunk`
- `--version 0.1|0.0`

## Layout expectations

- 2AFC splits must expose `ref/`, `p0/`, `p1/`, and `judge/`.
- JND splits must expose `p0/`, `p1/`, and `same/`.
- The helper requires aligned file names across the subdirectories.

## When to use the tiny fixture

Use the tiny fixture when you want to confirm that the evaluation path works end-to-end without downloading the full BAPPS dataset.

The tiny fixture is enough to verify:

- split discovery,
- image loading,
- label loading,
- metric construction,
- and the score aggregation path.
