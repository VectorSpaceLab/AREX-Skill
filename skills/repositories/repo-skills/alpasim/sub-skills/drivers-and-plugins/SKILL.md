---
name: drivers-and-plugins
description: "Select, configure, inspect, and extend AlpaSim ego drivers and
  model plugins while preserving camera, trajectory, asset, and optional-backend
  contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Drivers and plugins

Use this sub-skill when the task is about **which ego policy to run**, the
model-facing driver configuration, model input/output adaptation, camera
rectification, manual/external drivers, or Python plugin discovery. It owns
policy and model contracts; it does not own simulation deployment orchestration,
service event-loop internals, or protobuf schema details.

## Route the request first

- Choose `manual` for interactive keyboard control and a display.
- Choose `vam` through the `vavam` preset for a single-camera, single-image
  VAM policy. Choose `vavam_video_model` only when the renderer returns the
  recorded f-theta view and driver-side rectification is intended.
- Choose `alpamayo1`, `alpamayo1_5`, or `alpamayo2` for their corresponding
  four-camera, temporal VLA presets. Use `alpamayo1_5_1cam` for the documented
  single-view video-model path. Alpamayo policies use route text rather than
  the discrete waypoint command in the 1.5 and 2 presets.
- Choose `alpamayo1_5_recipes_sft` only when the optional recipes package and
  its checkpoint are installed.
- Choose `transfuser` only after installing its separate plugin package and
  supplying its four-camera checkpoint/config pair.

For a complete command, deployment target, topology, scene, cache, or external
renderer setup, continue with [simulation-wizard](../simulation-wizard/SKILL.md).
Read [model overview](references/model-overview.md) for preset/backend tradeoffs
and [manual and external](references/manual-and-external.md) for GUI or endpoint
workflows.
For runtime cadence, service lifecycle, or video chunk scheduling, use
[runtime-services](../runtime-services/SKILL.md). For generated stubs and
protobuf-level API work, use [grpc-and-developer-tools](../grpc-and-developer-tools/SKILL.md).

## Standard driver workflow

1. **Inspect the installed registry before editing YAML.** Run
   `python scripts/check_driver_plugins.py` from this skill, or the installed
   [driver/plugin checker](scripts/check_driver_plugins.py), or the installed
   `alpasim-info` command. Confirm the requested `model_type` is present; a
   config name alone does not install a model.
2. **Select a matching driver config group.** Start from a built-in policy
   preset (`driver=vavam`, `driver=alpamayo1`, `driver=alpamayo1_5`,
   `driver=alpamayo2`, `driver=manual`) or an installed plugin preset. Keep
   the model's camera count, frame cadence, context length, and output rate
   aligned with the renderer and runtime.
3. **Set assets and device deliberately.** Use a local checkpoint directory or
   a documented Hugging Face model ID. Authenticate and pre-cache gated assets
   outside the driver process; never put tokens in YAML. `device: cuda` is a
   request, not proof of GPU inference: the service falls back to a CPU Torch
   device when CUDA is unavailable, which is useful for the manual model but is
   not a CPU substitute for heavyweight VAM/Alpamayo/Transfuser inference.
4. **Validate camera contracts.** The session rejects requested logical IDs
   absent from the rollout specification. A model also rejects the wrong set
   of camera IDs, frame count, or unsupported frame dimensions. Preserve the
   documented camera order; do not add `+cameras=...` to a video-model preset
   unless the renderer seed/calibration is changed consistently.
5. **Validate policy output before a run.** Models return candidate poses in
   rig coordinates (`x` forward, `y` left, `z` up); the driver converts the
   selected candidate to the simulator trajectory. Check output frequency,
   route semantics, and any candidate-selection settings before enabling
   optimization or sampling.
6. **Run a bounded import/config smoke check.** Load the registry and the
   Hydra config without instantiating a model when assets or optional backends
   are unavailable. Treat model-load, VRAM, gated-download, and renderer
   failures as distinct from YAML or plugin registration failures.

## Configuration guardrails

- `model.model_type` is the `alpasim.models` entry-point name. Required model
  fields are `checkpoint_path` and `device`; VAM additionally requires
  `tokenizer_path`. `image_decode_device: cuda` cannot be combined with
  rectification because rectification operates on host images.
- `inference.use_cameras` is an ordered logical-ID list. `context_length` is
  the temporal frame count per camera; `subsample_factor` selects older frames
  from the frame cache; `max_batch_size` is an inference-worker bound, not a
  guarantee that the model fits in VRAM. `output_frequency_hz` must match the
  model's action spacing when the implementation does not resample.
- `route.use_waypoint_commands` controls discrete turn-command derivation for
  command-based policies. The driver chooses the first route waypoint at least
  `min_lookahead_distance` ahead; positive rig-frame lateral displacement over
  `command_distance_threshold` means LEFT, negative means RIGHT, otherwise
  STRAIGHT. Alpamayo 1.5 and 2 presets intentionally disable this path.
- `rectification` is an explicit per-camera f-theta-to-pinhole compatibility
  map. Use it for video-model output consumed by a pinhole-trained policy, not
  for a renderer that already emits pinhole images.
- `trajectory_selection` only has an effect when more than one Alpamayo
  candidate is sampled. `ALWAYS_FIRST` needs no previous plan; `CLOSEST_3D` and
  `CLOSEST_LATERAL` require at least two samples and use the previous selected
  plan for continuity.

## Safe plugin extension

A plugin is an installed Python distribution that registers entry points. A
model implements `BaseTrajectoryModel`, including `from_config`, `predict`,
`camera_ids`, `context_length`, and `output_frequency_hz`, then registers its
factory/class under `alpasim.models`. A Hydra config package is a separate
`alpasim.configs` entry point. Install both the model package and config
package before expecting `model_type` or `driver=<name>` to resolve.

Use the [plugin contract](references/plugin-contract.md) for the exact
Transfuser pattern and the [driver API](references/driver-api.md) for the
input/output shape contract. Do not copy weights, upstream repositories,
credentialed downloaders, or scheduler launchers into this skill.

## Failure recovery

Start with [troubleshooting](references/troubleshooting.md). First classify the
failure as registry/import, config/camera contract, asset/auth, backend/VRAM,
or deployment/runtime ownership. Fix only the owning layer, then rerun the
smallest smoke check. Keep CUDA, containers, FlashDreams, gated Hugging Face
assets, and model inference explicitly optional unless their prerequisites are
present and verified.
