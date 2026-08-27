# Observables, buffering, and variation reference

Use this reference when a Composer task needs custom observations, delayed/buffered observations, observable corruption, per-episode randomization, or reproducible variation patterns.

## Observable families

Public observable constructors commonly used in Composer tasks:

| Constructor | Use |
|---|---|
| `observable.Generic(callable, ...)` | Wrap an arbitrary callable that accepts `physics` and returns an array-like value. Good for task-level metrics, distances, rewards-as-observations, and small custom sensors. |
| `observable.MJCFFeature(kind, mjcf_element, ...)` | Observe an attribute through `physics.bind(mjcf_element)`, for example joint `qpos`, joint `qvel`, geom `xpos`, or sensor `sensordata`. Accepts an element or iterable of elements and optional indexing. |
| `observable.MujocoFeature(kind, feature_name, ...)` | Observe a named MuJoCo data field via `physics.named.data.<kind>[feature_name]`. Useful when you have stable compiled names rather than MJCF elements. |
| `observable.MJCFCamera(camera_element, ...)` | Render from an MJCF `<camera>` element; route backend errors to the rendering sub-skill. Supports RGB, depth, or segmentation. |
| `observable.MujocoCamera(camera_name, ...)` | Render from a named MuJoCo camera; route backend errors to the rendering sub-skill. |

`MJCFCamera` and `MujocoCamera` are not CPU-only observations because they call `physics.render(...)`.

## Defining entity observables

Entity observables belong in a `composer.Observables` subclass:

```python
class DemoObservables(composer.Observables):
    def __init__(self, entity):
        super().__init__(entity)
        self.enable_all()  # Optional; individual observables can be enabled too.

    @composer.observable
    def joint_position(self):
        return observable.MJCFFeature("qpos", self._entity.joint)
```

Rules:

- Decorated methods are sorted by name, evaluated once during entity construction, and cached.
- `self._entity` is a weak proxy to the entity. Do not hold a long-lived separate physics reference inside observables.
- Return observable objects, not raw arrays. The raw observation is produced later from compiled physics.
- Enable only observations the agent should receive. Disabled observables remain configurable but are omitted from `env.observation_spec()` and `TimeStep.observation`.
- For constructor-time configuration, pass `observable_options` to the entity: `MyEntity(observable_options={"joint_position": {"enabled": True}})`.

## Configuring enabled observations

Observable options:

| Option | Meaning | Default in updater when unset |
|---|---|---|
| `enabled` | Whether this observable appears in environment observations. | `False` on construction. |
| `update_interval` | Number of physics substeps between produced samples. Can be an int or variation/callable. | `1` |
| `buffer_size` | Number of arrived samples returned. | `1` |
| `delay` | Number of physics substeps between sample production and delivery. Can be int or variation/callable. | `0` |
| `aggregator` | `None`, one of `min`, `max`, `mean`, `median`, `sum`, or a callable reducing over the first buffer axis. | `None` |
| `corruptor` | Callable `corruptor(value, random_state=...)` applied before buffering. | `None` |

Configuration examples:

```python
# Apply to all observables on the entity.
entity.observables.set_options({
    "enabled": True,
    "buffer_size": 3,
    "delay": 1,
})

# Per-observable options use unqualified method names.
entity.observables.set_options({
    "joint_position": {"enabled": True, "buffer_size": 2},
    "joint_velocity": {"enabled": True, "aggregator": "mean"},
})
```

If `set_options` reports `No observable with name ...`, list valid configuration keys with `entity.observables.as_dict(fully_qualified=False)`.

## Buffering, delay, and shapes

Composer's observation updater keeps per-observable buffers and schedules updates over physics substeps.

- Without an aggregator, observations include a leading buffer dimension unless `strip_singleton_obs_buffer_dim=True` and `buffer_size == 1`.
- With `buffer_size=3`, the returned array contains the three most recent arrived observations, padded on the left when not enough samples have arrived.
- With `delay > 0`, an observation produced at physics substep `t` is delivered at `t + delay`; out-of-order arrivals are handled by arrival time.
- Initial delayed-buffer padding is selected by `composer.Environment(delayed_observation_padding=...)`:
  - `composer.ObservationPadding.ZERO`: pad missing values with zeros.
  - `composer.ObservationPadding.INITIAL_VALUE`: pad with the first observed value.
- `strip_singleton_obs_buffer_dim=True` affects only `buffer_size == 1`; larger buffers keep their leading dimension.
- If an observable has no `array_spec`, the updater infers shape/dtype by calling it once during reset/compile setup. Keep raw callables cheap and deterministic in shape.

Spec consequences:

- `aggregator=None` preserves a provided custom `array_spec` type when possible, updating only shape/name.
- Aggregators reduce the first buffer axis. Built-in `min`, `max`, `mean`, and `median` are bounds-preserving; built-in `sum` is not.
- If a custom aggregator preserves bounds, set `my_aggregator.preserves_bounds = True`; otherwise a bounded spec may become an unbounded `Array` spec.
- Invalid aggregator names raise `KeyError` with the valid names.

## Observable keys and qualification

There are two names to track:

1. **Configuration name:** the unqualified decorated method name, such as `joint_position`. Use this for `set_options`.
2. **Environment observation key:** the key in `env.observation_spec()` and `TimeStep.observation`. Entity-bound observables are returned by `Observables.as_dict(fully_qualified=True)` inside `Task.observables`.

Qualification behavior:

- Root entity observables may appear as plain keys when the root model has no non-empty full identifier.
- Observables on attached entities are prefixed by their `mjcf_model.full_identifier`, for example `arm/joint_positions` or `arena/gripper/touch`.
- Task-level observables from `Task.task_observables` are never auto-prefixed; choose task keys that cannot collide with entity keys.
- Inspect `env.observation_spec()` after `env.reset()` before wiring a policy or replay buffer.

## Task-level observables

Use `Task.task_observables` for derived quantities not owned by one entity:

```python
class ReachTask(composer.Task):
    @property
    def task_observables(self):
        distance = observable.Generic(lambda physics: self._target_distance(physics))
        distance.enabled = True
        return {"target_distance": distance}
```

If `task_observables` constructs new observable objects each time it is accessed, settings and identity can change unexpectedly. Prefer creating stable enabled observable objects during task initialization and returning the same ordered mapping.

## Variation API basics

A `variation.Variation` is a callable with signature:

```python
variation_value(initial_value=None, current_value=None, random_state=None)
```

Use `dm_control.composer.variation.evaluate(structure, ...)` to evaluate a nested structure of constants, callables, and variations. Variations support arithmetic operators (`+`, `-`, `*`, `/`, `//`, `**`), unary negation, and item selection, so variations can be combined without writing new classes.

Use the environment-provided `random_state` inside hooks for reproducible randomization.

## Distribution and noise helpers

Import helper submodules explicitly:

```python
from dm_control.composer import variation
from dm_control.composer.variation import deterministic, distributions, noises
from dm_control.composer.variation import variation_broadcaster
```

Common helper modules:

| Helper | What it provides |
|---|---|
| `deterministic.Constant(value)` | A fixed value wrapped as a variation, useful in tests and for uniform APIs. |
| `deterministic.Sequence(values)` | Cycles through a fixed sequence; each element can itself be a variation or callable. Stateful. |
| `deterministic.Identity()` | Returns `current_value`. |
| `distributions.Uniform(low, high)` | Uniform real samples; defaults to the shape of `initial_value` unless `single_sample=True`. |
| `distributions.UniformInteger(low, high)` | Integer samples from `RandomState.randint`. |
| `distributions.UniformChoice(choices)` | Random choice from a sequence. |
| `distributions.UniformPointOnSphere()` | Unit 3D direction samples. |
| `distributions.Normal`, `LogNormal`, `Exponential`, `Poisson`, `Bernoulli` | Standard statistical distributions following the same shape/random-state pattern. |
| `distributions.BiasedRandomWalk(stdev, timescale)` | Stateful Ornstein-Uhlenbeck-style noise. Rejects negative `stdev` or `timescale`. |
| `noises.Additive(variation, cumulative=False)` | Adds a sampled amount to the initial value, or to the current value in cumulative mode. |
| `noises.Multiplicative(variation, cumulative=False)` | Multiplies the initial/current value by a sampled amount. |
| `variation_broadcaster.VariationBroadcaster(wrapped)` | Produces proxies that share the same sampled value across multiple callers in each broadcast round. |

Reproducibility notes:

- `Distribution.__call__` uses the supplied `random_state`; if none is supplied, it falls back to global NumPy randomness. Always pass the hook/environment RNG in tasks.
- `Sequence` and `BiasedRandomWalk` are stateful. Recreate or reset them deliberately if repeated experiments need identical sequences from the beginning.
- `VariationBroadcaster` is useful when several MJCF attributes must receive the same random draw, but each proxy should be called once per intended round.

## Applying variation to MJCF and physics

`variation.MJCFVariator` applies variations to MJCF element attributes before compilation:

```python
from dm_control.composer import variation
from dm_control.composer.variation import distributions

self._mjcf_variator = variation.MJCFVariator()
self._mjcf_variator.bind_attributes(
    self._box_geom,
    rgba=distributions.Uniform(low=[0.2, 0.2, 0.2, 1.0], high=[1.0, 1.0, 1.0, 1.0]),
)

def initialize_episode_mjcf(self, random_state):
    self._mjcf_variator.apply_variations(random_state)
```

`variation.PhysicsVariator` applies variations to compiled `physics.bind(element)` attributes after compilation:

```python
self._physics_variator = variation.PhysicsVariator()
self._physics_variator.bind_attributes(self._joint, qpos=distributions.Uniform(-0.1, 0.1))

def initialize_episode(self, physics, random_state):
    self._physics_variator.apply_variations(physics, random_state)
```

Variator behavior:

- The first application remembers an initial value for each bound attribute and passes it to later variation calls.
- `reset_initial_values()` discards remembered baselines so the next application uses the current value as the new baseline.
- `clear()` removes all bound variations.
- Passing `None` for a bound attribute removes that attribute's variation.
- Use `MJCFVariator` in `initialize_episode_mjcf` and `PhysicsVariator` in `initialize_episode` unless you have a deliberate reason to do otherwise.

## Validation patterns for observables and variation

Before training:

1. Enable exactly the observables the agent should receive.
2. Run `env.reset()` and print both `env.observation_spec()` and `time_step.observation` keys.
3. Check every configured observable name against `as_dict(fully_qualified=False)` and every policy input key against the environment observation spec.
4. For buffers/delays, verify actual shapes and initial padding for at least one reset and two control steps.
5. For variations, run two environments with the same seed and confirm deterministic equality for intended values; run a different seed and confirm intended diversity.
6. For MJCF variations that change model structure or compile-time attributes, keep `recompile_mjcf_every_episode=True` until the behavior is proven.
7. For camera observables, validate the rendering backend in a separate fresh process before treating observation failures as Composer logic bugs.
