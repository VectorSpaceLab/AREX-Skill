# Benchmarking LightGlue

This benchmark workflow measures the matcher stage of LightGlue on a single
image pair after feature extraction. It is intended to compare latency,
throughput, FlashAttention, `torch.compile`, and pruning choices on the same
hardware.

## Quick start

```bash
python scripts/benchmark_lightglue.py --help
python scripts/benchmark_lightglue.py \
  --features superpoint \
  --device auto \
  --num-keypoints 256 512 1024 2048 \
  --repeat 10 \
  --measure time \
  --save benchmark.png \
  --no-show
```

If you do not pass `--image0` / `--image1`, the script generates a deterministic
synthetic pair so it can run without repo assets. Use two local images for
meaningful numbers. The selected feature family can still require cached or
downloaded pretrained weights; use `--features sift` for an extractor-download-free
smoke path, and remember that the SIFT LightGlue matcher head may still load
matcher weights. For real images, `--max-resize` bounds the long side before
feature extraction so quick runs stay tractable.

## What the benchmark measures

- The timing loop measures `matcher({...})` only.
- Feature extraction happens before each keypoint-count run and is not included
  in the measured latency.
- A short warmup is run before the repeated measurements.
- The script reports mean wall time in milliseconds and derives throughput as
  pairs/second from the mean latency.

`--measure` controls the plotted y-axis:

| Mode | Meaning |
| --- | --- |
| `time` | Linear latency plot in ms |
| `log-time` | Log-scaled latency plot in ms |
| `throughput` | Pairs/second computed from mean latency |

## Feature and matcher pairing

Choose the extractor and matcher family together with `--features`:

- `superpoint`
- `disk`
- `aliked`
- `sift`
- `doghardnet`

The first use of a feature family may fetch pretrained extractor or matcher
weights. Do not treat that as a failure unless the download actually errors.

## Device selection

`--device auto` prefers CUDA, then MPS, then CPU. Explicit values fail fast if
that backend is unavailable.

| Device | Good for | Notes |
| --- | --- | --- |
| `cuda` | Best speed comparisons | Best place to test FlashAttention and `torch.compile` |
| `mps` | Apple Silicon smoke tests | Useful for correctness; not a substitute for CUDA benchmarking |
| `cpu` | Portable fallback | Best for pruning-threshold experiments and headless smoke tests |

## FlashAttention and compile decisions

- `--no-flash` forces the matcher into the non-flash path so you can compare the
  baseline against the accelerated path.
- Without `--no-flash`, LightGlue will still fall back automatically if the
  backend or installed PyTorch build does not expose the flash path.
- `--compile` enables the matcher compile path when the selected device is
  CUDA. On non-CUDA devices the script keeps running in eager mode and prints a
  note instead of failing.
- Compiled runs are most useful for larger keypoint counts. For small counts,
  compilation can add overhead or partially disable pruning.
- `--matmul-precision` maps to PyTorch's float32 matmul precision knob when the
  runtime exposes it. Keep `highest` for conservative numbers; compare `high`
  or `medium` only when you are explicitly studying throughput.

## Pruning decisions

Point pruning can help or hurt depending on the hardware and keypoint count.
The matcher exposes device-specific pruning thresholds, and the benchmark
script allows explicit overrides.

Recommended patterns:

- Compare default adaptive settings against a full matcher run with
  `--depth-confidence -1 --width-confidence -1` to see the cost of pruning and
  early stopping.
- On CPU-only systems, start with small keypoint counts and tune pruning
  thresholds manually if you want to study the overhead.
- If you want to force pruning to be active at all sizes, set the thresholds to
  `-1` for the devices you are testing.

Example CPU-only tuning run:

```bash
python scripts/benchmark_lightglue.py \
  --device cpu \
  --features superpoint \
  --num-keypoints 64 128 256 512 \
  --pruning-thresholds cpu=256 mps=-1 cuda=-1 flash=-1 \
  --repeat 5 \
  --no-show \
  --save cpu-pruning.png
```

## Safe short-run guidance

Use these settings for quick validation or a headless server session:

- `--repeat 3` to `--repeat 10`
- 3 to 4 keypoint values only
- `--device cpu` or `--device auto`
- `--no-show`
- `--save out.png`

For stable reporting, increase the repeat count and use a real image pair.

## Optional SuperGlue comparison

Some benchmark variants include a SuperGlue baseline for comparison, but that
baseline requires `hloc` and is outside this bundled LightGlue-only script. If
you add or use a SuperGlue comparison, treat a missing `hloc` dependency as an
optional-baseline issue, not as a LightGlue benchmark failure.

This comparison is only useful when matching SuperPoint-style features. Skip it
for regular LightGlue-only throughput runs.

## Common interpretation tips

- A faster `throughput` run may still be a worse end-to-end choice if feature
  extraction dominates the pipeline.
- Lower `width_confidence` usually increases pruning and can reduce latency,
  but only when the pruning overhead is worth it.
- `torch.compile` and FlashAttention are acceleration knobs, not accuracy
  changes.
