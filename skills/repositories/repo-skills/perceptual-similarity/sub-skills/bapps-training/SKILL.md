---
name: bapps-training
description: "Routes BAPPS training, fine-tuning, checkpointing, and smoke-test
  workflows for the PerceptualSimilarity package."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# BAPPS Training

Use this sub-skill when the task is about training or fine-tuning the LPIPS metric on BAPPS-style 2AFC data.

## Trigger phrases

- "train LPIPS"
- "fine-tune on BAPPS"
- "run the scratch variant"
- "run the tune variant"
- "smoke-test the training path"
- "save checkpoints"

## What this route covers

- LPIPS/BAPPS ranking-loss training.
- Checkpoint directory creation and file naming.
- Smoke-friendly one-step or one-epoch runs.
- Scratch and trunk-tuning modes.
- Training-specific troubleshooting.

## What this route excludes

- Direct image-pair comparison.
- Benchmark scoring only.
- Dataset-download automation.

If the task is only about scoring a split, route to `bapps-evaluation`. If the task is about direct LPIPS distances or LPIPS loss visualization, route to `metric-usage`.

## Read these next

- `references/workflows.md` for the training command matrix.
- `references/troubleshooting.md` for checkpoint, dependency, and runtime issues.
- `../../references/bapps-dataset.md` for the expected split layout.
- `../../references/api-reference.md` for the verified `Trainer` API.

## Run these helpers

- `scripts/train_bapps.py` for the bundled training loop.
- `scripts/train_test_metric.sh` for the standard train-then-score wrapper.
- `scripts/train_test_metric_scratch.sh` for the scratch variant.
- `scripts/train_test_metric_tune.sh` for the trunk-tune variant.
- `../../scripts/make_tiny_bapps_fixture.py` to create a tiny BAPPS-style smoke fixture.

## Working assumptions

- Training uses 2AFC splits with `ref/`, `p0/`, `p1/`, and `judge/`.
- The bundled helper creates the checkpoint directory automatically.
- The bundled helper avoids the old HTML/visdom stack used by the stock `train.py`.
- The smoke default is intentionally bounded so it is safe to run on small fixtures.
