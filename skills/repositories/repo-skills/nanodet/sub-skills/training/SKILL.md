---
name: "training"
description: "Routes NanoDet training, validation, checkpoint, logging,
  optimizer, and evaluator workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# training

Use this sub-skill when you need to train, validate, test, resume, or debug a NanoDet Lightning run.

## Use this route for

- Launching training or evaluation from a config.
- Resuming from `model_last.ckpt` or loading a specific checkpoint.
- Inspecting the Lightning task, evaluator, logger, EMA, and optimizer behavior.
- Understanding where checkpoints, logs, and evaluation files are written.
- Converting a legacy `.pth` checkpoint into the Lightning format.

## Do not use this route for

- Config syntax and dataset layout questions. Use `dataset-config` first.
- Demo inference or export. Use `inference-export` instead.

## Read first

- `references/workflows.md` for the train / test / checkpoint flow.
- `references/troubleshooting.md` for runtime and config failures.
- `../../references/api-reference.md` for the verified builders and helper APIs.

## Skill-owned scripts

- `scripts/train.py` — run a NanoDet training job from a config.
- `scripts/test.py` — run validation or test-time evaluation from a config and checkpoint.
- `scripts/convert_old_checkpoint.py` — convert a legacy checkpoint to the Lightning format.

## Typical workflow

1. Validate the config and dataset with `dataset-config`.
2. Run the skill-owned training launcher.
3. Inspect `save_dir`, `model_last.ckpt`, `model_best/`, `eval_results.txt`, and logs.
4. Use the test launcher or checkpoint converter when you need to reproduce or debug a saved model.

## Cross-links

- If the problem is really a config or dataset issue, switch back to `dataset-config`.
- If you only need inference or export after training, switch to `inference-export`.
