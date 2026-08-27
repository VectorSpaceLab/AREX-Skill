# Composer environment troubleshooting

Use this guide for custom `dm_control.composer` entity/task/environment failures. If the traceback is an OpenGL, pixel rendering, GLFW, EGL, or OSMesa issue, route to the rendering sub-skill after confirming the Composer code does not require rendering.

## Quick triage

1. Confirm the package imports in a clean process. If missing, install with `python -m pip install dm_control`; for unreleased snapshots use `python -m pip install git+https://github.com/google-deepmind/dm_control.git`. Do not use editable installs.
2. Run the bundled smoke: `python scripts/composer_minimal_task.py --steps 3`.
3. If your custom environment fails but the smoke passes, compare your entity `_build`, `mjcf_model`, task `root_entity`, timing, action spec, and enabled observable keys against the smoke output.
4. Validate without rendering first. Add camera observables only after the non-rendering reset/step loop is stable.

## Symptom matrix

| Symptom | Likely cause | What to do |
|---|---|---|
| `TypeError` or abstract-method error when instantiating an entity | `composer.Entity` subclass did not implement `_build` or `mjcf_model` | Implement `_build` instead of overriding `__init__`; assign a `mjcf.RootElement` or model object during `_build`; return it from `mjcf_model`. |
| Abstract-method error when instantiating a task | `composer.Task` subclass did not implement `root_entity` or `get_reward` | Add a `root_entity` property returning a `composer.Entity` and implement `get_reward(physics)`. For no-reward prototypes, return `0.0`. |
| `RuntimeError` mentioning a call before `root_entity` is available | `control_timestep`, `physics_timestep`, or `set_timesteps` was called before the task had a root entity | Set `self._root_entity` before calling `set_timesteps(...)` in task initialization. |
| `AttributeError` or `ValueError` retrieving `mjcf_model.full_identifier` | Entity `mjcf_model` is missing, invalid, or not built before observables are qualified | Ensure `_build` assigns the model before `_build_observables` runs. Do not return raw bodies/sites as `mjcf_model`; return the entity's model root. |
| `KeyError: No observable with name ...` | `set_options` used environment-qualified keys or misspelled unqualified method names | Configure with names from `entity.observables.as_dict(fully_qualified=False)`. Use `env.observation_spec()` only for policy-facing keys. |
| Observation key missing from `TimeStep.observation` | Observable exists but is disabled, task observable was recreated disabled, or a name collision overwrote it | Set `enabled=True`, call `enable_all()` intentionally, keep task observable objects stable, and inspect `env.observation_spec()` after reset. |
| Observation shape differs from expected | Buffering, aggregation, or `strip_singleton_obs_buffer_dim` changed dimensions | Check `buffer_size`, `delay`, `aggregator`, and environment `strip_singleton_obs_buffer_dim`. Remember that unaggregated buffers add a leading buffer axis. |
| `KeyError: Unrecognized aggregator name` | Aggregator string is not one of the built-ins | Use `min`, `max`, `mean`, `median`, `sum`, or pass a callable aggregator. |
| Bounds disappear from an aggregated spec | Aggregator is not known to preserve bounds | For custom aggregators that preserve bounds, set `aggregator.preserves_bounds = True`. Built-in `sum` is intentionally not bounds-preserving. |
| `ReferenceError` from a cached `physics` object | `env.physics` is a weak proxy invalidated by recompilation or `env.close()` | Do not store `env.physics` across resets or after close. Reacquire `env.physics` inside the current operation. Re-bind elements in `after_compile` if needed. |
| `composer.EpisodeInitializationError` during reset | Task/initializer could not find a valid initial state | Broaden randomization ranges, reduce collision/contact constraints, increase initializer attempts, and set `max_reset_attempts` high enough for expected rejection sampling. |
| Reset retries never recover | Every sampled initialization is invalid or deterministic failure repeats | Log or inspect the sampled values, verify collision constraints, and test with a fixed simple initial state. More reset attempts cannot fix a deterministic invalid model. |
| `ValueError` about control timestep divisibility | `control_timestep / physics_timestep` is not an integer | Choose values where the control timestep is an exact integer multiple of the physics timestep, or call `set_timesteps(...)` with compatible values. |
| Step fails with action shape or dtype mismatch | Policy action does not match `env.action_spec()` | Generate actions with `spec.shape`, `spec.dtype`, `spec.minimum`, and `spec.maximum`. For custom action spaces, override `Task.action_spec` and `Task.before_step` together. |
| No actuator response after overriding `before_step` | Override forgot to set MuJoCo controls | Call `super().before_step(physics, action, random_state)` or explicitly write controls through `physics.set_control(...)` / bound actuator controls. |
| Later resets stop applying MJCF randomization | Environment was created with `recompile_mjcf_every_episode=False` | Use `recompile_mjcf_every_episode=True` when `initialize_episode_mjcf` must run each episode. Only disable recompilation after proving the model is static between episodes. |
| Same seed is not reproducible | Global randomness or stateful variation objects are used outside the environment RNG | Use the `random_state` argument passed to hooks/variations. Recreate or deliberately reset stateful variations such as sequences and random walks. |

## Abstract method and constructor pitfalls

Do not override `Entity.__init__` for ordinary entities. `Entity.__init__` performs required Composer setup:

1. Records parent/attachment state.
2. Pops `observable_options` from kwargs.
3. Calls `_build(*args, **kwargs)`.
4. Calls `_build_observables()`.
5. Applies observable options.

Safe entity skeleton:

```python
class MyEntity(composer.Entity):
    def _build(self, name="my_entity"):
        self._mjcf_root = mjcf.RootElement(model=name)
        # Add bodies, joints, geoms, actuators, sensors here.

    @property
    def mjcf_model(self):
        return self._mjcf_root
```

If a base class truly must customize `__init__`, it must still call `super().__init__(...)` exactly once and leave `_build`/`_build_observables` semantics intact.

## Missing `mjcf_model` or `root_entity`

`mjcf_model` must be available immediately after entity `_build` finishes. Common mistakes:

- Returning `worldbody`, `body`, `site`, or another child element instead of the model root.
- Creating a model in a local variable and not storing it on the entity.
- Referring to attributes that are assigned only after `super().__init__()` returns.
- Attaching children before the parent model exists.

`root_entity` must be available before task timing or environment construction. Safe task skeleton:

```python
class MyTask(composer.Task):
    def __init__(self):
        self._root_entity = MyEntity()
        self.set_timesteps(control_timestep=0.02, physics_timestep=0.005)

    @property
    def root_entity(self):
        return self._root_entity

    def get_reward(self, physics):
        return 0.0
```

## Observable key failures

Keep separate the names used for configuration and the names seen by an agent:

- Configuration names are unqualified decorated method names: `joint_position`.
- Environment observation keys may be qualified: `arm/joint_position`.
- Task-level keys are exactly the strings returned by `task_observables`.

Debug sequence:

```python
print(entity.observables.as_dict(fully_qualified=False).keys())
# After env.reset():
print(env.observation_spec().keys())
```

If a key is absent from `TimeStep.observation`, check `enabled` first. Composer silently omits disabled observables by design.

## Physics proxy invalidation

`env.physics` is a weak proxy to the current compiled `mjcf.Physics`. The underlying object is freed when the environment recompiles MJCF or closes. This is intentional: model randomization can create a completely new compiled model.

Avoid this anti-pattern:

```python
physics = env.physics
env.reset()         # May recompile and invalidate the old proxy.
physics.step()      # Can raise ReferenceError.
```

Use this pattern instead:

```python
env.reset()
physics = env.physics  # Fresh proxy for the current compiled model.
```

For task internals, store MJCF element handles on entities and call `physics.bind(element)` after compile/reset rather than storing old bound physics arrays indefinitely.

## Episode initialization retries

Raise `composer.EpisodeInitializationError` from reset-time logic when a sampled initial state is invalid but another sample might succeed. `composer.Environment.reset()` catches this error and retries until `max_reset_attempts` is exhausted.

Use retries for:

- Rejection-sampled object placements.
- Collision-free robot or prop initial states.
- Randomized model variants that occasionally create invalid starts.

Do not use retries to hide deterministic programming errors such as missing joints, invalid action shapes, or impossible MJCF definitions. First make a deterministic fixed initial state pass, then add randomization.

## Action spec mismatches

The default `Task.action_spec(physics)` is derived from MuJoCo actuators:

- `shape` is `(physics.model.nu,)`.
- `minimum` and `maximum` come from MuJoCo actuator control ranges.
- `name` is a tab-separated list of actuator names.

Policy/debug action generator:

```python
spec = env.action_spec()
action = np.zeros(spec.shape, dtype=spec.dtype)
action = np.clip(action, spec.minimum, spec.maximum)
time_step = env.step(action)
```

If your task maps a high-level action to actuators, override both:

1. `action_spec(self, physics)` to describe the high-level action.
2. `before_step(self, physics, action, random_state)` to convert that high-level action into MuJoCo controls.

Call `super().before_step(...)` only when the high-level action is already the actuator control vector.

## Validation escalation

After fixing the immediate error:

1. Run the bundled smoke script.
2. Run your custom environment with `max_reset_attempts=1` and a fixed seed to expose deterministic reset errors.
3. Run with the intended `max_reset_attempts` and randomized seeds to exercise rejection sampling.
4. Print action/observation specs and compare every policy input/output against those specs.
5. Run at least one short episode with zero actions and one with bounded random actions.
6. Only then connect a learner, replay buffer, viewer, or camera-observation pipeline.
