# DiffusionPlanner API and configuration reference

## Import surface

The planner adapter is importable as:

```python
from diffusion_planner.planner.planner import DiffusionPlanner
from diffusion_planner.utils.config import Config
from nuplan.planning.simulation.trajectory.trajectory_sampling import TrajectorySampling
```

The inspected environment uses Python 3.9, `nuplan-devkit==1.2.2`, and the
repository package. These imports are an API/parser check only; they do not
open a dataset or instantiate a full simulation.

## Constructor

The public constructor is:

```text
DiffusionPlanner(
    config: diffusion_planner.utils.config.Config,
    ckpt_path: str,
    past_trajectory_sampling: TrajectorySampling,
    future_trajectory_sampling: TrajectorySampling,
    enable_ema: bool = True,
    device: str = "cpu",
)
```

Behavior that matters operationally:

- `device` must be exactly `cpu` or `cuda`. The CUDA branch asserts that
  `torch.cuda.is_available()`.
- The constructor stores both sampling objects, computes the future horizon,
  computes `future_trajectory_sampling.time_horizon /
  future_trajectory_sampling.num_poses` as the output step interval, creates
  `Diffusion_Planner(config)`, creates `DataProcessor(config)`, and keeps the
  configured observation normalizer.
- `ckpt_path` may be `None`; that path makes the implementation print that it
  is loading a random model. A real evaluation should use the trained file.
- `past_trajectory_sampling` is stored for the data adapter/history contract;
  it must describe the history expected by the model/checkpoint.

The repository YAML defaults are:

| Object | `num_poses` | `time_horizon` | Meaning |
|---|---:|---:|---|
| past sampling | 20 | 2 s | history window supplied to the adapter |
| future sampling | 80 | 8 s | predicted trajectory horizon; 0.1 s interval |

Use the `TrajectorySampling` signature supported by the installed nuPlan
version. Do not silently change only one of pose count, horizon, or checkpoint
model horizon.

## Lifecycle and methods

`DiffusionPlanner` implements nuPlan's `AbstractPlanner` contract:

1. **Construction** creates the model and data processor but does not load the
   checkpoint.
2. **`name()`** returns `diffusion_planner`.
3. **`observation_type()`** returns `DetectionsTracks`; the simulation must
   provide the compatible observation type.
4. **`initialize(initialization)`** stores the map API and route roadblock IDs,
   then loads the checkpoint with `torch.load(..., map_location=device)`.
   With `enable_ema=true`, it selects `state_dict['ema_state_dict']`. With
   EMA disabled, a checkpoint wrapper with a `model` key is unwrapped. Keys
   beginning with `module.` are stripped before loading. The model is then
   put in evaluation mode and moved to the selected device.
5. **`planner_input_to_model_inputs(planner_input)`** takes the nuPlan history,
   traffic-light data, map API, route roadblocks, and device and delegates to
   `DataProcessor.observation_adapter`.
6. **`compute_planner_trajectory(current_input)`** adapts and normalizes inputs,
   calls the model, converts the output to states, and returns an
   `InterpolatedTrajectory`. NuPlan's inherited `compute_trajectory` is the
   normal simulation entrypoint around this method.
7. **`outputs_to_trajectory(outputs, ego_state_history)`** reads
   `outputs['prediction'][0, 0]`, interprets the final two prediction channels
   as heading-vector components via `atan2`, and transforms x/y/heading into
   future ego states using the configured horizon and step interval.

The model's documented inference output is prediction-shaped
`[B, P, future_steps, 4]`; the adapter consumes the first batch and first
planner candidate. This is why a multi-candidate or differently shaped custom
checkpoint must not be assumed compatible.

## `Config(args_file, guidance_fn)` contract

`Config` opens the JSON file immediately, assigns each top-level JSON field as
an attribute, converts `state_normalizer` into a `StateNormalizer`, converts
each `observation_normalizer` entry into tensor-backed mean/std values, and
stores `guidance_fn`.

The checked model code reads at least these architecture/runtime fields from
the resulting object:

```text
agent_num, decoder_depth, decoder_drop_path_rate, device,
diffusion_model_type, encoder_depth, encoder_drop_path_rate, future_len,
hidden_dim, lane_len, lane_num, num_heads, predicted_neighbor_num,
route_len, route_num, static_objects_num, static_objects_state_dim, time_len,
state_normalizer, observation_normalizer, guidance_fn
```

The exact values belong to the checkpoint release. Do not hand-author a
partial `args.json` for a real run. Validate that it is JSON, contains the
normalizer objects and architecture fields, and came from the same release as
`model.pth`.

## Checkpoint forms

The planner's loader accepts these practical forms:

- EMA-enabled run: a mapping containing `ema_state_dict` whose keys match the
  model after removing an optional `module.` prefix.
- Non-EMA run: a mapping containing `model`, or a direct state-dict mapping,
  with keys matching the model after the same prefix cleanup.

A file that merely exists or has a `.pth` suffix is not proof of compatibility.
A wrong release commonly fails at `initialize()` with a missing/unexpected key,
missing `ema_state_dict`, or an architecture/horizon mismatch. Keep
`args.json`, the checkpoint, and the intended YAML overrides together in the
experiment record.

## Guidance boundary

The standard YAML sets `config.guidance_fn: null`. The guidance YAML constructs
`GuidanceWrapper` instead. Guidance behavior is not authored or expanded in
this sub-skill; when a guided planner is selected, confirm that the checkpoint,
CUDA/autograd path, and guidance config are available before simulation.
