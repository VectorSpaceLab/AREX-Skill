# Metric Families

PySOT’s toolkit uses one of four benchmark classes depending on the dataset family. All metric classes load tracker files through the dataset adapter after `dataset.set_tracker(<tracker_dir>, <tracker_names>)`.

## OPEBenchmark

Used for OTB, UAV, NFS, and LaSOT-style one-pass evaluation.

Typical evaluation calls:

```python
benchmark = OPEBenchmark(dataset)
success_ret = benchmark.eval_success(trackers)
precision_ret = benchmark.eval_precision(trackers)
norm_precision_ret = benchmark.eval_norm_precision(trackers)  # LaSOT branch
benchmark.show_result(success_ret, precision_ret, norm_precision_ret)
```

Outputs:

- `Success`: mean success-overlap curve area over thresholds `0.00, 0.05, ..., 1.00`.
- `Precision`: center-location precision at the 20-pixel threshold from thresholds `0, 1, ..., 50`.
- `Norm Precision`: normalized center precision at the 0.20 threshold from thresholds `0.00, 0.01, ..., 0.50`; printed by the LaSOT branch.

Input assumptions:

- Prediction files use `[x, y, width, height]` rows.
- Ground-truth and prediction lengths should match the sequence frame count. Some adapters print mismatches instead of raising immediately; do not ignore these prints when reporting results.
- LaSOT applies its `absent` mask before computing curves.

Result table shape:

```text
| Tracker name | Success | Norm Precision | Precision |
```

For non-LaSOT OPE branches, norm precision is printed as `0.000` because it is not computed.

## AccuracyRobustnessBenchmark

Used for VOT short-term restart-protocol datasets: `VOT2016`, `VOT2017`, `VOT2018`, and `VOT2019`.

Typical evaluation calls:

```python
ar_benchmark = AccuracyRobustnessBenchmark(dataset)
ar_result = ar_benchmark.eval(trackers)
ar_benchmark.show_result(ar_result, eao_result)
```

Outputs:

- `Accuracy`: mean overlap over valid tracked regions.
- `Robustness`: failure count normalized by sequence length and shown as a percentage-like value.
- `Lost Number`: average number of failures.
- When passed an EAO result, `show_result` also prints `EAO` in the same table.

Input assumptions:

- Result rows may include VOT restart markers: `1` for initialization, `2` for failure, and `0` for skipped frames.
- Predictions can be rectangles or polygons.
- Overlaps are computed by `toolkit.utils.region`.

## EAOBenchmark

Used with VOT short-term datasets to compute expected average overlap. It is normally run after AR evaluation and displayed through `AccuracyRobustnessBenchmark.show_result(ar_result, eao_result)`.

Typical evaluation calls:

```python
benchmark = EAOBenchmark(dataset)
eao_result = benchmark.eval(trackers)
```

Dataset-specific sequence-length windows are embedded in the benchmark class:

| Dataset | Low | High | Peak |
| --- | ---: | ---: | ---: |
| VOT2016 | 108 | 371 | 168 |
| VOT2017 | 100 | 356 | 160 |
| VOT2018 | 100 | 356 | 160 |
| VOT2019 | 46 | 291 | 128 |

Outputs:

- A dictionary keyed by tracker name, then by tag. The default tag set is `['all']`.
- The displayed table is sorted by `EAO` for tag `all`.

Input assumptions:

- The VOT dataset sidecar must provide tag arrays for `all`, `camera_motion`, `illum_change`, `motion_change`, `size_change`, `occlusion`, and generated `empty` behavior.
- Missing or malformed restart result files can cause empty trajectory groups or invalid EAO values; validate result layout before running metric code.

## F1Benchmark

Used for `VOT2018-LT` long-term evaluation.

Typical evaluation calls:

```python
benchmark = F1Benchmark(dataset)
f1_result = benchmark.eval(trackers)
benchmark.show_result(f1_result)
```

Outputs:

- `Precision`: overlap-weighted precision at the confidence threshold that maximizes F1.
- `Recall`: recall at the same selected threshold.
- `F1`: maximum F1 value over generated confidence thresholds.

Input assumptions:

- Each video directory contains both trajectory and confidence files:
  - `<video>_001.txt`
  - `<video>_001_confidence.value`
- The confidence file is read from the second line onward, and the evaluator inserts a NaN for frame 1.
- `toolkit.utils.region` is used for overlap calculations.

## Video-level output

The evaluation CLI supports `--show_video_level`.

Practical constraints:

- OPE video-level rows are printed only when both success and precision results contain fewer than 10 trackers.
- AR and F1 video-level tables are likewise designed for small tracker sets.
- Use video-level output for debugging a small run, not for large leaderboards.

## Required region extension

The VOT-family metrics and shared statistics utilities rely on the compiled `toolkit.utils.region` extension. If imports fail, OPE result layout checks may still work, but full VOT/EAO/F1 metric computation will not. See [troubleshooting.md](troubleshooting.md) for the legacy Cython build requirement.
