---
name: train-configure
description: "Configure DreamerV3 training, evaluation, logging, checkpoints,
  and smoke runs from the CLI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Train Configure

Use this sub-skill when you need to:

- compose DreamerV3 config blocks from `dreamerv3/configs.yaml`
- launch, resume, or dry-run `dreamerv3.main.main`
- choose between `train`, `train_eval`, `eval_only`, `parallel`, and the `parallel_*` worker modes
- inspect startup flow, logging, checkpointing, and resume behavior
- run a bounded CPU or random-agent smoke before heavier GPU training

Read these bundled references first:

- `references/cli-and-config.md`
- `references/run-loops.md`
- `references/troubleshooting.md`

Run the bundled smoke helper when you want a one-command CPU validation:

- `python scripts/smoke_train_debug.py --help`
- `python scripts/smoke_train_debug.py --dry-run-config`
- `python scripts/smoke_train_debug.py`

## Covered surface

This sub-skill covers the control and configuration layer around the DreamerV3 training entry point:

- `dreamerv3/main.py`
  - `main`
  - `make_agent`
  - `make_env`
  - `make_replay`
  - `make_stream`
  - `make_logger`
- `dreamerv3/configs.yaml`
  - defaults
  - size presets
  - task presets
  - `debug`
  - `multicpu`
  - CLI override ordering
- `embodied/run/train.py`
- `embodied/run/train_eval.py`
- `embodied/run/eval_only.py`
- `embodied/run/parallel.py`
- README install/training/tips distilled into runtime guidance

## What to do

1. Start from the config reference and pick the smallest preset set that matches the goal.
2. Use the smoke helper for a bounded CPU or random-agent check before any larger run.
3. Keep `--logdir` stable when you want continuation, but start a fresh logdir after any model-shape change.
4. Use the run-loop reference to choose the correct script mode and checkpoint path.
5. If the issue is env wrappers, replay internals, or stream mechanics, hand off to `embodied-dataflow`.
6. If the issue is RSSM/encoder/decoder/model internals, hand off to `jax-models`.
7. If the issue is Docker, plotting, or backend ops, hand off to `results-ops`.

## Fast rules

- `--configs` blocks apply in order, then explicit CLI flags win.
- `debug` is for fast validation, not for learning a good policy.
- `random_agent` is the cheapest way to check env, replay, logger, and checkpoint plumbing.
- `train_ratio` is interpreted relative to batch size and batch length, so changing those changes the effective update cadence.
- `task` must resolve to a supported suite/task pair or env creation will fail before training starts.
- Reusing a checkpoint after changing a size preset or other model-shape-sensitive config is unsafe unless compatibility is known.

## Expected outputs

A healthy bounded training smoke should usually produce at least:

- `config.yaml`
- `metrics.jsonl`
- `scores.jsonl`
- `ckpt/`
- terminal metrics and episode summaries

For parallel modes, expect a nested checkpoint tree such as `ckpt/agent`, `ckpt/replay`, and `ckpt/logger`.

## When to stop here

Do not dig into source-repo implementation details beyond the bundled references if you only need to:

- choose a config preset
- verify a small training or evaluation smoke
- resume from a checkpoint in a compatible logdir
- decide whether a failure belongs to config, logging, checkpointing, or run-loop control
