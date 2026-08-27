# Utility script reference

## Log analysis

The log-analysis helper has two safe subcommands:

- `plot_curve` for loss or metric curves,
- `cal_train_time` for average iteration timing.

It reads JSON logs only. For evaluation-stage metrics, use the current parser flags `--eval` and `--eval-interval`. Older prose in the source tree may mention legacy wording such as `--mode eval` or `--interval`; prefer the parser in this bundle.

Common curve options:

- `--keys` chooses the metric or metrics to plot.
- `--legend` overrides the label list.
- `--backend` selects the Matplotlib backend.
- `--style` chooses the seaborn style.
- `--out` writes the figure instead of showing it.

Common timing option:

- `--include-outliers` keeps the first iteration from each epoch when averaging.

## FLOPs and throughput

### FLOPs helper

The FLOPs helper accepts a config and an input shape.

- `--modality point` expects a point-cloud shape.
- `--modality image` expects an image shape.
- `--modality multi` is declared but not implemented.
- `--cfg-options` can override config values before model construction.
- The results are approximate and may omit unsupported custom ops.
- Only use the output for rough comparison unless a separate verification step is available.

### Throughput benchmark helper

The benchmark helper loads `cfg.test_dataloader` and a checkpoint, then measures inference throughput.

- `--samples` limits the number of benchmarked samples.
- `--log-interval` controls progress reporting.
- `--amp` enables automatic mixed precision inference.
- `--fuse-conv-bn` fuses compatible layers before timing.
- The helper requires CUDA because it synchronizes the device every iteration.
- In this snapshot, the parser does not type-cast `--samples` or `--log-interval`, so explicit CLI overrides should be checked carefully before use.
- It is not a substitute for end-to-end evaluation or deployment validation.

## Config and checkpoint inspection

### Print config

- Prints the merged config after applying `--options` overrides.
- Useful for confirming inheritance and overrides without building a model.

### Fuse Conv+BN

- Builds a model from a config/checkpoint pair.
- Recursively fuses `Conv2d` followed by `BatchNorm2d` or `SyncBatchNorm`.
- Saves a new checkpoint with the fused weights.
- Use only when the architecture and layer order are known to be compatible.

### Publish checkpoint

- Removes optimizer state from a checkpoint.
- Saves the cleaned checkpoint under a hash-suffixed release filename.
- Intended for publication copies, not for training recovery.

## Legacy checkpoint migration

- The H3DNet and VoteNet conversion helpers rewrite older state-dict layouts into the current key layout.
- The RegNet conversion helper maps external pretrained weights into MMDetection-style keys.
- Treat these helpers as one-off file transforms, not as general model runners.

## Safe-use boundary

If a requested action needs a real server, a long benchmark, a missing custom op, or an unavailable checkpoint, stop at guidance and report the blocker instead of inventing a run.
