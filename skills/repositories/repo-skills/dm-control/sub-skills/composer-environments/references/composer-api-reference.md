# Composer API reference for custom environments

This reference covers installed-package `dm_control.composer` workflows for building custom entities, tasks, and `composer.Environment` loops. It is intentionally focused on Composer abstractions; use the sibling MJCF/MuJoCo skill for raw model parsing/export and the suite skill for benchmark task loading.

## Core construction pattern

A Composer environment has three layers:

1. **Entity:** owns MJCF model pieces, attachments, entity-scoped observables, and optional lifecycle hooks.
2. **Task:** owns the root entity, task-level observables, reward/discount/termination logic, timing, action handling, and task hooks.
3. **Environment:** compiles the task's MJCF model into `mjcf.Physics`, handles resets/steps, observation buffering, hook scheduling, and `dm_env` specs.

Minimal public imports:

```python
from dm_control import composer, mjcf
from dm_control.composer.observation import observable
```

## `composer.Entity` contract

Implement a subclass with these pieces:

| Piece | Required? | Purpose |
|---|---:|---|
| `_build(self, *args, **kwargs)` | yes | Constructor body. Do not override `__init__`; `Entity.__init__` calls `_build`, then `_build_observables`, then applies `observable_options` if supplied. |
| `mjcf_model` property | yes | Return the entity's `mjcf.RootElement` or attached MJCF model object. Missing or invalid values break compilation, attachments, and observable key qualification. |
| `_build_observables(self)` | optional | Return a `composer.Observables` subclass. The default returns an empty `Observables` container. |
| `attachment_site` property | optional | Defaults to `mjcf_model`; override when children should attach to a specific site/frame. |
| lifecycle hooks | optional | Entity hooks have no `action` argument and are called after the task hook of the same name. |

Entity helper behavior:

- `entity.attach(child, attach_site=None)` attaches the child model without extra degrees of freedom and records a parent/child relation for `iter_entities()` and hook scanning. Add a joint such as a `freejoint` to the returned frame when the child should move independently.
- `entity.detach()` removes an attached child. Calling it on an unattached entity raises `RuntimeError`.
- `entity.iter_entities()` yields the entity and attached descendants depth-first.
- Pose helpers such as `get_pose`, `set_pose`, `shift_pose`, `get_velocity`, and `set_velocity` operate on an attached frame or freejoint. They require a current `mjcf.Physics` object and the entity must be attached where those semantics make sense.
- `ModelWrapperEntity(mjcf_model)` wraps an existing MJCF model with no custom logic; use it for simple root models or prototypes.

## `composer.Observables` contract

Subclass `composer.Observables` and mark methods that return observable objects with `@composer.observable`:

```python
class ArmObservables(composer.Observables):
    @composer.observable
    def joint_positions(self):
        return observable.MJCFFeature("qpos", self._entity.joints)
```

Important rules:

- `@composer.observable` is a cached property evaluated during entity construction. It should create an observable object; it should not read live physics state directly.
- Observables are disabled by default. Enable them individually (`obs.enabled = True`), call `entity.observables.enable_all()`, or pass `observable_options` to the entity constructor.
- `Observables.set_options(...)` accepts either a single options dict applied to all observables, or a dict mapping unqualified observable method names to option dicts. Valid option names are `update_interval`, `buffer_size`, `delay`, `aggregator`, `corruptor`, and `enabled`.
- `Observables.as_dict(fully_qualified=True)` returns entity-bound keys. Root entity keys may be plain method names; attached entity keys are prefixed by the entity model's `full_identifier`, such as `gripper/joints_pos`.
- Use `observables.as_dict(fully_qualified=False)` to see the unqualified names expected by `set_options`.
- `observables.dict_keys.<observable_name>` gives the entity-qualified key helper for decorated observables when the entity has a usable model identifier.

Task-level observables returned by `Task.task_observables` keep exactly the keys you provide and are not entity-qualified.

## `composer.Task` contract

Implement or override these methods/properties:

| Piece | Required? | Purpose |
|---|---:|---|
| `root_entity` property | yes | Return the root `composer.Entity` for model compilation, traversal, hooks, and entity observables. |
| `get_reward(self, physics)` | yes | Return the scalar reward for the current physics state. |
| `task_observables` property | optional | Return an `OrderedDict` or dict of task-level observables not tied to a single entity. Enable each observable. |
| `should_terminate_episode(self, physics)` | optional | Return `True` for task-defined terminal states. Default is `False`. |
| `get_discount(self, physics)` | optional | Return scalar discount. Default is `1.0`. |
| `get_reward_spec()` / `get_discount_spec()` | optional | Return non-default dm_env specs for custom reward/discount structures. |
| `action_spec(self, physics)` | optional | Default is a `BoundedArray` derived from MuJoCo actuators, with tab-separated actuator names in `spec.name`. Override for non-MuJoCo or transformed action spaces. |
| `before_step(self, physics, action, random_state)` | optional | Default calls `physics.set_control(action)`. If you override it, call `super().before_step(...)` or explicitly set controls. |

Timing rules:

- `physics_timestep` reads/writes `root_entity.mjcf_model.option.timestep`; if unset, MuJoCo's default `0.002` seconds is used.
- `control_timestep` defaults to `physics_timestep` unless explicitly set.
- `set_timesteps(control_timestep, physics_timestep)` changes both safely.
- `control_timestep` must be an integer multiple of `physics_timestep`; otherwise `ValueError` is raised.
- `physics_steps_per_control_step` is the integer ratio used by `composer.Environment` to decide how many MuJoCo substeps to run per agent action.

## Lifecycle sequence

Hook names are:

```python
(
    "initialize_episode_mjcf",
    "after_compile",
    "initialize_episode",
    "before_step",
    "before_substep",
    "after_substep",
    "after_step",
)
```

Hook call order is deterministic:

1. For each hook name, the **task hook** runs first.
2. Then non-trivial hooks on every entity in `root_entity.iter_entities()` run in traversal order.
3. Then extra hooks registered with `env.add_extra_hook(hook_name, callable)` run.

Episode reset sequence:

1. If MJCF recompilation is due, call `initialize_episode_mjcf(random_state)` on task, entities, and extra hooks. Modify MJCF structure or attributes here.
2. Recompile the current `root_entity.mjcf_model` into a new `mjcf.Physics`.
3. Call `after_compile(physics, random_state)`. Re-bind references or initialize helpers that depend on compiled physics here.
4. Enter `physics.reset_context()` and call `initialize_episode(physics, random_state)`. Set qpos/qvel, run initializers, and apply compiled-physics randomization here.
5. Reset the observation updater and return a `dm_env.TimeStep` with `StepType.FIRST`, `reward=None`, `discount=None`, and the initial observation.

Agent step sequence:

1. If the previous call ended the episode, `step(action)` first performs an implicit reset.
2. Call `before_step(physics, action, random_state)`. The default task implementation writes the action into MuJoCo controls.
3. Prepare observation schedules for the next control step.
4. For each physics substep: call `before_substep(physics, action, random_state)`, run `physics.step()`, then call `after_substep(physics, random_state)`.
5. Call `after_step(physics, random_state)`.
6. Update observations, compute reward and discount, test task termination and `time_limit`, and return `StepType.MID` or `StepType.LAST`.

## `composer.Environment` options

Constructor signature highlights:

```python
composer.Environment(
    task,
    time_limit=float("inf"),
    random_state=None,
    n_sub_steps=None,
    raise_exception_on_physics_error=True,
    strip_singleton_obs_buffer_dim=False,
    max_reset_attempts=1,
    recompile_mjcf_every_episode=True,
    fixed_initial_state=False,
    delayed_observation_padding=composer.ObservationPadding.ZERO,
    legacy_step=True,
)
```

| Option | Use |
|---|---|
| `time_limit` | Forces termination when `physics.time() >= time_limit`; task termination can still end earlier. |
| `random_state` | `None`, int seed, or `np.random.RandomState`. The same RNG object is passed to hooks, observables, and variations. |
| `n_sub_steps` | Deprecated. Prefer task `control_timestep` / `physics_timestep`; use only for compatibility. |
| `raise_exception_on_physics_error` | If `True`, MuJoCo `PhysicsError` propagates. If `False`, divergent physics terminates the episode with reward `0.0` and discount `0.0`. |
| `strip_singleton_obs_buffer_dim` | If `True`, observations with `buffer_size == 1` omit the leading buffer dimension. |
| `max_reset_attempts` | Retries `reset()` when `composer.EpisodeInitializationError` is raised. The final failure propagates. |
| `recompile_mjcf_every_episode` | If `True`, reset runs MJCF initialization and recompilation every episode. If `False`, later resets skip `initialize_episode_mjcf` and `after_compile` after the first reset. |
| `fixed_initial_state` | Restores the RNG state before MJCF initialization and episode initialization, giving identical starts for identical actions. |
| `delayed_observation_padding` | `ObservationPadding.ZERO` pads delayed buffers with zeros; `ObservationPadding.INITIAL_VALUE` pads with the first observed value. |
| `legacy_step` | Sets the underlying physics legacy stepping behavior. Keep the default unless reproducing behavior that requires changing it. |

Environment construction itself compiles a current model so specs and physics exist. `after_compile` is called after each compile. Do not assume there is only one `after_compile` call in the lifetime of an environment.

## Random state and recompilation behavior

- Every hook receives the environment's `np.random.RandomState` object. Use it instead of global `np.random` when reproducibility matters.
- `fixed_initial_state=True` rewinds the RNG state before reset-time randomization, so repeated resets produce identical initial states.
- Use `initialize_episode_mjcf` for changes that require recompilation: adding/removing geoms, changing MJCF attributes that MuJoCo reads at compile time, or applying `variation.MJCFVariator`.
- Use `initialize_episode` for qpos/qvel, controls, compiled-physics attributes, and collision-aware placement after compile.
- `env.physics` is a weak proxy to the current physics object. It becomes invalid after recompilation or `env.close()`. Reacquire it from `env.physics` inside the current reset/step context rather than caching it across episodes.

## Validation checklist before training

1. Construct the task and environment in a fresh Python process.
2. Print `env.action_spec()` and verify your policy emits exactly that shape, dtype, and bounds.
3. Call `time_step = env.reset()` and compare `time_step.observation.keys()` with `env.observation_spec().keys()`.
4. Verify entity-observable keys are expected, especially for attached entities whose keys include model prefixes.
5. Run several zero or random actions from the action spec and ensure `reward`, `discount`, `step_type`, and observation shapes remain stable.
6. If you use stochastic initialization, rerun with the same seed and confirm reproducible starts; rerun with different seeds and confirm intended variation.
7. If `initialize_episode_mjcf` changes the model, test both `recompile_mjcf_every_episode=True` and any planned `False` optimization explicitly.
8. If any observable renders camera images, validate rendering through the rendering/backend sub-skill before training.
