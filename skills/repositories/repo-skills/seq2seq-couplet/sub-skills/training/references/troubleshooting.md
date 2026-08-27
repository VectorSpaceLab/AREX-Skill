# Training Troubleshooting

## Purpose

Read this for training-specific failures that are not covered by the root
troubleshooting page.

## Common issues

### Checkpoint restores but BLEU stays flat

**Likely causes**

- The dataset is too small.
- The input and target files are not actually aligned.
- The vocabulary is missing important tokens, so many words are dropped.

**Recovery**

- Verify the line alignment and the vocabulary order.
- Increase the real dataset size before tuning hyperparameters.
- Use the smoke fixture only to check that the graph runs, not as a quality
  benchmark.

### Training prints samples that look wrong immediately

**Likely causes**

- The model is still at step 0 or has not seen enough data.
- Batch size or learning rate is too aggressive for the dataset size.

**Recovery**

- Run more epochs or reduce the learning rate.
- Keep the smoke fixture for graph verification only.

### `restore_model=True` fails on resume

**Likely causes**

- The checkpoint directory does not contain a compatible checkpoint.
- The vocab file changed after the checkpoint was created.
- The hidden size or number of layers changed.

**Recovery**

- Reuse the exact same vocab and model shape.
- Point `--output-dir` at the directory that already contains the checkpoint.
- If the vocabulary changed, retrain instead of resuming.

### Some examples never seem to be used

**Likely cause**

- The reader computes data size with integer division by batch size.

**Recovery**

- Choose a batch size that divides the aligned example count.
- Or accept the dropped tail and adjust the dataset size accordingly.

## Environment failure modes during training

If training fails before any batch runs, separate environment issues from data
or checkpoint issues first:

- protobuf descriptor errors mean TensorFlow 1.15 needs the pinned protobuf
  version from the root dependency reference;
- symbolic Tensor / NumPy conversion errors in beam-search graph construction
  mean NumPy is too new and should be pinned to `1.18.5`;
- legacy CUDA warnings are acceptable on the CPU path unless the user explicitly
  requires GPU acceleration.

## Practical debugging steps

1. Run the root `scripts/check_env.py` helper.
2. Run `scripts/train_smoke.py` to prove the graph still works.
3. Compare the smoke dataset layout against your real files.
4. Only then change hyperparameters or checkpoint paths.
