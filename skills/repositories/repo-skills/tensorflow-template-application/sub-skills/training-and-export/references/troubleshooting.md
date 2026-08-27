# Troubleshooting

This page focuses on the failures that show up most often in the dense and sparse training/export workflows.

## Runtime and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError` or `AttributeError` for `tf.app`, `tf.Session`, `tf.contrib`, or `tf.python_io` | The environment is not a TF1-compatible runtime | Use a TF1.x environment for the training/export workflows; TF2 by itself is not enough for the source trainers |
| `DuplicateFlagError` when importing both dense and sparse trainers in one process | Both modules register overlapping `tf.app.flags` at import time | Keep the trainers in separate Python processes; do not import both trainer modules in a single interpreter session |
| `--help` does not behave like a normal argparse program for the source trainers | The source scripts use TF1 flag registration instead of `argparse` | Use the bundled command builder for a safer help surface and keep source trainer imports isolated |

## Flag-name and mode mismatches

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Unknown command line flag train_file` on the current dense trainer | The README example uses old queue-era names while the current dense trainer expects `train_files` and `validation_files` | Use the current dense flags or let `scripts/build_training_command.py` translate the alias names for you |
| `Unknown command line flag input_file_format` or `optmizier` | README-era spelling from older examples | Use `file_format` and `optimizer`; the command builder normalizes the common aliases |
| `savedmodel` does nothing on the sparse trainer | Sparse export uses `save_model`, not `savedmodel` | Switch to `mode=save_model` for the sparse path |
| `scenario` looks ignored on the sparse trainer | The sparse path is classification-only in the current source | Do not expect a sparse regression branch; route regression questions back to the dense trainer |

## Data and shape failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `InvalidArgumentError`, reshape failure, or placeholder shape mismatch | `feature_size` does not match the actual training or inference layout | Recheck the model family and the data width before checking the checkpoint |
| Dense `cnn`, `lstm`, `bidirectional_lstm`, or `gru` fails on reshape | Those paths hard-code the flat size to a 3x3 layout | Use a 9-feature toy input for those branches or choose a flat model such as `dnn` or `lr` |
| Dense `customized_cnn` fails on reshape | The source path expects a 512x512-style flat vector and uses the training batch size in the reshape | Make the feature vector 512*512 wide and keep the batch-size assumptions aligned |
| Sparse inference gives the wrong width or index error | The sparse `feature_size` is the embedding width / vocabulary width, not the number of nonzero values | Make sure the sparse TFRecords or LibSVM ids stay within that width |
| Sparse `label_type=float` still behaves like integer labels | The float branch in the current source is cast to `int32` after parsing | Prefer integer labels unless you are intentionally matching the source branch |
| Dense regression gives odd loss behavior | The default dense loss is still `sparse_cross_entropy` unless you override it | Set `--loss mean_square` when you really want the regression branch |
| Dense `cross_entropy` behaves unexpectedly | The branch is more fragile than `sparse_cross_entropy` because label shape must match the logits expectation | Prefer `sparse_cross_entropy` for classification unless you know the label encoding matches the branch |

## Checkpoint and export failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No checkpoint for exporting model` or `No checkpoint found` | You asked for export or inference before any checkpoint existed | Run training first, or point the run at a checkpoint directory that already contains a checkpoint |
| `The model exists in path` during export | `model_path/model_version` already exists | Pick a new version number or remove the old export directory before exporting again |
| Export succeeds but a client cannot load the model | The SavedModel signature keys or tensor names do not match the client expectation | Check `references/model-overview.md` for the dense vs sparse input/output names and select the default signature key first |
| A dense serving client cannot find the custom signature | The source dense exporter adds a nonstandard secondary signature name and method name | Prefer the default serving signature and verify the tensor names instead of assuming the custom name is the one the client should call |
| Inference reads a checkpoint from the wrong run | Multiple runs share one checkpoint directory | Keep checkpoint, tensorboard, and export directories separate per experiment |

## TensorBoard and event-file issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `scripts/read_tensorboard_events.py` prints nothing | The event path points to the wrong directory or the tag names do not match the actual summaries | Point the helper at the event file or log directory and drop the tag filter once to inspect all scalar names |
| TensorBoard shows no new data | The trainer wrote to a different `output_path` than the one you opened | Match the trainer's `output_path` to the TensorBoard logdir |
| The source reader only found `loss_1` when the current trainer writes `loss` | The tag name changed across graph branches and old logs | Use the bundled helper's `--tag` option to inspect the actual tag names in the file |

## Queue and distributed failure modes

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Queue-based training appears to hang | Queue runners are waiting on data or `min_after_dequeue` / batch sizing is too aggressive for the dataset | Reduce the queue buffer, verify the input file list, or switch back to the current dense trainer |
| Distributed worker/ps jobs never make progress | One or more cluster roles were not started with the correct host lists or job name | Start separate ps and worker processes and check the `ps_hosts`, `worker_hosts`, `job_name`, and `task_index` values |
| Distributed ps tasks consume GPUs unexpectedly | The source notes expect ps tasks to run on CPU only | Force the ps process onto CPU-only devices and reserve GPUs for workers |

## Known fragile source branches

- Dense `cross_entropy` is less forgiving than the default sparse cross-entropy branch.
- Sparse `lr` currently reaches for `FLAGS.input_units`, which is not the declared sparse flag name.
- The queue-era and distributed trainers are useful for compatibility notes, but the current dense `tf.data` path is the cleaner default.

## Quick recovery order

1. Check the runtime first: TF1 symbols, flags, and process isolation.
2. Check the flag names against `references/cli-reference.md`.
3. Check the model and loss choice against `references/model-overview.md`.
4. Check data width, sparse shape, and label encoding.
5. Check the checkpoint/export directories.
6. Check the TensorBoard event path and tag names.
