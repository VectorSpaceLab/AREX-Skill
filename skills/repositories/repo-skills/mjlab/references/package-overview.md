# Package overview

mjlab has two main layers.

## Simulation layer

The simulation layer composes MuJoCo assets and uploads them to MuJoCo Warp:

1. `EntityCfg` wraps an MJCF/MjSpec factory plus optional initial state,
   actuators, and spec editors.
2. `SceneCfg` combines terrain, named entities, sensors, and optional MjSpec
   edits into one scene.
3. `Scene` builds the combined `mujoco.MjSpec`, compiles an `MjModel`, and
   initializes entities and sensors.
4. `Simulation` owns MuJoCo Warp model/data objects, CUDA graph capture,
   `step`, `forward`, `reset`, and sensor-context execution.

Use [scene-simulation-assets](../sub-skills/scene-simulation-assets/SKILL.md)
for this layer.

## Manager layer

The manager layer defines the RL MDP on top of the simulation:

- `ObservationManager` builds actor/critic or custom observation groups.
- `ActionManager` maps policy tensors into actuator, tendon, or site targets.
- `RewardManager`, `TerminationManager`, and `MetricsManager` compute scalar
  signals.
- `EventManager` performs reset/startup/interval/step events and domain
  randomization.
- `CommandManager` generates command tensors such as velocity or motion targets.
- `CurriculumManager` changes difficulty or term parameters during training.
- `RecorderManager` attaches logging hooks without changing environment logic.

Use [environment-configuration](../sub-skills/environment-configuration/SKILL.md)
for lifecycle/config structure and [mdp-components](../sub-skills/mdp-components/SKILL.md)
for built-in term catalogs.

## Task and CLI layer

Built-in task families are registered under task IDs:

- Cartpole balance/swingup.
- Velocity locomotion for Unitree G1 and Go1 on flat or rough terrain.
- Tracking with Unitree G1 motion imitation.
- Manipulation/lift-cube tasks for the Yam robot, including camera variants.

The installed CLIs load these registry entries:

- `list-envs` lists registered task IDs.
- `train <TASK>` launches RSL-RL training with nested Tyro overrides.
- `play <TASK>` evaluates zero/random/trained policies and opens a viewer.
- `export-scene <TARGET>` writes a self-contained scene package.
- `viz-nan <DUMP>` inspects NaN guard dumps.
- `demo` downloads a pretrained demo motion/checkpoint and starts playback.

Use [training-evaluation-cli](../sub-skills/training-evaluation-cli/SKILL.md)
for operational commands.

## High-value imports

```python
from mjlab.envs import ManagerBasedRlEnv, ManagerBasedRlEnvCfg
from mjlab.scene import Scene, SceneCfg
from mjlab.entity import EntityCfg, EntityArticulationInfoCfg
from mjlab.sim import SimulationCfg
from mjlab.managers import ObservationTermCfg, RewardTermCfg, SceneEntityCfg
from mjlab.envs.mdp import observations, rewards, terminations, events
from mjlab.envs.mdp.actions import JointPositionActionCfg, JointEffortActionCfg
from mjlab.sensor import RayCastSensorCfg, CameraSensorCfg, ContactSensorCfg
from mjlab.terrains import TerrainEntityCfg, TerrainGeneratorCfg
from mjlab.rl import RslRlOnPolicyRunnerCfg, RslRlVecEnvWrapper
```

Prefer importing public objects from package-level modules when they are
re-exported. Use deeper module imports for specific task-family MDP terms or
advanced domain-randomization functions.
