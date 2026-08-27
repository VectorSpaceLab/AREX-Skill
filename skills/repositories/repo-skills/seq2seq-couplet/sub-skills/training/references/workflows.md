# Training Workflows

## Purpose

Read this when you need the exact sequence for starting a training run,
continuing an existing checkpoint, or validating the training graph with the
bundled smoke fixture.

## Workflow summary

1. Prepare aligned train and test files with the verified vocabulary order.
2. Choose a checkpoint output directory.
3. Run the bundled training wrapper with explicit file paths.
4. Watch the save and eval cadence.
5. Resume with `--restore-model` and a `start` step offset when needed.

## Real-data training

Use `scripts/train_couplet.py` when you have your own aligned dataset.
Run the examples from the `seq2seq-couplet` skill root. The wrapper exposes the
key model parameters as flags, validates line counts and batch-size feasibility,
and avoids source-file edits.

Example:

```bash
python sub-skills/training/scripts/train_couplet.py \
  --train-input <train.in.txt> \
  --train-target <train.out.txt> \
  --test-input <test.in.txt> \
  --test-target <test.out.txt> \
  --vocab-file <vocabs.txt> \
  --output-dir <checkpoint-dir> \
  --num-units 1024 \
  --layers 4 \
  --dropout 0.2 \
  --batch-size 32 \
  --learning-rate 0.001 \
  --epochs 5000000
```

## Continuing a checkpoint

When resuming, keep the same vocabulary and model size, then set
`--restore-model` and a `--start` step offset that matches the step count you
have already run.

Example:

```bash
python sub-skills/training/scripts/train_couplet.py \
  --train-input <train.in.txt> \
  --train-target <train.out.txt> \
  --test-input <test.in.txt> \
  --test-target <test.out.txt> \
  --vocab-file <vocabs.txt> \
  --output-dir <checkpoint-dir> \
  --restore-model \
  --start 102500
```

## What the wrapper maps onto

The wrapper uses the bundled `Model` runtime copy and passes the explicit file
paths into its constructor. The relevant methods are:

- `Model.train(epochs, start=0)`
- `Model.eval(train_step)`

The `save_step` and `eval_step` settings are step counters, so step `0` already
triggers both save and eval when the loop starts at zero. The bundled wrapper's
fresh-run default starts at step `1` to avoid surprising step-zero eval behavior;
set `--start 0` only when you intentionally want the exact legacy cadence.

## Tiny smoke path

Use `scripts/train_smoke.py` when you only need to prove that the training graph
still builds and can run on a tiny fixture.

The smoke helper:

- writes a deterministic aligned dataset,
- creates a vocabulary with `<s>` and `</s>` first,
- trains a very small model for one epoch,
- checks that the checkpoint directory was created.

This is the fastest end-to-end way to confirm the data layout and TensorFlow
runtime before using a real dataset.

## Notes that matter during training

- The reader drops tokens that are absent from the vocabulary.
- The reader's `data_size` is integer division by batch size, so choose a batch
  size that does not accidentally hide most of the dataset.
- The evaluation path restores the checkpoint before computing BLEU.
- The output directory must exist or be creatable before training starts.

## When to jump elsewhere

- If the dataset or vocabulary format is unclear, read
  `data-formats.md` first.
- If the run fails with protobuf, NumPy symbolic-tensor, or TensorFlow import
  errors, read the root troubleshooting reference.
- If you need to expose the model through an API, move to the inference
  sub-skill instead of extending the training workflow.
