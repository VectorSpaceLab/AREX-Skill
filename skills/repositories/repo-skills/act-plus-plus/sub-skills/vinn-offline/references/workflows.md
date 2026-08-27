# VINN offline workflows

## Purpose

This reference covers the self-contained VINN preprocessing steps that can be run before any real-robot deployment: feature caching and k selection.

## 1) Cache image features

`vinn_cache_feature.py` loads a checkpoint path that encodes the task name and seed, then extracts ResNet18 features for every episode and every available camera.

### Naming contract

The source script expects a checkpoint filename like:

- `byol-<task>-DUMMY-seed-<seed>.pt`
- `byol_cotrain-<task>-DUMMY-seed-<seed>.pt` for cotrain variants

The script replaces `DUMMY` with each camera name when loading the matching per-camera ResNet weights.

### Output contract

It writes one file per episode with the layout described in [data formats](../../../references/data-formats.md):

- `/features/<camera>` with shape `(T, 512)`

### Notes

- The source code uses `torchvision.models.resnet18(pretrained=True)` as the feature backbone.
- The image pipeline resizes and center-crops to 120, then expands grayscale channels if needed.
- The source script expects dense episode indices with no gaps.

## 2) Select k offline

The raw source k-selection script includes an `IPython.embed()` stop, which makes it unsuitable for unattended runs. Use the bundled `select_k.py` helper instead.

### Algorithm shape

- Load train episodes from the first 80% of the episode ids.
- Load the cached feature files and concatenate all camera features along the feature axis.
- For each k in `1..max_k-1`, compute a softmax-weighted nearest-neighbor prediction and mean-squared error.
- Choose the minimum-loss k and save a plot in `ckpt_dir`.

### Dataset assumptions

- Episode ids must be dense from `0` to `N-1`.
- The cached feature files must exist for every episode id in the selected split.
- The `repr_type` is derived from the checkpoint name in the source script: `byol` or `byol_cotrain`.

## 3) What not to do with the raw eval script

The raw `vinn_eval.py` script is evidence for the evaluation logic, but it hard-codes a real-robot branch and imports `aloha_scripts.real_env` when executed. Treat it as an external deployment step, not a self-contained runtime helper.

## 4) Quick validation checklist

- Confirm the checkpoint naming pattern before caching features.
- Confirm the dataset directory contains dense episode indices and no missing feature files.
- Confirm CUDA is available before starting feature extraction.
- Confirm the feature directory and checkpoint directory are writable.
