---
name: evaluation-and-logs
description: "Inspect AlpaSim ASL rollouts, extract camera streams, evaluate and
  aggregate metrics, re-evaluate completed runs, render diagnostic videos, and
  analyze trajectories, maps, and geometry without producing new simulations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation and logs

Use this sub-skill when the task starts with an existing AlpaSim run, `.asl` log,
rollout directory, metrics parquet, evaluation configuration, trajectory, map,
or diagnostic video. It is for reading, scoring, aggregating, and explaining
outputs—not for starting the simulator or fixing controller, physics, traffic,
renderer, or deployment services.

## Route first

- **Runtime production, replay service orchestration, daemon health, or timing
  failures:** route to `runtime-services`.
- **Wizard setup, scene/model acquisition, Docker/Slurm deployment, or run
  creation:** route to `simulation-wizard`.
- **Driver policy/model implementation:** route to `drivers-and-plugins`.
- **Controller, physics, or traffic implementation:** route to
  `control-physics-traffic`.
- **Proto compilation, generated stubs, or contributor tooling:** route to
  `grpc-and-developer-tools`.

Keep this sub-skill for the evidence and post-run analysis boundary.

## Choose the smallest workflow

1. Identify the run root and whether it is a single job or an array-job parent.
   A single job has `eval-config.yaml` at its root; an array parent has child
   job directories containing that file. Confirm `wizard-config.yaml` is
   present before using automatic re-evaluation.
2. Locate complete rollouts under `rollouts/<scene-or-clip-id>/<rollout-id>/`.
   Treat a rollout as complete only when its `_complete` marker exists. Expect
   `rollout.asl`, optional `metrics.parquet`, and optional `.mp4` files there.
3. For a quick log diagnosis, read the [ASL format reference](references/asl-format.md)
   and use the bundled `scripts/print_asl.py`. Start with `--just-types`, a
   narrow `--start/--end` range, and selected
   `--message-types`; payloads containing images or video-model bytes are
   redacted before printing. Use `--strict` when truncation must fail loudly.
4. For camera inspection, use `scripts/asl_to_frames.py` with a quoted recursive
   glob. Choose `--format frames` for bounded file inspection or `--format mp4`
   when ffmpeg/imageio is available. Keep `--max-files` and
   `--max-concurrency` bounded for large run trees.
5. For post-evaluation, run the documented module form in
   [evaluation workflows](references/evaluation-workflows.md). Read
   [geometry and utilities](references/geometry-and-utilities.md) before
   comparing trajectories or maps. Evaluation
   requires the resolved YAML, complete ASLs, and a matching USDZ glob when
   map-backed metrics or videos are enabled. It writes per-rollout parquet
   beside each ASL.
6. Aggregate only after all intended jobs have metrics. The aggregation step
   discovers `rollouts/**/metrics.parquet`, writes the aggregate tree, and may
   create relative video links. For a prior run, prefer `python -m eval.reeval`
   or the equivalent installed re-evaluation command; never submit scheduler
   work from this sub-skill without an explicit user request.

## Read the data correctly

- ASL is a big-endian, four-byte size-delimited protobuf stream of `LogEntry`
  messages. The first meaningful message should be `rollout_metadata`; actor
  poses are timestamped and include `EGO`. Requests/returns, camera images,
  routes, and traffic predictions are additional evidence.
- Use timestamps (`timestamp_us`) rather than list positions when correlating
  poses, plans, camera frames, and metrics. `async_read_pb_log()` is tolerant
  by default: a short final frame logs a warning and stops. Set
  `raise_on_malformed=True` for diagnosis or validation.
- Evaluation loads ASL through `load_scenario_eval_input_from_asl()`, then
  `ScenarioEvaluator(EvalConfig).evaluate(...)` returns per-timestep
  `MetricReturn` values, aggregated values, and a Polars metrics dataframe.
  Missing rollout metadata, actor definitions, ground truth, or required
  response/camera data can make a metric unavailable or the input invalid.
- Map-dependent offroad and video analysis need a discoverable USDZ artifact
  and compatible map data. Without a vector map, aggregation supplies an
  `offroad=0.0` fallback and records a warning; do not interpret that as proof
  that offroad was measured.

## Interpret outputs

Use [metrics and videos](references/metrics-and-videos.md) for the complete
metric and output contract. In short: per-rollout metrics live next to the ASL;
`aggregate/metrics_results.txt`, `metrics_results.parquet`,
`metrics_unprocessed.parquet`, `results-summary.json`, and
`metrics_results.png` summarize a run. Videos are named from clip, rollout,
camera, and layout identifiers and are organized under `aggregate/videos/`.
Inspect the raw parquet and the modifiers recorded in the text summary before
comparing runs.

## Programmatic analysis

- Use `alpasim_utils.logs.read_trajectory()` for a scene name plus the EGO
  trajectory extracted from actor-pose messages. It returns `None` when there
  are no usable actor poses or no metadata scene id.
- Use `alpasim_utils.geometry` for gRPC conversion, `Pose`, `Polyline`, and
  timestamped `Trajectory`. Internally, quaternion arrays are `(x, y, z, w)`;
  gRPC fields are addressed as `(w, x, y, z)`. Preserve the rig-to-AABB-center
  transform from rollout metadata before comparing map or vehicle geometry.
- Use `Trajectory.interpolate_pose()` only inside its time range (a one-pose
  trajectory accepts its exact timestamp); sort or validate timestamps before
  constructing trajectories. Use Shapely objects for 2-D intersections and
  distances, and state when z is intentionally ignored.
- Treat the Rust-backed `utils_rs` types as an optional native boundary: verify
  that the extension and generated protobufs import before relying on geometry
  helpers. The Python evaluation path is not a substitute for a missing map,
  renderer, ffmpeg, or model asset.

## Safe checks and failure recovery

Run `python -m ... --help`, import checks, and bounded fixture checks before a
large evaluation. Do not run the original checkout's setup, asset download,
Docker build, Slurm submission, or credentialed model acquisition from here.
Use [troubleshooting](references/troubleshooting.md) for install/import,
optional backend, data/config, CLI/API, and workflow failures. When evidence
is incomplete, report the exact missing message, asset, marker, config field,
or backend rather than filling in a metric or claiming a successful run.

## Bundled helpers

- `scripts/print_asl.py`: bounded, redacted protobuf inspection; safe and
  read-only.
- `scripts/asl_to_frames.py`: bounded extraction to images or MP4; writes only
  under the requested output directory and never downloads data.
- `scripts/check_run_metadata.py`: read-only single/array-job layout and ASL
  metadata checker; it does not load USDZ maps or rewrite configs.

The package's `print-asl` and `asl-to-frames` console launchers currently
request a `main` symbol that the installed modules do not define. Use
`python -m alpasim_utils.print_asl` and `python -m alpasim_utils.asl_to_frames`
(or these bundled helpers) until packaging is corrected. The evaluation,
aggregation, and re-evaluation module entry points expose `main` and their
`python -m` forms are the portable fallback.
