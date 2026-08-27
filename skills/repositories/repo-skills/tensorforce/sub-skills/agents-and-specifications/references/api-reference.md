# Agent API Reference

## Purpose

Use this reference to select Tensorforce agent factory forms, algorithm aliases, and the exact public signatures needed by `Agent.create`, `Agent.load`, and low-level interaction methods. The facts below are distilled from Tensorforce 0.6.5 source, public docs, examples, tests, and installed-package signature inspection.

## Public import

```python
from tensorforce import Agent
# equivalent package-local import:
from tensorforce.agents import Agent
```

The root package also exports `Environment`, `Runner`, and `TensorforceError`.

## Verified public signatures

```python
Agent.create(agent='tensorforce', environment=None, **kwargs)
Agent.load(directory=None, filename=None, format=None, environment=None, **kwargs)
Agent.__init__(states, actions, max_episode_timesteps=None, parallel_interactions=1,
               config=None, recorder=None)

agent.initial_internals()
agent.act(states, internals=None, parallel=0, independent=False, deterministic=True)
agent.observe(reward=0.0, terminal=False, parallel=0)
agent.experience(states, actions, terminal, reward, internals=None)
agent.update(query=None, **kwargs)
agent.get_specification()
agent.get_architecture()
agent.close()
```

`experience()` and `update()` are implemented by Tensorforce learning agents, not by every utility wrapper. `save`, `restore`, and full checkpoint/export details are owned by `../persistence-export-and-recording/`, but `Agent.load(...)` is summarized here because construction arguments and environment inference matter when loading.

## `Agent.create(...)` accepted `agent` forms

| Form | Use when | Notes |
|---|---|---|
| Alias string, for example `agent='ppo'` | You want a built-in algorithm. | Alias must be one of the registry names below. |
| Dictionary spec, for example `agent=dict(agent='ppo', batch_size=10)` | You want a self-contained in-memory spec. | The key can be `agent` or `type`; extra `kwargs` override/extend the dictionary. |
| JSON spec path | The user has their own agent JSON file. | The path is read by Tensorforce at runtime; do not depend on any original repository config file. |
| Agent class | You have a subclass of `tensorforce.Agent`. | `environment` can still infer `states`, `actions`, and `max_episode_timesteps`. |
| Agent object | You already created or restored an agent-like Recorder object. | `Agent.create` initializes or resets it and checks compatible kwargs. |
| Callable act function | You want a recording wrapper around a state-to-action callable. | A `recorder` argument is required. |
| Module path string | You expose an Agent subclass from an importable module. | Tensorforce imports and validates it as an Agent class. |

Recommended baseline:

```python
agent = Agent.create(
    agent='ppo',
    environment=environment,
    batch_size=10,
    network=dict(type='auto', size=32, depth=1),
    config=dict(device='CPU', seed=7)
)
```

If no `environment` object is available, pass `states`, `actions`, and any required `max_episode_timesteps` explicitly.

## Built-in agent aliases

Registry names verified from the installed package:

```text
a2c, ac, constant, ddpg, ddqn, default, double_dqn, dpg, dqn,
dueling_dqn, ppo, random, recorder, reinforce, tensorforce, trpo, vpg
```

| Alias(es) | Class family | Required arguments beyond `states`/`actions` | Best-fit use |
|---|---|---|---|
| `random` | `RandomAgent` | none | API smoke tests, random baselines, action-mask validation. |
| `constant` | `ConstantAgent` | none; `action_values` optional | Fixed-action baselines and deterministic debug cases. |
| `tensorforce`, `default` | Generic `TensorforceAgent` | `update`, `optimizer`, `objective`, `reward_estimation` | Advanced custom policy/objective/memory setups. Route module details to `../modules-and-configuration/`. |
| `ppo` | `ProximalPolicyOptimization` | `max_episode_timesteps`, `batch_size` | Common on-policy default for discrete or continuous tasks. `environment` can supply `max_episode_timesteps` if the environment defines it. |
| `trpo` | `TrustRegionPolicyOptimization` | `max_episode_timesteps`, `batch_size` | TRPO-style on-policy experiments. |
| `vpg`, `reinforce` | `VanillaPolicyGradient` | `max_episode_timesteps`, `batch_size` | Vanilla policy-gradient experiments. |
| `a2c` | `AdvantageActorCritic` | `batch_size` | Advantage actor-critic recipes. |
| `ac` | `ActorCritic` | `batch_size` | Actor-critic recipes. |
| `dqn` | `DeepQNetwork` | `memory`, `batch_size` | Discrete integer-action Q-learning. |
| `ddqn`, `double_dqn` | `DoubleDQN` | `memory`, `batch_size` | Double-DQN variants for discrete integer actions. |
| `dueling_dqn` | `DuelingDQN` | `memory`, `batch_size` | Dueling DQN for discrete integer actions. |
| `dpg`, `ddpg` | `DeterministicPolicyGradient` | `memory`, `batch_size` | Deterministic policy-gradient workflows, typically continuous actions. |
| `recorder` | `Recorder` wrapper | recorder/callable-specific setup | Use the persistence/recording sibling for full recorder/pretraining workflows. |

All learning aliases also accept common options such as `network`, `learning_rate`, `discount`, preprocessing, exploration, regularization, `parallel_interactions`, `config`, `saver`, `summarizer`, `tracking`, and `recorder` where supported by the class. Keep deep module dictionaries in the modules/configuration route.

## Selected constructor signatures

These are the compact signatures most often needed to diagnose missing required arguments:

```python
RandomAgent(states, actions, max_episode_timesteps=None, config=None, recorder=None)
ConstantAgent(states, actions, max_episode_timesteps=None, action_values=None,
              config=None, recorder=None)

TensorforceAgent(states, actions, update, optimizer, objective, reward_estimation,
                 max_episode_timesteps=None, policy='auto', memory=None,
                 baseline=None, baseline_optimizer=None, baseline_objective=None,
                 l2_regularization=0.0, entropy_regularization=0.0,
                 state_preprocessing='linear_normalization', exploration=0.0,
                 variable_noise=0.0, parallel_interactions=1, config=None,
                 saver=None, summarizer=None, tracking=None, recorder=None, **kwargs)

ProximalPolicyOptimization(states, actions, max_episode_timesteps, batch_size,
                           network='auto', use_beta_distribution=False,
                           memory='minimum', update_frequency=1.0,
                           learning_rate=0.001, multi_step=10,
                           subsampling_fraction=0.33,
                           likelihood_ratio_clipping=0.25, discount=0.99,
                           reward_processing=None, return_processing=None,
                           advantage_processing=None, predict_terminal_values=False,
                           baseline=None, baseline_optimizer=None,
                           state_preprocessing='linear_normalization', exploration=0.0,
                           variable_noise=0.0, l2_regularization=0.0,
                           entropy_regularization=0.0, parallel_interactions=1,
                           config=None, saver=None, summarizer=None, tracking=None,
                           recorder=None, **kwargs)

DeepQNetwork(states, actions, memory, batch_size, max_episode_timesteps=None,
             network='auto', update_frequency=0.25, start_updating=None,
             learning_rate=0.001, huber_loss=None, horizon=1, discount=0.99,
             reward_processing=None, return_processing=None,
             predict_terminal_values=False, target_update_weight=1.0,
             target_sync_frequency=1, state_preprocessing='linear_normalization',
             exploration=0.0, variable_noise=0.0, l2_regularization=0.0,
             entropy_regularization=0.0, parallel_interactions=1, config=None,
             saver=None, summarizer=None, tracking=None, recorder=None, **kwargs)
```

`DoubleDQN` and `DuelingDQN` follow the DQN-style required arguments. `A2C` and `AC` require `batch_size`; `TRPO` and `VPG` require `max_episode_timesteps` and `batch_size`; `DPG/DDPG` require `memory` and `batch_size`.

## State/action value specification

Primitive value specs use:

```python
dict(type='bool', shape=...)
dict(type='int', shape=..., num_values=...)
dict(type='float', shape=..., min_value=..., max_value=...)
```

- `shape` can be scalar `()`/omitted for scalar actions, an integer, or a tuple/list of dimensions.
- `num_values` is required for discrete integer values.
- `min_value` and `max_value` are optional for floats but useful for bounded continuous actions.
- A singleton state/action is represented by a single primitive dict. Multi-component states/actions add one dictionary layer around named primitive specs.

Example multi-component spec:

```python
states = dict(
    observation=dict(type='float', shape=(16, 16, 3)),
    attributes=dict(type='int', shape=(4, 2), num_values=5)
)
actions = dict(
    move=dict(type='int', shape=(), num_values=3),
    throttle=dict(type='float', shape=(1,), min_value=0.0, max_value=1.0)
)
```

## `Agent.load(...)` construction behavior

Use:

```python
agent = Agent.load(directory='checkpoints', filename='agent', format='checkpoint',
                   environment=environment)
```

Operational notes:

- If `directory` contains an agent JSON spec matching `filename`, Tensorforce reads it and then applies allowed overrides from `kwargs`.
- Passing `environment` is recommended when the saved JSON does not contain enough environment-related information; it can supply `states`, `actions`, and `max_episode_timesteps`.
- If a checkpoint spec is incomplete or contains non-JSON-serializable Python objects, pass the missing constructor kwargs explicitly to `Agent.load`.
- `parallel_interactions` can be increased through `kwargs` when loading for parallel workflows.
- Checkpoint, NumPy/HDF5, and SavedModel format decisions belong to `../persistence-export-and-recording/`.

## Interaction return conventions

- Singleton action specs usually return a scalar/array action directly.
- Multi-action specs return an ordered dict keyed by action name.
- `agent.act(..., independent=True)` returns only actions when `internals` is omitted. If an `internals` argument is supplied, it returns `(actions, next_internals)`.
- `agent.observe(...)` returns the number of updates performed by that observe call.
- `terminal` accepts `False`/`0` for non-terminal, `True`/`1` for true terminal, and `2` for an aborted/time-limit terminal.
