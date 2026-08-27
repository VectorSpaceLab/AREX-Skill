# Benchmark Troubleshooting

## `eval` or `tune` says `--benchmark` is required

These commands are benchmark-driven. Pass a valid benchmark name or YAML path.

```bash
boxmot eval --benchmark mot17 --split ablation --tracker boosttrack
```

## Cache keeps regenerating

The cache key changes when any of these change:

- benchmark
- split
- detector
- ReID
- detection source
- replay backend

If you want cache reuse, keep all of those fixed.

## Public detections are missing

If the benchmark uses public detections, check the `--detection-source` value and make sure the benchmark config actually defines the requested detection variant.

## `--tracker-backend cpp` fails for a tracker

Only the supported native trackers have a C++ replay path. If the chosen tracker is not supported, fall back to the Python backend or switch trackers.

## Postprocessing confusion

`--postprocessing` applies in order. If a later step looks wrong, remember it is reading the output of the earlier step, not the original tracker results.

## OBB benchmark mismatch

If the benchmark uses OBB but the detector or tracker is running AABB, fix the tensor layout first. The benchmark's `box_type` must match the runtime geometry.
