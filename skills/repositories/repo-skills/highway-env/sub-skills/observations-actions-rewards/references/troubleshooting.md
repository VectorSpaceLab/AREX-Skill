# Troubleshooting observation/action/reward configuration

Use `scripts/inspect_spaces.py` first when a failure might be caused by a config
or a mismatch between expected and actual spaces. It performs one reset and one
sample step, then prints JSON.

## Unknown observation or action type

Symptoms:

- `ValueError: Unknown observation type`
- `ValueError: Unknown action type`

Likely causes and fixes:

- The `type` string is case-sensitive. Use `Kinematics`, not
  `KinematicObservation`; use `OccupancyGrid`, not `OccupancyGridObservation`.
- Action type strings are `DiscreteMetaAction`, `ContinuousAction`,
  `DiscreteAction`, and `MultiAgentAction`.
- Make sure `observation` and `action` are dicts, for example
  `{"action": {"type": "ContinuousAction"}}`, not `{"action": "ContinuousAction"}`.

## Nested config validation errors

Symptoms from `highway_env.utils.update_config`:

- `config.observation invalid: missing_keys=...`
- `config.observation.features_range invalid: missing_keys=...`
- `config.action must be a mapping, got str`

This validator is used when composing default configs in environment classes. If
you override a nested dict that already exists, include all keys from that nested
dict or intentionally build the full replacement. For ordinary runtime use with
`gym.make(..., config=...)`, still prefer complete nested snippets so future
subclass/default-config code can reuse them safely.

## Action shape mismatch

Symptoms:

- `env.action_space.contains(action)` is false.
- A continuous policy emits two values but the env expects shape `(1,)`.
- A discrete policy assumes `3` means `FASTER`, but the configured action set has
  only lateral or only longitudinal actions.

Fixes:

- Inspect `env.action_space` after reset. `ContinuousAction` has shape `(2,)`
  only when both `longitudinal` and `lateral` are true; otherwise shape is `(1,)`.
- Read `env.unwrapped.action_type.actions` and `actions_indexes` after reset for
  `DiscreteMetaAction` labels. Index meanings change when an axis is disabled.
- For `MultiAgentAction`, pass a tuple with one valid nested action per
  controlled vehicle.

## `get_available_actions()` fails or returns surprising values

Symptoms:

- `NotImplementedError` from `env.unwrapped.get_available_actions()`.
- Available actions omit lane changes or speed changes.

Explanation and fixes:

- Availability masks are implemented for `DiscreteMetaAction` and delegated by
  `MultiAgentAction`; they are not implemented for `ContinuousAction` or
  `DiscreteAction`.
- Lane-change labels disappear at road boundaries or where side lanes are not
  reachable. Speed labels disappear at min/max target speed indexes.
- Keep `IDLE` as the safe fallback and build masks from the returned indexes,
  not from a fixed five-action assumption.

## Occupancy grid shape is not what the model expects

Symptoms:

- A CNN expects channels-last data but receives `(channels, width_cells,
  height_cells)`.
- Cell counts differ from hand calculations.
- `NotImplementedError` when using `absolute=True`.

Fixes:

- HighwayEnv occupancy grids are channels-first.
- Cell counts use `floor((max - min) / step)` separately for x and y.
- The config key is `grid_step` (singular).
- Keep `absolute=False`; use `align_to_vehicle_axes=True` if the grid should
  rotate into the ego frame.
- Use `as_image=True` only when the consumer expects `uint8` image-like values.

## Kinematics feature errors or unstable row interpretation

Symptoms:

- Key errors for feature names.
- A policy treats zero rows as real vehicles.
- Rows appear in a different order across resets.

Fixes:

- Use supported vehicle features such as `presence`, `x`, `y`, `vx`, `vy`,
  `heading`, `cos_h`, `sin_h`, `cos_d`, `sin_d`, `long_off`, `lat_off`, and
  `ang_off`.
- Include `presence` whenever padding matters.
- Use `order="sorted"` for deterministic nearest-first ordering; use
  `order="shuffled"` only when the model is intended to be order-robust.
- If `normalize=True`, provide `features_range` for important numeric features
  so scales are explicit and reproducible.

## Lidar config spelling and interpretation

Symptoms:

- A config uses `normalise` and normalization does not behave as expected.
- Distances appear as fractions rather than meters.

Fixes:

- Use `normalize`, not `normalise`.
- With `normalize=True`, both distances and relative speed components are divided
  by `maximum_range`. With `normalize=False`, distances are in meters and clipped
  by the maximum trace range.

## Goal observation or `is_success` confusion in parking

Symptoms:

- Parking observation is a dict, but a policy expects an array.
- `info["rewards"]` is missing in parking.
- `info["is_success"]` is still present after changing the parking observation
  to lidar or grayscale.

Explanation and fixes:

- Default parking observations are goal dicts with `observation`,
  `achieved_goal`, and `desired_goal`.
- Parking computes its scalar reward through `compute_reward(...)` and collision
  penalty, not through an exposed `info["rewards"]` component dict.
- Parking keeps an internal goal observer for reward and success calculations
  even when the agent-facing observation config is not `KinematicsGoal`.
- For non-goal RL algorithms, wrap or flatten the dict observation deliberately;
  route model-selection questions to the training sub-skill.

## `info["rewards"]` is missing or values do not sum to scalar reward

Symptoms:

- `info.get("rewards")` is `None`.
- Summing component values does not equal the scalar `reward`.

Explanation and fixes:

- Some envs do not implement decomposed rewards. Parking reports `is_success`;
  lane keeping returns an empty `info` dict from its custom `step()`.
- Component values are usually unweighted. The scalar reward may multiply by
  config weights, normalize into `[0, 1]`, clip, override on arrival, or multiply
  by `on_road_reward`.
- Inspect both `reward` and `info.get("rewards")`; do not train against component
  values unless the task explicitly requires a multi-objective signal.

## Rendering or video issues from image observations

`GrayscaleObservation` depends on the simulator renderer. If the issue is a
render mode, RGB array capture, video wrapper, headless display, or frame-rate
problem, route to the simulation or training sub-skill. Keep this sub-skill
focused on the observation config and expected `uint8` stack shape.

## Custom roads change observation semantics

If a task needs a new road network, lane geometry, vehicle class, custom reward
method, or environment registration, route to the road/vehicle dynamics
sub-skill. Return here only after the custom env exposes a stable observation and
action config to inspect.
