# Troubleshooting simulation environments

Use this page as the first diagnostic pass. Keep the original exception and
record the SMARTS version, Python version, scenario identifier, interface
preset, formatting options, seed, and whether the failure occurred at import,
reset, step, or close.

## Install and import

**`ModuleNotFoundError: smarts` or imports resolve to an unexpected copy**

- Run `python -m pip show smarts` and `python -c 'import smarts; print(smarts.__file__)'`
  in the same interpreter that runs the policy.
- Install the package into that interpreter with the project's supported
  package workflow; do not mix a system `pip` with a virtual-environment
  `python`.
- Core CPU operation needs the base package, Gymnasium for this route, and the
  selected scenario/map dependencies. The verified inspection environment used
  SMARTS 2.0.1 on Python 3.11 and passed `pip check`.
- Import `smarts.env.gymnasium` before `gym.make("smarts.env:hiway-v1", ...)`.
  Direct `HiWayEnvV1(...)` is useful when debugging registration.

**Gymnasium import fails or the registered id is absent**

- Check `python -c 'import gymnasium; import smarts.env.gymnasium; print("ok")'`.
- Use `from smarts.env.gymnasium.hiway_env_v1 import HiWayEnvV1` to distinguish
  registration from simulator import failure.
- Do not assume a legacy Gym API: this route expects the five-value
  Gymnasium `step` return and two-value `reset` return.

## Optional dependencies and rendering

**Image/grid sensor raises a renderer, Panda3D, display, or shader error**

- A successful `import smarts` proves only package import, not camera behavior.
- Install the optional camera-observation variant supported by the deployment
  and verify Panda3D/offscreen rendering separately.
- Confirm `AgentInterface.requires_rendering` and disable
  `top_down_rgb`, `occupancy_grid_map`, `drivable_area_grid_map`, occlusion, or
  custom renders for a low-dimensional CPU run.
- Image generation can significantly slow every step. Do not use image fields
  merely to make an observation dict look complete.
- Envision/record/replay is a separate route and may require a server or
  compatible display; `headless=True` avoids starting the default client for
  this skill's smoke.

**Ray/RLlib, Torch, SUMO, ROS, Waymo, Argoverse, or Visdom is missing**

- These are optional integrations, not a failure of `HiWayEnvV1` core CPU
  behavior. Do not install them as a repair for an action-space or scenario
  problem.
- Use the `rl-agent-zoo` route for RLlib/registry packaging and the
  `cli-integrations` route for SUMO/system services. Record the missing optional
  capability explicitly.

## Scenario, data, and configuration

**Reset cannot load a scenario, map, traffic file, or generated artifact**

- The `--scenario` passed to `smoke_env.py` must be an existing generated
  scenario directory, not a source definition or a parent directory that has
  not been built.
- Check directory readability and the generated map/traffic files using the
  scenario tooling. Do not make this route silently build or mutate scenario
  data.
- Ask `scenario-studio` to define/build the scenario and verify its map,
  traffic, missions, and generated outputs.
- A scenario list can expand to multiple concrete variations; log the active
  `scenario_log` after reset when comparing runs.

**No active agents after reset**

- This can be valid when missions are scheduled at different times. Step with
  `{}` while `__all__` is false; do not index a missing observation.
- If it stays empty until the outer bound, inspect mission scheduling, scenario
  generation, and done criteria rather than adding dummy actions.
- In `full` observation mode inspect `obs[id]["active"]`; padded data is not a
  live agent observation.

**Dataclass/configuration errors**

- Pass `AgentInterface` objects in `agent_interfaces`, or pass dictionaries
  only where the constructor explicitly accepts mappings that it will convert.
- `EnvironmentConfiguration` requires `id`; `HiWayEnvV1Configuration` requires
  `scenarios` and `agent_interfaces`. Do not omit required fields when using a
  typed config.
- Use enum members or their documented string names for
  `scenarios_order`, `observation_options`, `action_options`, and
  `environment_return_mode`. Keep `fixed_timestep_sec` positive.
- `occlusion_map` requires an occupancy grid of matching dimensions.

## API and CLI misuse

**`AssertionError` from `ActionSpacesFormatter`**

- Print `env.action_space`, `type(action)`, and `space.contains(action)` before
  stepping. Verify the agent id is present in the current active observation.
- `Lane` in formatted mode expects integer `0..3`; raw/unformatted mode expects
  lane strings such as `"keep_lane"`.
- Continuous and actuator-dynamic actions need three values with throttle and
  brake in `[0, 1]`, steering/rate in `[-1, 1]`.
- Lane-with-speed needs a two-value tuple; target pose, trajectory, and direct
  actions have distinct lengths and nested sequence requirements.
- Do not use `action_space.sample()` from one interface for a different agent.
  Spaces can differ by agent in a mixed-interface environment.
- `action_options="full"` requires every configured agent id even when it is
  inactive; use `multi_agent` for active-only policy loops.

**A policy gets a dict but expects a named tuple, or vice versa**

- `ObservationOptions.unformatted` returns raw SMARTS `Observation` objects.
- `multi_agent`/`full` return formatted nested structures matching their
  corresponding spaces. Inspect `env.observation_space` and adapt once at the
  policy boundary; do not guess based on field names.

**A caller unpacks the wrong number of step values**

- HiWayEnvV1 always returns five values from `step`: observation, reward,
  terminated, truncated, info.
- Per-agent mode uses dictionaries and includes `"__all__"` in done maps.
- Environment mode uses a summed float and scalar booleans.
- RLlib's environment has a different API and belongs to the RL route; do not
  apply its four-value/done conventions to this Gymnasium environment.

Public command spelling, scenario build/clean, diagnostics, and external
services belong to `cli-integrations`; this route's scripts are Python API
checks only.

## Controller and vehicle failures

**Lane controller says no waypoint or vehicle is out of lane**

- Ensure the interface enables `waypoint_paths` and the mission/vehicle starts
  near a valid lane.
- Confirm the selected action is a lane action and that the vehicle chassis
  supports the lane-following controller. Do not mask the exception by
  switching action types without changing the policy contract.

**Vehicle does not move or terminates immediately**

- Check throttle/brake signs and ranges, target speed units (m/s), timestep,
  mission route, and `DoneCriteria` event flags.
- Inspect `infos[id]` and the formatted `events` fields for collision,
  off-route, off-road, wrong-way, not-moving, goal, or max-step causes.
- A `Buddha`/`Empty` interface intentionally issues no movement action.

## Parallel and cleanup failures

**`ParallelEnv` rejects constructors or spaces**

- Every constructor must be callable, picklable, and accept `seed=`. Use a
  module-level function or `functools.partial`, not an already-created env.
- All workers must use equal agent ids, interfaces, action formatting, and
  observation formatting so their Gymnasium spaces compare equal.
- Keep worker count modest; process overhead can exceed simulation throughput.

**Worker hangs, raises a remote exception, or leaves processes behind**

- Reduce to one child and run the same constructor directly.
- Make the scenario and policy importable in a fresh worker process; avoid
  closures over unpicklable state.
- Put `workers.close()` in `finally`. Use `close(terminate=True)` only to
  recover an unresponsive worker, then fix the underlying exception.
- With `auto_reset=False`, reset completed workers before sending another
  episode's actions. With `auto_reset=True`, account for the worker's new
  observation after a terminal step.

**Close fails after a policy exception**

- Preserve the original exception, call `env.close()` in `finally`, and check
  for leaked visualization/worker processes separately. Avoid calling
  `step()` after `__all__` has become true.
