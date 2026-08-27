---
name: training
description: "Guides Tacotron training command construction, hyperparameter
  overrides, data-feeder contracts, logs, checkpoints, TensorBoard, restore
  runs, and loss troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training

Use this route for training a Tacotron model, preparing a restore run, changing
hparams, interpreting logs/checkpoints, or planning resource requirements. Full
training is long-running and data-dependent; build and validate the command
before launching it.

## Workflow

1. Complete the data-preparation route and validate `training/train.txt`.
2. Choose a stable `--base_dir`, `--input`, and `--name`. The default log
   directory is `<base_dir>/logs-<name-or-model>`.
3. Pass hparam overrides as comma-separated `name=value` pairs. Preserve the
   same audio/model hparams for evaluation and serving.
4. Use `--restore_step N` only when `<log_dir>/model.ckpt-N` exists. Use
   `--git` only in a clean source checkout; it intentionally fails on dirty
   state.
5. Monitor summaries, generated audio, and alignments. If loss explodes or
   attention is lost, stop safely and consider restoring before the spike.
## Command roots and training boundary

Build commands from the skill root; execute the printed command only from the
Tacotron checkout root. The input and output paths remain relative to the
selected `--base-dir`, not to the skill directory.

```bash
SKILL_ROOT=/path/to/tacotron-skill
CHECKOUT_ROOT=/path/to/tacotron-checkout
cd "$SKILL_ROOT" && python sub-skills/training/scripts/build_train_command.py --checkout-root "$CHECKOUT_ROOT" --base-dir /data/tacotron --input training/train.txt --hparams batch_size=16,max_iters=300
```

The builder is dry-run only. Actual training requires validated metadata,
decoded/preprocessed audio arrays, the compatible TensorFlow 1.x stack, disk,
memory, and potentially GPU resources; it may write checkpoints, WAV samples,
alignments, and logs. No training convergence or checkpoint restore is implied
by command construction or metadata validation.

Read [`references/cli-reference.md`](references/cli-reference.md) for flags,
[`references/hparams.md`](references/hparams.md) for defaults and duration
calculations, [`references/workflows.md`](references/workflows.md) for a safe
sequence, and [`references/troubleshooting.md`](references/troubleshooting.md)
for data, loss, and restore failures. Use
[`scripts/build_train_command.py`](scripts/build_train_command.py) to construct
commands without starting a training loop.
