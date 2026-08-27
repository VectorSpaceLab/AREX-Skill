# Extension Patterns

These recipes are distilled from Habitat-Lab's registries, examples, and tests. They are designed for code review and safe implementation planning; run full environments only after registry and config checks pass.

## Custom Lab Sensor

Use a lab sensor when a task needs an additional observation derived from simulator state, episode metadata, or task state.

Minimal recipe:

```python
from dataclasses import dataclass
from typing import Any

import numpy as np
from gym import spaces

import habitat
from habitat.config.default_structured_configs import LabSensorConfig

@habitat.registry.register_sensor(name="my_custom_sensor")
class MyCustomSensor(habitat.Sensor):
    def __init__(self, sim, config, **kwargs: Any):
        super().__init__(config=config)
        self._sim = sim

    def _get_uuid(self, *args: Any, **kwargs: Any) -> str:
        return "my_custom_observation"

    def _get_sensor_type(self, *args: Any, **kwargs: Any):
        return habitat.SensorTypes.POSITION

    def _get_observation_space(self, *args: Any, **kwargs: Any):
        return spaces.Box(low=-np.inf, high=np.inf, shape=(3,), dtype=np.float32)

    def get_observation(self, observations, *args: Any, episode, **kwargs: Any):
        return self._sim.get_agent_state().position.astype(np.float32)

@dataclass
class MyCustomSensorConfig(LabSensorConfig):
    type: str = "my_custom_sensor"
```

Config insertion pattern:

```python
with habitat.config.read_write(config):
    config.habitat.task.lab_sensors["my_custom_sensor_node"] = MyCustomSensorConfig()
```

Checklist:

- `type` equals the registry key.
- `_get_uuid()` equals the observation key consumers expect.
- Observation values match `_get_observation_space()` shape and dtype.
- The module containing the decorator is imported before `Env` or task construction.

## Custom Measure

Use a measure for metrics returned by `env.get_metrics()` or consumed by reward/success logic.

Minimal recipe:

```python
from dataclasses import dataclass
from typing import Any

import habitat
from habitat.config.default_structured_configs import MeasurementConfig

@habitat.registry.register_measure(name="MyProgressMeasure")
class MyProgressMeasure(habitat.Measure):
    cls_uuid = "my_progress"

    def __init__(self, sim, config, **kwargs: Any):
        super().__init__()
        self._sim = sim
        self._config = config

    def _get_uuid(self, *args: Any, **kwargs: Any) -> str:
        return self.cls_uuid

    def reset_metric(self, episode, task, *args: Any, **kwargs: Any):
        task.measurements.check_measure_dependencies(self.uuid, ["distance_to_goal"])
        self.update_metric(episode=episode, task=task, *args, **kwargs)

    def update_metric(self, episode, task, *args: Any, **kwargs: Any):
        distance = task.measurements.measures["distance_to_goal"].get_metric()
        self._metric = max(0.0, 1.0 - distance / self._config.max_distance)

@dataclass
class MyProgressMeasureConfig(MeasurementConfig):
    type: str = "MyProgressMeasure"
    max_distance: float = 10.0
```

Checklist:

- Use `check_measure_dependencies` in `reset_metric` before reading another measure.
- Read dependent metrics through `task.measurements.measures[uuid].get_metric()`.
- Keep `_get_uuid()` stable; changing it changes metric dictionary keys and dependency names.
- Include all dependent measures in `habitat.task.measurements`, not only the new measure.

## Custom Task Action

Use a task action when `Env.step` needs a new discrete or parameterized operation.

Minimal recipe:

```python
from dataclasses import dataclass

import habitat
from habitat.config.default_structured_configs import ActionConfig
from habitat.tasks.nav.nav import SimulatorTaskAction

@dataclass
class MyActionConfig(ActionConfig):
    type: str = "MyAction"
    scale: float = 1.0

@habitat.registry.register_task_action
class MyAction(SimulatorTaskAction):
    def __init__(self, *args, config, sim, **kwargs):
        super().__init__(*args, config=config, sim=sim, **kwargs)
        self._sim = sim
        self._scale = config.scale

    def _get_uuid(self, *args, **kwargs) -> str:
        return "my_action"

    def step(self, *args, task, **kwargs):
        # perform simulator or task update here
        return self._sim.step(None)
```

Config insertion pattern:

```python
with habitat.config.read_write(config):
    config.habitat.task.actions["MY_ACTION"] = MyActionConfig(type="MyAction", scale=0.5)
```

Action-space checklist:

- The config dictionary key, such as `MY_ACTION`, is the action name used by `Env.step` and `env.action_space.contains`.
- The config `type`, such as `MyAction`, is the registry key used to instantiate the class.
- If `step` accepts parameters, expose a matching `action_space` property returning a Gym space or `ActionSpace` so sampled and user-provided actions validate.
- If no simulator observation is returned from `step`, Habitat calls `sim.step(None)` after the action.

## Custom Task, Dataset, or Simulator

Use core registry decorators for factory-discovered top-level components:

```python
from habitat.core.registry import registry

@registry.register_task(name="MyTask-v0")
class MyTask(...):
    pass

@registry.register_dataset(name="MyDataset-v1")
class MyDataset(...):
    pass

@registry.register_simulator(name="MySim-v0")
class MySimulator(...):
    pass
```

Factory behavior:

- Task factories call `registry.get_task(id_task)` and assert the class exists.
- Dataset factories call `registry.get_dataset(id_dataset)` and assert the class exists.
- Simulator factories call `registry.get_simulator(id_sim)` and assert the class exists.

Checklist:

- Import the module before calling the factory.
- Match `habitat.task.type`, `habitat.dataset.type`, or `habitat.simulator.type` to the registered key used by the relevant factory.
- Keep dataset and simulator constructors compatible with the factory keyword arguments.

## Rearrangement and Robot Components

Rearrangement code uses the same registry primitives plus composed action and sensor conventions.

Patterns to follow:

- Register robot- or agent-specific sensors with `@registry.register_sensor` and return a stable `_get_uuid()` for downstream policies and measures.
- Register rearrangement actions with `@registry.register_task_action`; composed actions can look up nested controllers through `registry.get_task_action`.
- Use config fields to point a composed action to child controller registry keys instead of importing concrete child classes directly.
- For multi-agent components, include agent-specific names in config and UUIDs consistently so action and observation dictionaries do not collide.

Review checks:

- Nested action controller keys exist in the registry after imports.
- Composed `action_space` keys match the arguments accepted by `step`.
- Sensor UUIDs are unique across all active lab sensors.
- Config names for robot arms, grippers, humanoids, and base controllers are not confused with registry `type` strings.

## Custom Baseline Policy

Use a policy when the trainer's agent access manager should instantiate a new actor-critic implementation.

Recipe:

```python
from habitat_baselines.common.baseline_registry import baseline_registry
from habitat_baselines.rl.ppo.policy import Policy

@baseline_registry.register_policy(name="MyPolicy")
class MyPolicy(Policy):
    @classmethod
    def from_config(cls, config, observation_space, action_space, **kwargs):
        return cls(observation_space=observation_space, action_space=action_space, **kwargs)
```

Checklist:

- Subclass the expected policy base or compatible project base.
- Implement `from_config(config, observation_space, action_space, **kwargs)` because Habitat baselines construct policies through this hook.
- Align the policy config name with the registry key, such as `habitat_baselines.rl.policy.name = MyPolicy`.
- Ensure required sensors are present in `observation_space.spaces` before assuming observation keys in the network.

## Custom Baseline Trainer

Use a trainer for a new training/evaluation loop.

Recipe:

```python
from habitat_baselines.common.base_trainer import BaseTrainer
from habitat_baselines.common.baseline_registry import baseline_registry

@baseline_registry.register_trainer(name="my_trainer")
class MyTrainer(BaseTrainer):
    supported_tasks = ["Nav-v0"]
```

Checklist:

- Register under the short config string used by `habitat_baselines.trainer_name`.
- Keep `supported_tasks` aligned with task registry keys the trainer accepts.
- Import the module before `baseline_registry.get_trainer(config.habitat_baselines.trainer_name)` runs.
- Delegate training/evaluation behavior and checkpoint handling to the baselines-training sub-skill.

## Custom Observation Transform

Use an observation transformer for batched tensor preprocessing and observation-space rewriting.

Recipe:

```python
import copy
import torch
from habitat_baselines.common.baseline_registry import baseline_registry
from habitat_baselines.common.obs_transformers import ObservationTransformer

@baseline_registry.register_obs_transformer(name="MyTransform")
class MyTransform(ObservationTransformer):
    def __init__(self, key="rgb"):
        super().__init__()
        self.key = key

    @classmethod
    def from_config(cls, config):
        return cls(key=config.key)

    def transform_observation_space(self, observation_space):
        observation_space = copy.deepcopy(observation_space)
        # update observation_space.spaces[self.key] if shape/range changes
        return observation_space

    @torch.no_grad()
    def forward(self, observations):
        # update observations[self.key] consistently with transform_observation_space
        return observations
```

Checklist:

- `from_config` consumes the structured transform config.
- `transform_observation_space` deep-copies before modifying shapes.
- `forward` returns tensors whose per-environment shapes are contained by the transformed observation space.
- Channel order, semantic interpolation, and batch dimensions match existing transform utilities.

## Storage, Updater, Auxiliary Loss, and Agent Access Manager

Use baselines registry extension points when PPO internals need to be swapped.

Patterns:

- `@baseline_registry.register_storage` for rollout storage classes looked up by agent access managers.
- `@baseline_registry.register_updater` for PPO or HRL update implementations.
- `@baseline_registry.register_auxiliary_loss(name="short_name")` for auxiliary loss modules referenced by config dictionary key.
- `@baseline_registry.register_agent_access_mgr` for classes that construct policy, storage, and updater objects for trainers.

Checklist:

- Confirm the caller's getter and config path before choosing the registry category.
- Keep constructor signatures compatible with existing callers.
- Use the bundled probe to confirm the key is present after imports.
