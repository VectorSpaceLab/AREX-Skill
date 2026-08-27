# Training workflows

## Preflight

```bash
SKILL_ROOT=/path/to/tacotron-skill
CHECKOUT_ROOT=/path/to/tacotron-checkout
cd "$SKILL_ROOT" && python sub-skills/data-preparation/scripts/validate_training_metadata.py --data-dir /data/tacotron/training
cd "$SKILL_ROOT" && python sub-skills/training/scripts/build_train_command.py --checkout-root "$CHECKOUT_ROOT" --base-dir /data/tacotron --input training/train.txt --hparams batch_size=16,max_iters=300
```

Inspect the resulting command, available disk, and expected duration before
running the equivalent training CLI in the checkout cwd. The original README
warns that full training can need at least 40 GB free disk. The builder and
validator do not establish TensorFlow runtime, audio quality, or convergence.

## Start or restore

Use the bundled training command builder with the selected `base_dir`, input,
name, and optional restore step. Review its printed command before intentionally
executing it; the printed command begins with `cd "$CHECKOUT_ROOT"`.
For example, build the equivalent of a fresh run and a restore run with
`--name ljspeech` and `--restore-step 150000`.

At checkpoints, expect model checkpoint files, summary data, a WAV sample, and
an alignment PNG in the log directory. Keep source commit, hparams, and data
layout recorded with the run. WAV samples use built-in Griffin-Lim, not a
neural vocoder.

## Optional CMUDict

Use `--hparams use_cmudict=True` only after placing the expected CMUdict file in
the preprocessed data directory. This changes text feeding behavior and should
be carried into synthesis when forced pronunciations are needed.
