# Driver API and configuration contract

The driver is a gRPC policy adapter, but this reference intentionally stops at
the model-facing API. Use grpc-and-developer-tools for protobuf messages and
runtime-services for service lifecycle.

## Model interface

Every model registered in `alpasim.models` is expected to implement
`BaseTrajectoryModel`:

```python
from_config(model_cfg, device, camera_ids, context_length, output_frequency_hz)
predict(prediction_input) -> ModelPrediction
camera_ids -> list[str]
context_length -> int
output_frequency_hz -> int
```

`predict_batch(list[PredictionInput])` has a sequential default. GPU-aware
models may override it to stack inputs and perform one forward pass. The driver
factory calls `from_config`; it does not branch on model class names.

`PredictionInput` contains:

- `camera_images`: `dict[str, list[CameraFrame]]`; each `CameraFrame` has an
  integer `timestamp_us` and an HWC uint8 NumPy array or Torch tensor.
- `command`: the canonical `DriveCommand` enum: `LEFT=0`, `STRAIGHT=1`,
  `RIGHT=2`, `UNKNOWN=3`.
- `speed` in m/s and longitudinal `acceleration` in m/s².
- `ego_pose_history`, `inference_seed`, the previous selected local-frame
  plan, and the latest route when available.

Models must validate the exact camera key set and their required frame count.
The driver supplies every declared field, but a model should read only the
fields it needs. A model-specific command encoding is implemented in
`_encode_command`; do not assume the canonical integer matches VAM or a plugin.

`ModelPrediction` contains candidate positions shaped `(K, T, 3)` and candidate
rotations shaped `(K, T, 3, 3)`, all in the rig frame. `selected_index` selects
the driven candidate. `from_planar(trajectory_xy, headings)` is the safe
constructor for ground-plane adapters; it produces z=0 poses and z-axis
rotations. Optional reference metadata (`model_t0_us`,
`pose_local_to_rig_t0`, and `waypoint_timestamps_us`) must be supplied as a
complete set or omitted as a complete set. Partial metadata is an error.

The coordinate convention is x forward, y left, z up. If an upstream model
uses y-right coordinates, invert y positions and headings before constructing
`ModelPrediction`; the Transfuser adapter is the concrete example.

## Driver schema

The structured configuration has these main groups:

```yaml
model:
  model_type: <alpasim.models entry-point name>
  checkpoint_path: <local path or supported model id>
  device: cuda                 # or cpu
  tokenizer_path: null         # required by VAM
  image_decode_device: cpu    # cpu or cuda
  num_trajectory_samples: 1
  trajectory_selection:
    strategy: ALWAYS_FIRST
inference:
  use_cameras: [<logical IDs in order>]
  max_batch_size: 1
  subsample_factor: 1
  context_length: null
  output_frequency_hz: 10
route:
  use_waypoint_commands: true
  command_distance_threshold: 2.0
  min_lookahead_distance: 5.0
rectification: null
trajectory_optimizer:
  enabled: false
```

The server also needs `host`, `port`, and `output_dir`; presets fill these from
the deployment configuration. `plot_debug_images` writes model-input images to
that output directory and should be enabled only for a deliberate bounded run.
The inference worker batches concurrent sessions up to `max_batch_size`, so
raising it can increase VRAM pressure and is not a correctness fix.

## Session and route preconditions

At session creation, every requested camera must exist in the rollout vehicle
spec. A missing logical ID, an empty `use_cameras`, or rectification for a
camera not used by inference is rejected. A drive request returns an empty
trajectory until all camera caches have enough frames and ego-motion has been
submitted. Dynamic state is required for speed/acceleration extraction.

Route waypoints are interpreted in the true rig frame. The command helper finds
the first waypoint at or beyond `min_lookahead_distance`. Positive lateral y
beyond the threshold is LEFT; negative y is RIGHT; an in-threshold waypoint is
STRAIGHT; no waypoint is UNKNOWN. If no waypoint reaches the lookahead distance,
the helper returns STRAIGHT. This command is advisory and is ignored by manual
and language-conditioned Alpamayo presets.

## Frequency and temporal alignment

VAM and Transfuser adapters report 2 Hz. Alpamayo 1/1.5/2 adapters report a
fixed 10 Hz and reject a different `output_frequency_hz` rather than silently
resampling. The configured camera interval, `context_length`, and
`subsample_factor` must provide the expected temporal history. Alpamayo also
validates a 16-step, 0.1-second ego-pose history and the action checkpoint's
waypoint spacing. An error about history span or action `dt` is a contract
mismatch, not a missing renderer retry.

For video-model output, preserve recorded calibration and use the model preset
that declares rectification. The rectifier accepts only cameras with FTheta
intrinsics and can crop a one-pixel source-size mismatch; larger unexpected
resolution differences are rejected. Rectification is host-side, so it cannot
be combined with CUDA JPEG decode.
