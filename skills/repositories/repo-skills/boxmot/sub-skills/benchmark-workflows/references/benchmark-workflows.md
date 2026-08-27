# Benchmark Workflows Reference

## Workflow family

BoxMOT uses one cached replay workflow family for four commands:

- `generate`
- `eval`
- `tune`
- `research`

`generate` builds the reusable detections and ReID embeddings. The other commands replay that cache with different tracker settings or objective functions.

## Core idea

The cache key depends on the benchmark, split, detector, ReID, detection source, and replay backend choices. If any of those change, BoxMOT creates a new cache bucket.

```bash
boxmot generate --benchmark mot17 --split ablation
boxmot eval --benchmark mot17 --split ablation --tracker boosttrack
boxmot tune --benchmark mot17 --split ablation --tracker bytetrack
boxmot research --benchmark mot17 --split ablation --tracker bytetrack --proposal-model openai/gpt-5.4
```

## Benchmark ids seen in this repo

- `mot17`
- `sportsmot`
- `mmot`
- `mmot-mini`

## Public detections

Use `--detection-source` when the benchmark ships public challenge detections:

- `public`
- `frcnn`
- `sdp`
- `dpm`

The public detections are cached separately from private detector runs.

## Postprocessing

`eval` supports chained postprocessing via `--postprocessing`:

- `none`
- `gsi`
- `gbrc`
- `gta`

Multiple steps are comma-separated and applied in order.

## Replay backends

`eval`, `tune`, and `research` can run the tracker itself with either:

- `--tracker-backend python`
- `--tracker-backend cpp`

`--tracking-backend` selects the replay executor strategy (`process`, `thread`, or the compatibility alias `cpp`).

## `--tune-kf`

`--tune-kf` estimates Kalman filter noise from the benchmark data before the replay loop starts. It is useful for KF-based trackers and can be reused across tuning trials.

## When to choose each command

- `generate`: create caches only
- `eval`: score a tracker on a benchmark
- `tune`: search tracker hyperparameters
- `research`: let GEPA propose and score tracker code changes

## Validation checks before a long run

1. Confirm the benchmark id exists.
2. Confirm the split name is valid for that benchmark.
3. Confirm the detector and ReID assets are the intended ones.
4. Confirm whether public or private detections should be used.
5. Decide whether the tracker replay should be `python` or `cpp`.
