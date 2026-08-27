# Registry API Reference

Habitat-Lab uses global registries as the bridge between import-time Python classes and runtime config nodes. A decorator call writes a class into a mapping; later factories and task constructors call a getter using the config `type` value.

## Core Habitat Registry

Import with `import habitat` and use `habitat.registry`, or import the object from `habitat.core.registry`.

| Component | Decorator | Getter | Mapping key | Expected base class | Usual config owner |
| --- | --- | --- | --- | --- | --- |
| Task | `@registry.register_task` | `registry.get_task(name)` | `task` | `EmbodiedTask` | `habitat.task.type` or factory task id |
| Task action | `@registry.register_task_action` | `registry.get_task_action(name)` | `task_action` | `Action` | `habitat.task.actions.<action>.type` |
| Simulator | `@registry.register_simulator` | `registry.get_simulator(name)` | `sim` | `Simulator` | `habitat.simulator.type` |
| Sensor | `@registry.register_sensor` | `registry.get_sensor(name)` | `sensor` | `Sensor` | `habitat.task.lab_sensors.<sensor>.type` |
| Measure | `@registry.register_measure` | `registry.get_measure(name)` | `measure` | `Measure` | `habitat.task.measurements.<measure>.type` |
| Dataset | `@registry.register_dataset` | `registry.get_dataset(name)` | `dataset` | `Dataset` | `habitat.dataset.type` |
| Environment | `@registry.register_env` | `registry.get_env(name)` | `env` | `gym.Env` | custom RL environment entry points |

Decorator rules:

- `@registry.register_sensor` registers the class name, such as `MySensor`, unless `name="custom_key"` is provided.
- `@registry.register_sensor(name="custom_key")` registers the key `custom_key` while leaving class and UUID names independent.
- All typed core decorators assert subclass compatibility at registration time.
- Reusing a key overwrites the mapping entry; there is no built-in duplicate guard.

Lookup rules:

- `make_task(id_task, **kwargs)`, `make_dataset(id_dataset, **kwargs)`, and `make_sim(id_sim, **kwargs)` assert that the getter returns a class.
- `EmbodiedTask` initializes measures, lab sensors, and actions by reading each config node, requiring `type`, and calling the matching getter.
- A missing config `type` raises `ValueError`; an unknown `type` raises an assertion like `invalid <name> type <type>`.

## Baselines Registry

Import with `from habitat_baselines.common.baseline_registry import baseline_registry`. `BaselineRegistry` inherits the core registry surface and adds baselines-specific categories.

| Component | Decorator | Getter | Mapping key | Expected base class or contract | Usual config owner |
| --- | --- | --- | --- | --- | --- |
| Trainer | `@baseline_registry.register_trainer` | `baseline_registry.get_trainer(name)` | `trainer` | `BaseTrainer` | `habitat_baselines.trainer_name` |
| Policy | `@baseline_registry.register_policy` | `baseline_registry.get_policy(name)` | `policy` | `Policy` | `habitat_baselines.rl.policy.name` |
| Observation transform | `@baseline_registry.register_obs_transformer` | `baseline_registry.get_obs_transformer(name)` | `obs_transformer` | `ObservationTransformer` | obs-transform config `type` |
| Storage | `@baseline_registry.register_storage` | `baseline_registry.get_storage(name)` | `storage` | rollout storage contract | `habitat_baselines.rl.storage` or agent access manager config |
| Updater | `@baseline_registry.register_updater` | `baseline_registry.get_updater(name)` | `updater` | policy updater contract | PPO/agent access manager updater config |
| Auxiliary loss | `@baseline_registry.register_auxiliary_loss` | `baseline_registry.get_auxiliary_loss(name)` | `aux_loss` | callable loss module contract | `habitat_baselines.rl.auxiliary_losses.<name>` |
| Agent access manager | `@baseline_registry.register_agent_access_mgr` | `baseline_registry.get_agent_access_mgr(name)` | `agent` | `AgentAccessMgr` | `habitat_baselines.rl.agent.type` |

Baselines lookup examples in the repository:

- PPO registers one trainer class under both `ddppo` and `ppo`.
- `PointNavBaselinePolicy` registers under its class name and implements `from_config(config, observation_space, action_space, **kwargs)`.
- Observation transforms register by class name and are constructed through `from_config` before transforming observation spaces and batches.
- PPO agent setup retrieves agent access managers, storage, updater, policy, and auxiliary losses from config names.

## Config-Name Alignment

Keep these names distinct and intentional:

- Registry key: the string stored by the decorator. This must equal the config node's `type` or baselines name field used by a getter.
- Config dictionary key: the local key in a config map, such as `agent_position_sensor`, `episode_info_example`, or `STRAFE_LEFT`. For task actions, this key is the action name accepted by `Env.step` and exposed in `ActionSpace`.
- Runtime UUID: the string returned by `_get_uuid()` for sensors/measures. This is the observation key or metric key, such as `agent_position`, `episode_info`, or `spl`.
- Class name: used as the default registry key only when the decorator has no explicit `name`.

Examples distilled from Habitat-Lab:

- A sensor can be registered as `my_supercool_sensor`, configured under `habitat.task.lab_sensors.agent_position_sensor.type`, and emit observations under `_get_uuid() == "agent_position"`.
- A measure class `EpisodeInfoExample` can be configured under `habitat.task.measurements.episode_info_example.type` and emit metrics under `_get_uuid() == "episode_info"`.
- A task action class `StrafeLeft` can be configured under `habitat.task.actions.STRAFE_LEFT.type` and registered by class name; `Env.step("STRAFE_LEFT")` uses the dictionary key, while registry lookup uses `StrafeLeft`.
- A trainer can be registered under a short string such as `ppo`; `baseline_registry.get_trainer(config.habitat_baselines.trainer_name)` must find it after the module import.
