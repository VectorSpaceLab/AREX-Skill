# Configuration, groups, capacity, and timing

## Layering

`base_config.yaml` registers the schema and composes required groups in this
order: `deploy`, `driver`, optional `driver_source`, `topology`, default
`trafficsim=disabled`, default controller, and optional plugin catalogs. The
resolved configuration is saved as `wizard-config.yaml` and a loadable form as
`wizard-config-loadable.yaml`. Runtime, driver, controller, traffic, evaluation,
and network YAML files are generated separately in the run directory.

The deployment group selects paths and filesystem roots. The topology group
sets GPU lists, replicas, runtime worker count, and endpoint concurrency. The
driver group supplies both the policy service config and the runtime camera/input
requirements. Do not change only one side of a driver/camera contract; route
model schema questions to `drivers-and-plugins`.

## Scene selectors

Exactly one logical selector should be active:

- `scenes.scene_ids=[...]` selects IDs and resolves the newest artifact per ID
  when catalogs contain multiple NRE versions; a warning is emitted.
- `scenes.test_suite_id=public_2601` selects catalog-pinned `(scene_id, uuid)`
  rows. `public_2601_video_model` is a 729-scene compatible subset;
  `public_2604` is the broad 26.04 catalog; `public_2507` is historical.
- `scenes.local_usdz_dir=/path` scans recursive `*.usdz` files and reads
  `metadata.yaml`. It builds a RAM-only `local` suite and does not write a
  scene database into the read-only input directory.

The wizard clears its default singleton `scene_ids` when a suite override is
provided. When selecting explicitly, set the unwanted selector to `null` if a
custom loadable config retains both. Positive `scenes.limit_to_first_n` is
applied after deterministic scene sorting.

## Capacity math

For a service with `G` GPUs, `R` replicas per container, and `C` concurrent
rollouts per replica:

```text
capacity = G × R × C
```

With no GPU list, the service is one container; with a GPU list, one container
is made per listed GPU and it gets `R` instances. NRE may instead run one
process per container with internal `--max-workers`; then renderer effective
capacity is approximately:

```text
renderer capacity = G × max_workers × renderer.n_concurrent_rollouts
```

Balance renderer, driver, physics, traffic, and controller capacities. The
`1gpu` topology is a development starting point. `2gpu` has 12 concurrent
rollouts distributed across renderer, driver, physics, traffic, and CPU
controller. `8gpu_64rollouts` targets 64 with four renderer GPUs, four driver/
physics GPUs, one renderer per GPU, eight driver replicas per GPU, four physics
replicas per GPU, one CATK replica per GPU, and 8 runtime workers. CATK loads a
full model per replica, so increasing replicas can exhaust memory.

Set `defines.nre_cache_size` at least as large as the renderer's concurrent
scene demand (the shipped minimal topology uses concurrent rollouts + 1).
`defines.physics_cache_size` should cover concurrent scenes to avoid cache
thrashing. For video-model runs begin with renderer concurrency 1.

## Timing and zero-delay validation

All times are integer microseconds. Let camera interval be `f`, control interval
be `c`, pose interval be `p`, and optional planner delay be `d`:

- a camera/control schedule is aligned only when relevant camera completion
  timestamps land on the decision timestamp;
- for a simple equal-rate setup, `c=f` (e.g. 200,000 us = 5 Hz);
- for a high-rate camera, choose `c=N×f` exactly and set the driver input
  subsampling to `N` when that policy expects fewer frames (e.g.
  `f=33,334`, `c=100,002`, `N=3`);
- `pose_reporting_interval_us=0` means the controller reports at the control
  rate; otherwise it must also align with decisions;
- `assert_zero_decision_delay=true` checks that camera and pose data finish
  exactly at `now_us` before the driver call. It does not repair a mismatch.

Use:

```bash
runtime.simulation_config.control_timestep_us=200000
runtime.simulation_config.cameras.0.frame_interval_us=200000
runtime.simulation_config.assert_zero_decision_delay=true
```

For a synthetic zero-delay failure, if `f=100000` and `c=150000`, the least
common alignment is 300000 us but the first decision at 150000 us has no
completed camera frame at that boundary. Keep the assertion on, inspect the
error's last-started/decision timestamps, then choose a common multiple or
change the policy's subsampling. Setting the assertion false is a diagnostic
escape hatch, not a correctness fix; route runtime scheduling details to
`runtime-services`.

## Video-model timing

OmniDreams is stateful and returns chunks, not isolated frames. The shipped
`+chunking=8frame` preset sets `first_chunk_frames=5`, `chunk_frames=8`,
`control_timestep_us=266664`, and `force_gt_duration_us=2033313` for a 30 FPS
server. This follows `8 × 33,333 us` regular chunks and the server's temporal
compression constraint for the first chunk. Use
`driver=vavam_video_model` or `driver=alpamayo1_5_1cam` with a single-view
preset. Alpamayo's 30 FPS renderer stream is subsampled by 3 for its 10 Hz,
four-frame driver history. Avoid camera overrides that invalidate recorded
FTheta calibration.
