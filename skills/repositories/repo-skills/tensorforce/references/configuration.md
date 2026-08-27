# Cross-Cutting Configuration Notes

## State and action specs

Tensorforce value specs use dictionaries:

```python
states = dict(type='float', shape=(8,), min_value=-1.0, max_value=1.0)
actions = dict(type='int', shape=(), num_values=4)
```

Nested state/action spaces add one dictionary layer:

```python
states = dict(
    observation=dict(type='float', shape=(16, 16, 3), min_value=0.0, max_value=1.0),
    attributes=dict(type='int', shape=(4,), num_values=5),
)
actions = dict(move=dict(type='int', shape=(), num_values=3))
```

Prefer passing `environment=environment` into `Agent.create(...)` so Tensorforce infers these specs. Use explicit specs only when there is no environment object yet.

## Agent and environment specs

Most Tensorforce factories accept dicts, JSON files from the user's project, registered keywords, classes/objects, or import paths. Do not rely on benchmark configs from a source checkout; copy the needed dict into the user's experiment.

```python
environment = dict(environment='custom_cartpole')
agent = dict(
    agent='ppo',
    network='auto',
    batch_size=10,
    update_frequency=2,
    learning_rate=3e-4,
    multi_step=10,
    discount=0.99,
)
```

For deep module configuration, use [modules-and-configuration](../sub-skills/modules-and-configuration/SKILL.md).

## Tensorforce config dictionary

Common `config` fields seen in source/tests include:

```python
config = dict(
    device='CPU',
    eager_mode=True,
    seed=7,
    create_debug_assertions=True,
    tf_log_level=40,
)
```

Use `device='CPU'` for deterministic smoke checks. Do not claim GPU behavior unless the user's TensorFlow build and device smoke pass.

## Validation pattern

Before a long run:

1. import Tensorforce;
2. instantiate environment and print `states()`/`actions()`;
3. create a cheap `random` or tiny `ppo` agent;
4. run one reset/action/execute/observe cycle;
5. only then increase episodes, parallelism, logging, or optional adapters.
