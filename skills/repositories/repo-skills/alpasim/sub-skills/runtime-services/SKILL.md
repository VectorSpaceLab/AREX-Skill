---
name: runtime-services
description: "Use when diagnosing or adapting AlpaSim's runtime event loop,
  service lifecycle, gRPC address routing, one-shot or daemon execution, replay,
  timing validation, renderer caches, or video-model chunk scheduling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Runtime services

Use this route for runtime-owned behavior: the event-driven rollout loop, the
runtime's gRPC clients and daemon server, service sessions, address pools,
replay, timing validation, and renderer/video-model scheduling. The runtime is
an orchestrator, not the owner of deployment composition, policy/model setup,
protobuf schema design, or metric interpretation.

## Route before acting

- For Hydra composition, Docker/Compose or Slurm deployment, scene acquisition,
  and user-facing run setup, use `simulation-wizard`.
- For driver policy/model inputs, camera rectification, or plugin registration,
  use `drivers-and-plugins`.
- For ASL inspection, scoring, aggregation, videos, and geometry utilities, use
  `evaluation-and-logs`.
- For protobuf definitions or stub generation, use `grpc-and-developer-tools`.
- For controller, physics, or traffic implementation details, use
  `control-physics-traffic`.

Read the focused reference before changing a configuration or interpreting a
failure:

1. [Architecture](references/architecture.md) for event ordering and service
   responsibilities.
2. [Configuration and timing](references/configuration-and-timing.md) for
   fields, cadence equations, validation rules, and cache controls.
3. [Service lifecycle](references/service-lifecycle.md) for one-shot, daemon,
   workers, endpoint probing, shutdown, and request routing.
4. [Replay and video model](references/replay-and-video-model.md) for ASL
   replay boundaries and stateful renderer chunks.
5. [Troubleshooting](references/troubleshooting.md) for symptom-to-check
   recovery paths.

## Common workflow

1. Preserve the resolved user config, network endpoint config, evaluation
   config, and a writable run directory. Do not hand-edit generated service
   addresses while containers are running.
2. Run the bundled [runtime config checker](scripts/inspect_runtime_config.py)
   first when a YAML config is available:
   `python scripts/inspect_runtime_config.py --user-config <user.yaml>`.
   Add `--network-config <network.yaml>` to check endpoint presence. It checks
   structural invariants and timing; it does not contact services.
3. Decide whether the run is one-shot (`--serve` absent) or daemon (`--serve`).
   For deployment generation and backing-service startup, route to
   `simulation-wizard`.
4. Confirm the renderer kind and service skip flags agree with the intended
   run. `sensorsim` is frame-oriented; `video_model` is session/chunk-oriented.
5. For a live run, inspect startup logs in order: config parsing, version
   probes, scene validation, worker startup, session initialization, then event
   handling. The first causal error is more useful than later RPC failures.
6. Treat a rollout as complete only when its output contains `_complete`; an
   ASL file or partial rollout directory alone is not success.

## Runtime entry points

A direct runtime invocation requires `--user-config`, `--network-config`,
`--log-dir`, and `--eval-config`. Optional `--log-level`, `--array-job-dir`,
`--serve`, and `--listen-address` control diagnostics, array aggregation, and
daemon mode. Use `python -m alpasim_runtime.simulate --help` in the installed
runtime environment to confirm the local CLI surface.

One-shot execution creates workers, assigns each job a concrete address for
`driver`, `renderer`, `physics`, `trafficsim`, and `controller`, runs the event
queue, writes ASL/evaluation artifacts, and shuts down managed services. With
`nr_workers=1`, execution is inline and easiest to debug; larger values spawn
workers and improve parallelism but make process failures and logs harder to
localize.

Daemon mode starts a runtime gRPC server. Clients should wait for the advertised
listen address to accept connections, call runtime discovery before submitting
work, submit valid scene IDs and rollout counts, then call shutdown when done.
Per-request driver addresses may override the configured driver pool only when
the request supplies a valid address list and positive per-driver concurrency.
See [service lifecycle](references/service-lifecycle.md).

## Timing and renderer choices

For zero-decision-delay debugging, enable
`runtime.simulation_config.assert_zero_decision_delay`. Align every camera's
`frame_interval_us` with `control_timestep_us`; a zero `pose_reporting_interval_us`
means report at the control cadence. A failure naming a stale camera or
egopose is a configuration/cadence problem before it is a model problem.

For a video-model renderer, use a known chunk preset or reproduce its equations
rather than changing one field in isolation. At the runtime's integer frame
interval `floor(1_000_000 / fps)`, require:

- `control_timestep_us == chunk_frames * frame_interval_us`;
- `force_gt_duration_us >= first_chunk_frames * frame_interval_us + control_timestep_us`;
- the remaining force-GT duration is an integer number of regular chunks.

The first chunk anchors the session after the recorded seed frame. Later chunks
sample ego trajectory and dynamic actors, then return timestamped frames to the
same event queue. Keep recorded calibration, seed images, HD-map conditioning,
and camera selection consistent; the video-model path is currently single-view
in the documented public recipe. GPU containers, checkpoints, USDZ assets, and
networked renderer availability are not replaced by CPU imports or mocked
checks. See [replay and video model](references/replay-and-video-model.md).

## Replay, caches, and failure triage

ASL replay is a deterministic integration/debug facility: recorded exchanges
are paired by service and method, dynamic UUID/seed fields are ignored, and
small floating-point drift is tolerated. It is primarily single-instance and
fixture-bound; it is not a general multi-client production backend.

The runtime has two distinct cache families. The artifact loader uses bounded
LRU semantics (`None` unlimited, `0` disabled). Force-GT frame caching is for
sensorsim deterministic warmup frames and is keyed by scene UUID plus a render
signature. Scene-affine daemon dispatch is a separate optional NRE cache-aware
scheduler and requires renderer cache introspection; disable it when the
renderer does not implement that RPC.

When a rollout fails, classify the evidence before retrying: missing `_complete`
means incomplete output; missing `generated-network-config` or an empty address
list means routing/configuration; `UNAVAILABLE` or version-probe timeout means
service startup/port readiness; a stale cache means cache identity or renderer
state; an ASL mismatch means replay input drift. Follow the concrete matrix in
[troubleshooting](references/troubleshooting.md).

## Safe helper and verification boundaries

Use `scripts/inspect_runtime_config.py` for parser-level and timing checks. It
never downloads data, starts containers, opens sockets, deletes output, or
modifies YAML. Native candidates for later verification are the runtime smoke,
validation, ASL replay, integration replay, service lifecycle, daemon plumbing,
and mocked video-model renderer tests. The full video-model integration remains
optional: it needs a compatible CUDA/container stack, model server, checkpoints,
scene assets, and possibly credentials.
