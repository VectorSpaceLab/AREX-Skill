# Workflows Overview

## Purpose

Read this for a quick map from common user requests to the correct sub-skill and bundled helper scripts.

## Workflows

### Compare images or inspect LPIPS maps

Use `sub-skills/metric-usage/` when the task is about two images, two directories, all pairs in a directory, or LPIPS as a perceptual loss.

Useful helpers:

- `sub-skills/metric-usage/scripts/compare_images.py`
- `sub-skills/metric-usage/scripts/optimize_lpips.py`

Typical smoke data:

- `assets/examples/ex_ref.png`
- `assets/examples/ex_p0.png`
- `assets/examples/ex_p1.png`
- `assets/examples/ex_dir0/`
- `assets/examples/ex_dir1/`
- `assets/examples/ex_dir_pair/`

### Score BAPPS splits

Use `sub-skills/bapps-evaluation/` when the task is about 2AFC or JND evaluation, split selection, or metric comparison on the BAPPS dataset.

Useful helpers:

- `sub-skills/bapps-evaluation/scripts/score_bapps.py`
- `sub-skills/bapps-evaluation/scripts/eval_valsets.sh`

For smoke tests, create a tiny fixture first:

- `scripts/make_tiny_bapps_fixture.py`

### Train or fine-tune on BAPPS

Use `sub-skills/bapps-training/` when the task is about training, fine-tuning, checkpointing, or smoke-testing the ranking loss path.

Useful helpers:

- `sub-skills/bapps-training/scripts/train_bapps.py`
- `sub-skills/bapps-training/scripts/train_test_metric.sh`
- `sub-skills/bapps-training/scripts/train_test_metric_scratch.sh`
- `sub-skills/bapps-training/scripts/train_test_metric_tune.sh`
- `scripts/make_tiny_bapps_fixture.py`

## Choosing between routes

- If the request is only about a pair of images or an LPIPS distance map, start with `metric-usage`.
- If the request names BAPPS, 2AFC, JND, train/val splits, or evaluation metrics, start with `bapps-evaluation`.
- If the request names checkpoint saving, `from_scratch`, `train_trunk`, or optimization of the ranking loss, start with `bapps-training`.

## Smallest useful path

For a quick end-to-end smoke test:

1. Run `scripts/make_tiny_bapps_fixture.py`.
2. Score the tiny 2AFC split with `bapps-evaluation`.
3. Train for one epoch or one step with `bapps-training`.

For a direct LPIPS smoke test:

1. Use `metric-usage` on `assets/examples/ex_ref.png` and `assets/examples/ex_p0.png`.
2. Compare the result against `assets/examples/ex_p1.png`.
