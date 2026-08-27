# Extension API and discovery

This reference is the operating contract for extension authors. It is intentionally limited to registration, construction, serialization, and dry-run checks; robot, camera, teleoperator, and policy behavior remain in their focused skills.

## Package discovery

`lerobot.utils.import_utils.register_third_party_plugins()` scans `importlib.metadata.distributions()`. It reads each distribution's `Name` metadata and imports names that start exactly with one of:

- `lerobot_robot_`
- `lerobot_camera_`
- `lerobot_teleoperator_`
- `lerobot_policy_`
- `lerobot_env_`

The package name is only a discovery prefix. The usable config `type` is whatever the imported package registered, so inspect the package's own public README or exported config—not the suffix guessed from the distribution. A distribution is imported at most once per Python process by normal import caching. Import exceptions are logged and added to a failed list; discovery continues, so a later unknown type may be caused by an earlier failed plugin.

The discovery helper does not normalize hyphens to underscores before matching. Publish an installable distribution name that actually matches the prefix, and verify its `Name` metadata. The read-only probe lists candidates without importing them.

## Explicit config plugins

The draccus wrapper supports a nested argument ending in `discover_packages_path`, for example `--env.discover_packages_path=vendor_pkg`. The parser:

1. extracts both `--key=value` and `--key value` forms;
2. calls `load_plugin(package_path)` before config parsing;
3. imports the package and each immediate module found by `pkgutil.iter_modules(package.__path__)`;
4. removes the discovery flag before the target config is parsed.

The package should perform registration during import. A missing package or an import failure is reported as `PluginLoadError`, including the CLI argument that selected it. This explicit route is useful for env or other package plugins that should not be discovered globally.

Do not specify both `--field.path=...` and `--field.type=...`: the parser rejects that combination. A `path` value means load a pretrained/config object and is not a ChoiceRegistry type.

## Choice registries and hardware factories

`RobotConfig`, `CameraConfig`, `TeleoperatorConfig`, `EnvConfig`, and `PreTrainedConfig` are draccus `ChoiceRegistry` bases. A concrete config normally uses `@BaseConfig.register_subclass("stable_name")`. Its `type` property is the registered name. Use the corresponding factory rather than bypassing it:

- `make_robot_from_config(config)` returns a `Robot` and has built-in branches before a convention fallback.
- `make_cameras_from_configs(configs)` constructs the configured camera map.
- `make_teleoperator_from_config(config)` returns a teleoperator and has built-in branches before a convention fallback.
- `make_policy_config(policy_type, **kwargs)` resolves the registered `PreTrainedConfig`; `get_policy_class(name)` resolves the modeling class lazily.

The convention fallback in `make_device_from_device_class()` derives the implementation class by removing `Config` from the config class name and tries the config's parent module, a lower-case class module, and a `config_`-replacement module. For a plugin config called `FooConfig`, expose a callable `Foo` in one of those importable locations. A missing vendor import should fail when that device is selected, not make the entire base package unimportable.

A robot config's `__post_init__` requires camera `width`, `height`, and `fps` when cameras are present. Camera and teleoperator IDs/calibration directories are config data; connecting, calibrating, or sending action is a separate hardware operation and is never part of a probe.

## Custom policy boundary

A policy plugin registers a concrete subclass of `PreTrainedConfig` with a unique name. The lazy policy factory rewrites the registered configuration module convention to find a `*Policy` modeling class. The config must implement the abstract observation/action/reward delta properties, optimizer and scheduler presets, and feature validation inherited from `PreTrainedConfig`. Heavy optional dependencies belong in the modeling module and should be guarded with LeRobot's availability flags and `require_package()` at use time.

After registration, validate the whole boundary with `make_policy_config()` and `get_policy_class()` in a process that has the plugin imported. A registered config alone is not enough if the modeling module/class convention is wrong or the optional extra is absent.

## Custom processors

`ProcessorStepRegistry.register(name="unique_step")` is the preferred portable registration. A concrete `ProcessorStep` must implement:

- `__call__(transition) -> transition`, with a defined input/output transition contract;
- `transform_features(features) -> features`, describing shape/type/modal changes without sample data.

Use the semantic base when appropriate: `ObservationProcessorStep.observation`, `ActionProcessorStep.action`, `RobotActionProcessorStep.action`, `PolicyActionProcessorStep.action`, `RewardProcessorStep.reward`, `DoneProcessorStep.done`, `TruncatedProcessorStep.truncated`, `InfoProcessorStep.info`, or `ComplementaryDataProcessorStep.complementary_data`. These wrappers copy/check the targeted transition field and set `step.transition` for cross-field logic.

Optional boundaries are deliberately separate: `get_config()` must return JSON-compatible constructor values; `state_dict()`/`load_state_dict()` carry tensor state; `save_artifacts()` may write only checkpoint-relative assets and must return relative paths; `reset()` clears runtime state. Keep artifact paths free of absolute paths and `..` traversal.

`DataProcessorPipeline` executes steps sequentially and supports `before_step_hooks`, `after_step_hooks`, and `step_through()` for local debugging. It serializes each registered step as `registry_name` plus `config`; unregistered steps use a fully qualified `class` path. Prefer the registry for portability.

## Pipeline reconstruction rules

`DataProcessorPipeline.from_config(config, state_dict=None, overrides=None)` is local/in-memory and does not download. Each step must have `registry_name` or `class`; registered names are resolved from `ProcessorStepRegistry`, otherwise the fully qualified class is imported. Constructor config is merged with per-step overrides, with overrides winning. Unused override keys are errors.

`from_pretrained(source, config_filename=...)` accepts a local directory, a single local JSON file, or a Hub model id. It resolves declared artifacts and safetensors state, rejects absolute/traversal artifact paths, and can require Hub credentials/network for a Hub id. Use `local_files_only=True` for an explicitly offline load. Missing old-format processor files may produce a migration error; do not “fix” it by guessing a new config.

## Collision and unknown-type recovery

Registries are process-global. A duplicate processor name raises `ValueError` at decorator/import time. A duplicate ChoiceRegistry name can make import or config parsing fail. Do not catch and continue with an ambiguous registry. In a fresh process, remove the duplicate package, rename the plugin's registration, or choose one explicit plugin path. For an unknown type, first run the read-only distribution probe, then explicitly import the intended package in a controlled local check and inspect its registration. Never solve an unknown type by adding a random built-in type to the config.
