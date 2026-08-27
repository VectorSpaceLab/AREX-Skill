---
name: bapps-evaluation
description: "Routes BAPPS 2AFC and JND evaluation workflows for LPIPS,
  baseline, L2, and SSIM-style metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# BAPPS Evaluation

Use this sub-skill when the task is about scoring a BAPPS split or comparing metric variants on the benchmark data.

## Trigger phrases

- "evaluate LPIPS on BAPPS"
- "score the validation splits"
- "run 2AFC or JND evaluation"
- "compare LPIPS, baseline, L2, and SSIM"
- "test the dataset loader on a tiny fixture"

## What this route covers

- BAPPS 2AFC scoring.
- BAPPS JND scoring.
- Split selection and dataset-root handling.
- Tiny smoke-fixture creation for benchmark-style tests.
- Metric selection across LPIPS, baseline, L2, and SSIM-style modes.

## What this route excludes

- Direct image-pair comparison.
- LPIPS-loss optimization.
- Training and checkpointing.

If the user wants to train or fine-tune, route to `bapps-training`. If the user only wants to compare images directly, route to `metric-usage`.

## Read these next

- `references/workflows.md` for the evaluation command matrix.
- `references/troubleshooting.md` for layout, loader, and SSIM compatibility issues.
- `../../references/bapps-dataset.md` for the expected split structure.
- `../../references/api-reference.md` for the verified public model and scoring APIs.

## Run these helpers

- `scripts/score_bapps.py` for BAPPS scoring.
- `scripts/eval_valsets.sh` for the standard validation-split wrapper.
- `../../scripts/make_tiny_bapps_fixture.py` to create a tiny BAPPS-style smoke fixture from bundled example assets.

## Working assumptions

- 2AFC splits contain `ref/`, `p0/`, `p1/`, and `judge/`.
- JND splits contain `p0/`, `p1/`, and `same/`.
- The bundled helper validates file alignment rather than silently guessing.
- The bundled helper uses a modern SSIM fallback, so it does not rely on the legacy `skimage.measure.compare_ssim` path.
