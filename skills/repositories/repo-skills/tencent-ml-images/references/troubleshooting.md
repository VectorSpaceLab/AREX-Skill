# Cross-cutting Troubleshooting

Use this page for installation, import, backend, and legacy TensorFlow issues
that affect more than one sub-skill.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `DuplicateFlagError: The flag 'log_dir' is defined twice` | TensorFlow 1.15/absl defines `log_dir` before the repo's `flags.py` registers it | Prefer the verified TensorFlow 1.6-era runtime for inspection; if you must use another runtime, patch the local checkout or adjust the flag name before execution |
| `SyntaxError: from __future__ imports must occur at the beginning of the file` | Several source scripts place a second string literal before `from __future__` imports | Patch the local checkout before direct execution, or treat the bundled helper scripts as the safe path and avoid invoking the original file directly |
| `tf.contrib` missing | TensorFlow 2-only or otherwise incompatible runtime | Use a TensorFlow 1.x runtime for this project; TF2 compat mode is not enough for `tf.contrib.image.rotate` |
| `cv2` missing | OpenCV not installed | Install OpenCV in the inspection environment before running inference helpers |
| `No files found for in data dir` | Training or dataset layout does not match the expected `train/` and `val/` shard directories | Check the data-preparation sub-skill and verify the split directory layout before invoking training |
| Checkpoint restore failure | Wrong prefix, missing checkpoint shards, or mismatched ResNet depth/class count | Validate the checkpoint with the checkpoint-inference inspector and confirm the intended model family |
| Training or finetuning appears stuck | Full ML-Images/ImageNet runs are large, long, and GPU-oriented | Stop and confirm the runtime budget, data layout, and whether a command template is all the user needs |
| Legacy downloader fails on modern Python | Original URL downloader is Python 2-only | Use the bundled Python 3 adaptation in the data-preparation sub-skill |

## What to do next

- If the error is about list parsing, image validation, or TFRecord writing,
  move to `data-preparation`.
- If the error is about flags, graph construction, or training commands, move
  to `resnet-training`.
- If the error is about checkpoint path, prediction output, or feature files,
  move to `checkpoint-inference`.

## Do not hide these issues

Do not claim full compatibility just because a helper script prints a command.
The generated skill should name the exact runtime or source patch needed when a
legacy TensorFlow issue blocks direct execution.
