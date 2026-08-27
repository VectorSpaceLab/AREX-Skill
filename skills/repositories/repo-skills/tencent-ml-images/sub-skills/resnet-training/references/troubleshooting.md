# Training Troubleshooting

Use this when TensorFlow import, source execution, graph construction, training
input, checkpoint restore, or GPU configuration fails.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `DuplicateFlagError: The flag 'log_dir' is defined twice` | Newer TensorFlow 1.15 + absl stacks define `log_dir` before the repo's `flags.py` registers it | Prefer an older TensorFlow 1.x stack closer to the README's `>=1.6.0` evidence, or patch the local checkout to rename/guard the repo flag before execution |
| `SyntaxError: from __future__ imports must occur at the beginning of the file` | Several source scripts place a second string literal before `from __future__` imports | In a local checkout, move future imports immediately after the first module docstring/comments or remove unnecessary future imports; record this as a source compatibility patch |
| `No files found for in data dir ...` | The data root does not contain the split directory/files expected by `Dataset(...).data_files()` | Arrange shards as `<data-root>/train/*.tfrecords` and `<data-root>/val/*.tfrecords`, or set `--data_dir` to the parent containing those directories |
| Training loss shape errors | `--class_num` does not match dense label vector length, or scalar-label TFRecords are used for multi-label pretraining | Recreate TFRecords with the correct one-hot/scalar mode; use `11166` for ML-Images pretraining and `1000` for ImageNet finetuning |
| CPU run fails with NCHW/data-format errors | The examples use `NCHW`, which is usually GPU-oriented in TensorFlow | For CPU smoke, try `NHWC`/channels-last only after verifying the source code path; for faithful public examples use GPU-compatible `NCHW` |
| Many checkpoint variables are not restored | Checkpoint depth/class head does not match the graph, or variable names differ | Confirm `--resnet_size`, `--class_num`, and checkpoint source. Finetune restore intentionally skips `global_step`, `Momentum`, and `logits`; missing backbone variables are suspicious |
| Shell example writes paths with empty `NODE_NUM`/`GPU_NUM` | Public `example/train.sh` uses variables that are not defined in the script | Use `scripts/build_train_command.py` with explicit node/gpu labels and output directories |
| Finetune example rejects `--weight_decay_rate` or `--batch_norm_elipson` | Public shell example uses flag names not defined in `flags.py` | Use source-defined `--weight_decay` and `--batch_norm_epsilon`; verify a patched checkout before using aliases |
| `tf.contrib` missing | TensorFlow 2.x or incompatible TF runtime | Use TensorFlow 1.x. A TF2 `compat.v1` import is not enough for `tf.contrib.image.rotate` unless that symbol is supplied separately |
| Training appears stuck or too slow | Full ML-Images/ImageNet runs are large and long-running | Stop and confirm runtime budget, GPU availability, and whether the user only needs a command template or a tiny smoke |

## Source patch boundary

This skill does not silently modify a user's Tencent ML-Images checkout. When a
source compatibility issue blocks execution, state the patch required and ask
before changing code. Keep the distinction clear between source-backed commands
and any new modernization work.

## Safe diagnosis order

1. Render a command with the bundled builder instead of copying shell examples.
2. Check TensorFlow 1.x imports and `models.resnet` graph construction.
3. Validate TFRecord data and class counts through the data-preparation
   sub-skill.
4. Check checkpoint prefixes and restore scope.
5. Only then start full training or finetuning.
