# Training and model troubleshooting

## `train.py` fails immediately on import

Likely causes:

- TensorFlow 2.x was installed instead of TensorFlow 1.x.
- `model/` is not on the Python path because the command was run from the wrong
  working directory.
- A dependency such as `scipy`, `numpy`, `Pillow`, or `functools32` is missing.

Recovery: use the original legacy environment, run from the zi2zi checkout, and
check dependency versions before launching training.

## `d_loss` collapses or samples look saturated

Likely causes:

- The discriminator has become too strong.
- Fine-tuning is too narrow or the data set is too small.
- Label distribution is imbalanced or embedding labels are reused.

Recovery: enable `--flip_labels=1` during later fine-tuning, inspect the label
set, and verify that the data packager produced records for all intended styles.

## Checkpoints do not restore

Likely causes:

- `--batch_size` changed between training and restore.
- `--embedding_num` or `--embedding_dim` changed.
- `--inst_norm` changed or a different normalization branch was used.
- The checkpoint directory points at the wrong experiment or run number.

Recovery: match the original hyperparameters and restore from the concrete
`checkpoint/experiment_<id>_batch_<batch>/` directory.

## Out-of-memory or device errors

Likely causes:

- Batch size is too large for the GPU.
- Other jobs already consume most GPU memory.
- Legacy TensorFlow/CUDA is incompatible with the current driver or GPU.

Recovery: reduce batch size, hide CUDA for a CPU graph check, or move the job to
legacy-compatible hardware. Do not claim success from an import alone.

## Missing sample or log directories

`train.py` creates `checkpoint/`, `logs/`, and `sample/` under the experiment
directory, but the command will still fail if the parent experiment directory is
unwritable or the data subdirectory is missing.

Recovery: create `experiment/data/` with valid `.obj` files first, then rerun.

## Input size or batch padding mismatch

If training fails deep in the graph, inspect the packaged JPG sizes and batch
counts. The model expects paired images with a consistent split width and a
fixed batch size. Use the data-preparation inspector to catch malformed or empty
object files before re-running the training loop.
