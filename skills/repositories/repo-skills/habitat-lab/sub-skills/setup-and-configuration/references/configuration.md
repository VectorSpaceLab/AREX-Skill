# Habitat-Lab Configuration

Habitat-Lab uses Hydra and OmegaConf for runtime config composition. Most workflows should compose a config first, inspect paths and key values, and only then create environments, trainers, or HITL apps.

## Entry Points

Use the installed packages, not source checkout paths:

```python
import habitat

config = habitat.get_config(
    "benchmark/nav/pointnav/pointnav_habitat_test.yaml",
    overrides=["habitat.environment.max_episode_steps=5"],
)
```

```python
from habitat_baselines.config.default import get_config

config = get_config(
    "pointnav/ppo_pointnav_example.yaml",
    overrides=["habitat_baselines.total_num_steps=10"],
)
```

Verified public signatures:

- `habitat.config.default.get_config(config_path: str, overrides: Optional[List[str]] = None, configs_dir: str = <package config dir>) -> DictConfig`
- `habitat_baselines.config.default.get_config(config_path: str, overrides: Optional[list] = None, configs_dir: str = <baseline config dir>) -> DictConfig`
- `habitat.config.read_write.read_write(config) -> context manager`

`config_path` can be an absolute/relative YAML file or a path relative to the installed package config directory. Core Habitat configs live under the installed `habitat/config` package; baselines configs live under the installed `habitat_baselines/config` package and also register Habitat config groups.

## Config Families

Common core Habitat config families:

- `benchmark/nav/...`: primary navigation configs such as PointNav, ObjectNav, ImageNav, InstanceImageNav, EQA, and VLN.
- `benchmark/rearrange/...`: primary rearrangement, skills, play, demo, and multi-task configs.
- `benchmark/multi_agent/...`: social/multi-agent primary configs.
- `habitat/dataset/...`: dataset group options for PointNav, ObjectNav, InstanceImageNav, EQA, VLN, and rearrangement datasets.
- `habitat/task/...`: task group options such as `pointnav`, `objectnav`, `imagenav`, `instance_imagenav`, `vln_r2r`, and rearrangement task groups.
- `habitat/simulator/agents/...`: robot/embodied-agent definitions such as Fetch, Spot, Stretch, humanoid, and human.
- `habitat/simulator/sensor_setups/...`: reusable RGB, depth, semantic, and RGB-D sensor bundles.

Common baselines config families:

- `pointnav/...`: PPO/DDPPO PointNav examples and challenge-style configs.
- `objectnav/...`, `imagenav/...`, `instance_imagenav/...`: navigation baselines for other task families.
- `rearrange/...`: rearrangement RL and hierarchical configs.
- `eqa/...`, `social_nav/...`, `social_rearrange/...`: specialized baseline workflows.

## Hydra Composition Model

Habitat primary YAML files use a Hydra defaults list to assemble an output config from structured config schemas and config group options. A typical navigation config composes:

```yaml
# @package _global_
defaults:
  - /habitat: habitat_config_base
  - /habitat/task: pointnav
  - /habitat/simulator/agents:
    - rgbd_agent
  - /habitat/dataset/pointnav: habitat_test
  - _self_
```

The composed object is an OmegaConf `DictConfig` with lowercase keys under namespaces such as `habitat`, `habitat_baselines`, and `hydra`. Important runtime paths are usually under:

- `habitat.dataset.data_path`: episode dataset path, often containing `{split}`.
- `habitat.dataset.scenes_dir` or `habitat.dataset.scene_dir`: scene dataset root.
- `habitat.simulator.scene`: specific scene file or scene-instance config.
- `habitat.simulator.agents.<agent>.articulated_agent_urdf`: robot URDF path.
- `habitat.simulator.habitat_sim_v0.physics_config_file`: physics config path when present.

## Override Syntax

Use dotted key overrides for scalar or nested values:

```bash
habitat.environment.max_episode_steps=20
habitat.seed=123
habitat.simulator.agents.rgbd_agent.sim_sensors.rgb_sensor.width=128
habitat.dataset.split=val
habitat_baselines.total_num_steps=1000
habitat_baselines.evaluate=True
```

Use Hydra group overrides when changing config group choices:

```bash
benchmark/nav/pointnav=pointnav_hm3d
/habitat/dataset/pointnav=habitat_test
/habitat/simulator/sensor_setups@habitat.simulator.agents.main_agent=rgbd_head_rgbd_arm_agent
```

When passing overrides through Python, provide each override as one list element:

```python
config = habitat.get_config(
    "benchmark/nav/pointnav/pointnav_habitat_test.yaml",
    overrides=[
        "habitat.environment.max_episode_steps=3",
        "habitat.dataset.split=val",
    ],
)
```

For command-line baselines, Hydra parses extra arguments after `--config-name`:

```bash
python -m habitat_baselines.run \
  --config-name=pointnav/ppo_pointnav_example.yaml \
  habitat_baselines.evaluate=True \
  habitat.environment.max_episode_steps=5
```

Older flags such as `--exp-config` and `--run-type` are intentionally rejected by the current Hydra-powered baselines entry point. Use `--config-name=<path-inside-baselines-config>` and `habitat_baselines.evaluate=True/False` instead.

## Readonly Configs And `read_write`

`habitat.get_config` patches and returns a readonly OmegaConf config. Direct mutation outside `read_write` can fail. For safe programmatic edits:

```python
import habitat
from habitat.config.read_write import read_write

config = habitat.get_config("benchmark/nav/pointnav/pointnav_habitat_test.yaml")
with read_write(config):
    config.habitat.environment.max_episode_steps = 5
```

`read_write` temporarily disables OmegaConf readonly and struct flags, then restores the previous state. Prefer Hydra overrides when possible; use `read_write` for dynamic edits that are easier to express in Python or when updating nested dictionaries such as agent sensor maps.

## Validation Pattern Before Runtime

Use this order before creating `Env`, Gym wrappers, baselines trainers, or HITL apps:

1. Import the expected packages: `habitat`, `habitat_sim`, `magnum`, and optionally `habitat_baselines` or `habitat_hitl`.
2. Compose the intended config with all user overrides.
3. Print or inspect important keys with OmegaConf path selection.
4. Resolve dataset and asset paths relative to the process working directory, because many Habitat configs intentionally use paths like `data/...`.
5. Check that episode files, scene roots, scene files, robot URDFs, and physics configs exist before running expensive simulation.
6. Only after the config and data checks pass, route to the runtime sub-skill for environment stepping, training, or HITL launch.

The bundled `../scripts/config_probe.py` implements this pattern for imports, config composition, selected key printing, and optional data-path existence checks.

## Interpreting Common Config Keys

- `habitat.env_task` and `habitat.env_task_gym_id`: identify Env/Gym integration choices.
- `habitat.environment.max_episode_steps`: caps episode length by steps.
- `habitat.task.type`: selects task implementation, such as navigation, object navigation, rearrangement, or PDDL tasks.
- `habitat.task.actions`, `habitat.task.measurements`, and `habitat.task.lab_sensors`: dictionaries populated by config group options.
- `habitat.simulator.type`: simulator backend registry key, normally Habitat-Sim backed.
- `habitat.simulator.agents` and `habitat.simulator.agents_order`: define embodied agents and must agree after composition.
- `habitat.dataset.type`, `habitat.dataset.split`, `habitat.dataset.data_path`, and `habitat.dataset.scenes_dir`: define dataset loader and asset roots.
- `habitat_baselines.trainer_name`: selects the baselines trainer registry entry.
- `habitat_baselines.evaluate`: switches baselines run mode from training to evaluation when using `habitat_baselines.run`.

## Choosing Where To Fix A Config

- If a user needs a one-off run, use Hydra CLI/Python overrides.
- If a user needs a reusable experiment, create a YAML that extends a nearby primary config and overrides values after the defaults list.
- If a user needs to add new sensors, measures, actions, tasks, or config schemas, route to `../extension-patterns/SKILL.md` rather than editing setup instructions.
- If a user asks why stepping fails after config composition succeeds, route to `../tasks-datasets-and-envs/SKILL.md` for runtime Env diagnostics.
