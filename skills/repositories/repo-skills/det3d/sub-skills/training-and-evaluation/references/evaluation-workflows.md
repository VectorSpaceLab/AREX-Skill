# Evaluation and Inference

The test path sets validation data to test mode, builds a deterministic
dataloader, constructs the detector, loads checkpoint metadata/classes, moves
batches to the selected CUDA device, accumulates predictions across ranks, and
calls the dataset's evaluation method.

Output guidance:

- Pickle output stores result objects for later inspection.
- JSON output is a prefix; source code strips a trailing `.json`.
- Text KITTI export needs a writable prediction directory and dataset-relative
  label/split paths. Do not reuse legacy hard-coded paths.
- `--show` introduces display/visualization dependencies; prefer saved outputs
  on headless hosts.

Metric names and formats depend on KITTI, nuScenes, or Lyft. Confirm split,
classes, coordinate frames, score thresholds, and evaluator version before
comparing against README model-zoo numbers.
