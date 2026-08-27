# Extension Troubleshooting

Use this guide when an extension class exists but Habitat-Lab cannot find or use it.

## Missing Registry Key

Symptoms:

- `Could not find task with name ...`
- `Could not find dataset ...`
- `Could not find simulator with name ...`
- `invalid <config-name> type <type>`
- `NoneType` errors after a `baseline_registry.get_*` lookup

Likely causes:

- The module containing the decorator was never imported.
- The config `type` or baselines name does not match the registry key.
- The decorator used the class name but the config uses a custom string, or vice versa.
- The extension is registered in `habitat.registry` but looked up through a baselines category, or the reverse.

Checks:

From this sub-skill directory:

```bash
python scripts/inspect_registry_extensions.py --import-module my_project.extensions --key sensor:my_custom_sensor
python scripts/inspect_registry_extensions.py --import-module my_project.baselines_ext --key trainer:my_trainer
```

Fixes:

- Import the extension package in the entry point before config or factory construction.
- Set the config `type` or baselines config field to the decorator key exactly.
- Use `@...register_*(name="stable_key")` for public config names rather than relying on class names.

## Duplicate Registration

Symptoms:

- A key resolves to an unexpected class.
- Changing import order changes behavior.
- A custom component silently replaces a built-in or another extension.

Cause:

- Registry writes are simple mapping assignments; a later registration with the same key overwrites the earlier class.

Fixes:

- Choose globally distinctive keys for public extensions.
- Probe the class module and qualname for the key before and after importing your extension.
- Avoid registering test doubles under production keys outside test scope.

## Missing Config Group or Structured Config

Symptoms:

- Config composition fails before registry lookup.
- A config node lacks `type` and `EmbodiedTask` raises `Could not find type in ...`.
- Custom fields are missing or are `MISSING` at runtime.

Likely causes:

- The config node was added to the wrong map.
- The structured config class does not extend the appropriate Habitat config base.
- Hydra/OmegaConf config groups were not registered or included.

Fixes:

- Sensors go under `habitat.task.lab_sensors`; measures under `habitat.task.measurements`; task actions under `habitat.task.actions`.
- Sensor configs should extend `LabSensorConfig`; measure configs should extend `MeasurementConfig`; action configs should extend `ActionConfig`.
- Ensure the config node includes `type` and every required typed field.
- Keep dictionary keys user-facing and `type` registry-facing.

## Import Order Failures

Symptoms:

- The extension works in a notebook cell after manual import but fails from CLI or tests.
- `inspect_registry_extensions.py --import-module ...` finds the key, but without `--import-module` it does not.

Fixes:

- Add a small import side-effect module such as `my_project.habitat_extensions` and import it from the application entry point.
- For baselines, import custom trainer/policy/transform modules before `habitat_baselines.run` resolves registry keys.
- Keep decorator calls at module import time, not inside functions that may never run.

## Measure Dependency Failures

Symptoms:

- A measure key is absent from `task.measurements.measures`.
- `check_measure_dependencies` fails.
- A measure reads stale or uninitialized values.

Likely causes:

- The dependent measure is not enabled in config.
- The dependency UUID does not match `_get_uuid()`.
- The custom measure reads another measure before reset/update establishes it.

Fixes:

- Add all dependent measures to `habitat.task.measurements`.
- Use class constants like `cls_uuid` for dependency strings when available.
- Call `task.measurements.check_measure_dependencies(self.uuid, [dep_uuid])` in `reset_metric`.
- Read dependent values through `task.measurements.measures[dep_uuid].get_metric()` after dependency checks.

## Action Space Mismatch

Symptoms:

- `env.action_space.contains(action)` returns false.
- `Can't find '<action>' action in ...`.
- `step` receives missing or unexpected keyword arguments.

Likely causes:

- The `Env.step` action name uses the config dictionary key, not the registry `type` or `_get_uuid()`.
- Parameterized actions do not expose an `action_space` matching `step` arguments.
- `action_args` keys do not match `step` parameter names.

Fixes:

- Use the configured action key for `Env.step`, such as `"STRAFE_LEFT"`, not necessarily `"StrafeLeft"`.
- For no-argument actions, rely on the base empty action space.
- For parameterized actions, return a Gym `spaces.Dict` or Habitat `ActionSpace` whose keys match `step` parameters.
- Reuse a narrow `action_space.contains` test before full simulator execution.

## Observation Transform Shape Issues

Symptoms:

- Transformed batches are incompatible with transformed observation spaces.
- Model construction fails because expected observation keys or channel orders changed.
- Semantic masks are interpolated incorrectly.

Likely causes:

- `transform_observation_space` and `forward` disagree on output shape.
- Transform code mutates the original observation space in place and surprises later transforms.
- `channels_last`, semantic interpolation mode, or target keys differ from the config.

Fixes:

- Deep-copy observation spaces before mutation.
- Use a test like: transform the observation space, batch-sample it, run `forward`, and assert the transformed observation space contains one unbatched result.
- Keep semantic transforms nearest-neighbor and image/depth transforms area or bilinear as appropriate.
- Make `trans_keys` explicit in config and skip absent observation keys.

## Baseline Policy or Trainer Not Found

Symptoms:

- `baseline_registry.get_trainer(...)` returns `None`.
- Agent access manager fails to find a policy, storage, updater, or auxiliary loss.
- A policy class is found but construction fails.

Fixes:

- Import the module containing the `baseline_registry` decorator before the baselines entry point resolves config.
- Align `habitat_baselines.trainer_name`, `habitat_baselines.rl.policy.name`, `habitat_baselines.rl.agent.type`, storage, updater, and auxiliary loss names with the decorator keys.
- Confirm policy classes implement `from_config(config, observation_space, action_space, **kwargs)`.
- Confirm trainers subclass the expected base trainer and declare compatible `supported_tasks`.
