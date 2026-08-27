# Extension and control troubleshooting

## Import and registration failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No method found for category ...` | The `(kinematics, name)` pair is absent from `behaviors_map`, or the custom module was never imported. | Import the module on `sys.path`, call `env.load_behavior("module_name")` before stepping, and inspect the exact kinematics/name spelling. |
| `ModuleNotFoundError` from `load_behavior` | The loader accepts an importable module name, not a filesystem path. | Put the module's directory on `PYTHONPATH`/`sys.path`, use its import name, and reproduce with `python -c "import module_name"`. |
| `ValueError` saying a method/class is already registered | A built-in or earlier import already owns the exact key. | Pick a new key or run the smoke in a fresh process. Do not overwrite the registry by mutating private maps in production code. |
| `unexpected keyword argument 'external_objects'` | A function uses the outdated `objects` parameter without `**kwargs`. | Rename the parameter to `external_objects` or accept `**kwargs`; the dispatcher passes that exact keyword. |
| Class handler initialization logs an error, then lookup fails | The class initializer did not accept configured behavior keywords or returned no callable. | Make the initializer accept `(object_info, **kwargs)` and return a callable with the per-step signature. |
| Group output has wrong length | A group function returned one action for the whole group or changed member order. | Return one action per current member, aligned to `members`, and handle membership changes in stateful handlers. |

Register keys with the kinematics used by the object. `rvo` on `acker`, for
example, is not repaired by registering a behavior named `rvo` for `diff`.
Use [navigation and planning](../../navigation-and-planning/SKILL.md) for the
built-in compatibility matrix and use [scene configuration](../../scene-configuration/SKILL.md)
for action/state dimensions.

## Kinematics extensions

- `register_kinematics(name)` lowercases the key and rejects a different class
  under an existing key. A custom class passed through
  `KinematicsFactory.create_kinematics()` must accept `(name, noise, alpha)`.
- Implement `step(state, velocity, step_time)` and set `action_dim`,
  `state_dim`, and `min_state_dim` consistently. Override the base projection,
  speed, and heading methods when their differential-drive defaults are wrong.
- `KinematicsFactory.get_handler_class("name")` is a safe lookup. An unknown
  robot name warns and falls back to the differential handler; it is not proof
  that the custom class was registered.
- A command with a wrong number of rows fails in object conversion or is
  clipped incorrectly. Test the exact shape with a tiny fake state before
  constructing a larger scene.

## Map-generator extensions

- `Unknown or missing grid_generator name` means the module defining the
  subclass was not imported, the name is misspelled/case-mismatched, or the
  class has an empty `name`.
- A non-image generator requires `resolution`; the framework computes cell
  counts from world width/height and passes only `yaml_param_names` plus
  `width`/`height` to the constructor.
- Extra YAML keys are ignored by `build_grid_from_generator`, so a typo in a
  parameter may silently select the default. Keep a small constructor-level
  validation or assert the expected output in a smoke test.
- `_build_grid()` must return an array-like object. `generate()` converts it to
  float64; `.grid` is lazy. Return the documented 0–100 occupancy convention
  and check the shape against injected width/height.

## External-control failures

| Symptom | Recovery |
| --- | --- |
| `env.step(action)` raises a `step_mode='external'` `ValueError` | This is the ownership guard. Call `set_state()` and `set_velocity()` for each externally owned object, then call `env.step()` with no action. |
| Pose changes but sensors/collisions use an old pose | Use public setters and call `env.refresh()` after direct mutations, or let external `env.step()` perform its ordered refresh. Do not mutate `_state` or `_geometry`. |
| Reactive data reports the previous motion | Update velocity every tick. `set_state()` does not infer velocity from a pose delta. |
| A controller both changes pose and passes a velocity action | Choose one mode: internal action integration or external state ownership. Mixing them double-integrates or is rejected. |
| A direct setter looks correct but collision queries lag | `set_state()` updates the object's geometry, but an environment-wide collision tree is rebuilt by `env.refresh()`/`env.step()`. |
| External loop never advances | Check `pause_flag`, `debug_flag`, `quit_flag`, and that the environment is not already done; external mode still requires normal lifecycle cleanup. |

The external route updates sensors after all objects are refreshed. Use
[sensing and mapping](../../sensing-and-mapping/SKILL.md) for sensor-specific
payload and timing details.

## GUI and optional dependencies

- `pynput` is optional. If it is missing or cannot initialize, `KeyboardControl`
  falls back to the `mpl` backend. Install it only for live input and verify
  OS permissions separately.
- An invalid `backend` value also falls back to `mpl`. The MPL window must have
  focus; `display=False` intentionally avoids starting an OS listener.
- Tk/Qt backend warnings in a headless session are not proof that core IR-SIM
  failed. Use `MPLBACKEND=Agg` and `display=False` for safe checks. Do not
  claim live keyboard semantics from an Agg run.
- `MouseControl` requires a Matplotlib `Axes`. Mock `inaxes`, data
  coordinates, button, and scroll step for deterministic tests.
- CBF/QP examples require separately installed solver packages and external
  assumptions. A missing `cvxpy`, an infeasible QP, or unsupported obstacle
  geometry is an integration limitation, not a missing IR-SIM base feature.

## Safe verification sequence

From the generated skill tree, run only:

```bash
python skills/disco/ir-sim/sub-skills/extension-and-control/scripts/custom_behavior_smoke.py --help
python skills/disco/ir-sim/sub-skills/extension-and-control/scripts/custom_behavior_smoke.py
```

Then use mocked GUI events or a tiny external-state fixture if a downstream
verification plan requires it. Do not run live input, original usage scripts,
full native GUI tests, or project-specific CBF/QP experiments as part of this
helper.
