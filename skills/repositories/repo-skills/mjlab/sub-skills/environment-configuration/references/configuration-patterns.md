# Configuration patterns

This reference covers the manager-layer shape of mjlab environment configs. It
assumes the physical scene/entity objects already exist or are being designed in
the scene-focused sub-skill.

## `ManagerBasedRlEnvCfg` at a glance

`ManagerBasedRlEnvCfg` is a flat dataclass. The core fields are:

| Field | Role |
|---|---|
| `scene` | `SceneCfg` that owns `num_envs`, terrain, entities, and sensors. Scene details are handled by the scene/simulation sub-skill. |
| `sim` | `SimulationCfg`; the environment step duration is `sim.mujoco.timestep * decimation`. |
| `decimation` | Number of physics steps per policy/environment step. |
| `episode_length_s` | Episode duration in seconds; `max_episode_length = ceil(episode_length_s / step_dt)`. |
| `observations`, `actions`, `events`, `rewards`, `terminations`, `commands`, `curriculum`, `metrics`, `recorders` | Manager dictionaries keyed by user-chosen names. |
| `is_finite_horizon` | Whether the task's time limit is a true terminal boundary. False means time limits are artificial truncations for value bootstrapping. |
| `auto_reset` | Whether `step()` resets done environments before returning observations. |
| `scale_rewards_by_dt` | Whether reward terms are multiplied by `step_dt` before accumulation. Enabled by default. |

A minimal task config is assembled by constructing the manager dictionaries and
passing them into the dataclass:

```python
from mjlab.envs import ManagerBasedRlEnvCfg, mdp
from mjlab.managers import (
    EventTermCfg,
    ObservationGroupCfg,
    ObservationTermCfg,
    RewardTermCfg,
    SceneEntityCfg,
    TerminationTermCfg,
)
from mjlab.scene import SceneCfg
from mjlab.sim import MujocoCfg, SimulationCfg
from mjlab.terrains import TerrainEntityCfg


def make_env_cfg(robot_entity_cfg) -> ManagerBasedRlEnvCfg:
    robot = SceneEntityCfg("robot")
    observations = {
        "actor": ObservationGroupCfg(
            terms={
                "joint_pos": ObservationTermCfg(
                    func=mdp.joint_pos_rel,
                    params={"asset_cfg": robot},
                ),
                "joint_vel": ObservationTermCfg(
                    func=mdp.joint_vel_rel,
                    params={"asset_cfg": robot},
                ),
            },
            concatenate_terms=True,
            enable_corruption=False,
        ),
    }
    rewards = {
        "alive": RewardTermCfg(func=mdp.is_alive, weight=1.0),
    }
    terminations = {
        "time_out": TerminationTermCfg(func=mdp.time_out, time_out=True),
    }
    events = {
        "reset_scene": EventTermCfg(func=mdp.reset_scene_to_default, mode="reset"),
    }
    return ManagerBasedRlEnvCfg(
        scene=SceneCfg(
            terrain=TerrainEntityCfg(terrain_type="plane"),
            entities={"robot": robot_entity_cfg},
            num_envs=1,
        ),
        sim=SimulationCfg(mujoco=MujocoCfg(timestep=0.005)),
        decimation=4,
        episode_length_s=20.0,
        observations=observations,
        rewards=rewards,
        terminations=terminations,
        events=events,
    )
```

This example deliberately leaves the entity factory to the scene/simulation
sub-skill. The manager-layer obligations are the term names, config classes,
params, shapes, and lifecycle timing.

## Shared term dictionary pattern

Every manager dictionary is keyed by a stable string name. Names are used in
logs, active-term summaries, and cross-manager references such as
`command_name`, `action_name`, `reward_name`, or `termination_name`.

Common rules:

- Registration order is preserved. It affects concatenated observation order,
  action tensor slicing, recorder execution order, and printed active-term
  tables.
- `None` entries are skipped by managers that support optional terms. Empty
  observation groups, or groups where every term is `None`, are skipped.
- Most term configs carry `func` plus `params`. `params` are forwarded as
  keyword arguments after `env` and any lifecycle arguments.
- Function terms are called directly. Class terms are instantiated once with
  `(cfg=term_cfg, env=env)` when the manager prepares terms, then called like a
  function.
- If a class term implements `reset(env_ids)`, the manager calls it on reset for
  the reset environments.
- `SceneEntityCfg` objects inside `params` are resolved once during manager
  construction. Use resolved IDs in the term call instead of re-running regexes.
- Managers that instantiate class terms work on internal copies of configs, so a
  reusable factory config is not mutated by resolution.

## Manager term shapes and signatures

| Manager | Config shape | Callable contract | Output or side effect |
|---|---|---|---|
| Observation | `observations[group] = ObservationGroupCfg(terms={name: ObservationTermCfg(...)})` | `func(env, **params)` or class `__call__(env, **params)` | Tensor `[num_envs, D]` per term. Group returns concatenated tensor or a term dict. |
| Action | `actions[name] = ActionTermCfg` subclass | Config builds an `ActionTerm`; term receives a slice of the flat action tensor. | Total policy action shape must be `[num_envs, sum(action_dim)]`. Built-in action choices belong to the MDP sub-skill. |
| Reward | `rewards[name] = RewardTermCfg(func=..., weight=...)` | `func(env, **params)` | Tensor `[num_envs]`; multiplied by `weight` and by `step_dt` when `scale_rewards_by_dt=True`. NaN/Inf becomes zero. |
| Termination | `terminations[name] = TerminationTermCfg(func=..., time_out=...)` | `func(env, **params)` | Boolean tensor `[num_envs]`. `time_out=True` contributes to truncation; otherwise to terminal failure. |
| Event | `events[name] = EventTermCfg(func=..., mode=...)` | `func(env, env_ids, **params)` | Mutates scene/sim state. Modes are `startup`, `reset`, `interval`, `step`. |
| Command | `commands[name] = CommandTermCfg` subclass | Config builds a `CommandTerm` implementing `command`, `_resample_command(env_ids)`, `_update_command(env_ids)`, `_update_metrics()` | Maintains command tensors; resampled by timers and resets; metrics returned through reset logging. |
| Curriculum | `curriculum[name] = CurriculumTermCfg(func=...)` | `func(env, env_ids, **params)` | Mutates difficulty/config state on reset and may return scalar/dict state logged under `Curriculum/...`. |
| Metrics | `metrics[name] = MetricsTermCfg(func=..., reduce=...)` | `func(env, **params)` | Tensor `[num_envs]`; reduced per episode using `mean`, `last`, `max`, or `sum`. `per_substep=True` evaluates inside decimation. |
| Recorder | `recorders[name] = RecorderTermCfg(func=RecorderTermSubclass, params=...)` | subclass hooks `record_pre_reset`, `record_post_reset`, `record_post_step`, `close` | User-defined side effects for rollout logging; function-based recorder terms are invalid. |

## Observation groups, corruption, delay, and history

Each observation term flows through this pipeline:

```text
compute -> noise -> clip -> scale -> delay -> history
```

Important details:

- A term function returns `[num_envs, D]` before any processing.
- Noise is applied only when the surrounding `ObservationGroupCfg` has
  `enable_corruption=True`. This lets actor and critic groups share terms while
  the critic remains noise-free.
- `clip=(lo, hi)` clamps after noise. `scale` is applied after clipping and may
  be a scalar, tuple, or tensor-compatible value.
- Delay is configured with `delay_min_lag`, `delay_max_lag`,
  `delay_hold_prob`, `delay_update_period`, and per-environment flags. Convert a
  latency to lag steps with `lag_steps = latency_seconds / env.step_dt` and round
  or bracket using min/max lag.
- History is configured with `history_length` and `flatten_history_dim`.
  Flattened history produces `[num_envs, history_length * D]`; unflattened
  history keeps `[num_envs, history_length, D]`.
- If `ObservationGroupCfg.history_length` is set, it overrides per-term history
  settings for all terms in the group.
- With `flatten_history_dim=True` and `concatenate_terms=True`, history is
  term-major: all of term A's history is flattened before term B's history.
- Reset backfills only the reset environments' delay/history buffers. A partial
  reset does not advance timelines for other environments.
- `nan_policy` is set per observation group: `disabled`, `warn`, `sanitize`, or
  `error`. Per-term checking identifies `group/term`; final-only checking reports
  the group.

## `SceneEntityCfg` matching

Use `SceneEntityCfg` in term params to select one entity and optional element
subsets:

```python
SceneEntityCfg(
    name="robot",
    joint_names=(r".*hip.*", r".*knee.*"),
    body_names=("base",),
    preserve_order=False,
)
```

Resolution rules:

- `name` must match an entity key in the scene.
- Element fields include joints, bodies, geoms, sites, actuators, tendons,
  cameras, lights, materials, textures, and contact pairs.
- Name patterns use Python regular expressions with full-string matching. If you
  want substring behavior, include `.*` explicitly.
- If names are provided, IDs are computed. If IDs are provided, names are
  populated. If both are provided, they must agree.
- If a pattern matches no elements, resolution raises an error listing the
  unmatched pattern and available strings.
- If multiple patterns match the same target string, resolution raises an error.
  Make patterns mutually exclusive or split terms.
- With `preserve_order=False`, resolved IDs/names follow entity/native order.
  With `preserve_order=True`, they follow the query pattern order.
- Selecting all elements in entity order is optimized to `slice(None)` for fast
  tensor slicing.

## Custom term patterns

### Stateless scalar term

```python
import torch
from mjlab.managers import RewardTermCfg, SceneEntityCfg


def base_height(env, asset_cfg: SceneEntityCfg = SceneEntityCfg("robot")) -> torch.Tensor:
    robot = env.scene[asset_cfg.name]
    return robot.data.root_link_pos_w[:, 2]

rewards = {"base_height": RewardTermCfg(func=base_height, weight=0.1)}
```

Scalar reward, termination, and metrics terms must return one value per
environment: shape `[num_envs]`.

### Class term with cached setup

```python
class CachedPostureReward:
    def __init__(self, cfg, env):
        self.asset_cfg = cfg.params["asset_cfg"]  # already resolved on manager copy
        self.target = cfg.params["target"]

    def __call__(self, env):
        robot = env.scene[self.asset_cfg.name]
        error = robot.data.joint_pos[:, self.asset_cfg.joint_ids] - self.target
        return -torch.sum(error * error, dim=-1)

    def reset(self, env_ids):
        pass
```

Use a class when setup is expensive, when a `SceneEntityCfg` should be cached, or
when state must survive across steps and reset only for selected environments.

### Command term signatures

A command config subclasses `CommandTermCfg` and implements `build(env)`. The
term subclass implements:

```python
@property
def command(self) -> torch.Tensor: ...
def _update_metrics(self) -> None: ...
def _resample_command(self, env_ids: torch.Tensor) -> None: ...
def _update_command(self, env_ids: torch.Tensor | None) -> None: ...
```

`_update_command(None)` is the normal per-step update for all environments.
`_update_command(env_ids)` runs on reset-scoped updates. If the update advances
state such as a motion-frame index, advance only the selected environments.

### Event terms and model-field recomputation

Event functions receive `env` and `env_ids` and mutate state. Interval and step
events should be lightweight because they may run during every rollout step.
If a custom event changes MuJoCo model fields that require per-environment
storage or derived-constant refreshes, declare fields with
`mjlab.managers.event_manager.requires_model_fields` and choose a recompute level
from `mjlab.managers.event_manager.RecomputeLevel`. The event manager expands
fields before simulation graph capture and recomputes constants after the event
fires.
