# Algorithm and component selection

Choose the algorithm from the environment action space and learning pattern,
then build exactly the model dictionary it expects. The model keys below are
public contract keys from the JAX agent documentation and maintained JAX tests;
they are not arbitrary names.

## Decision table

| Algorithm | Learning pattern | Action-space fit | Required model keys | Model kinds |
|---|---|---|---|---|
| A2C | on-policy actor-critic | `Discrete`, `MultiDiscrete`, or bounded continuous `Box` | `policy`, `value` | stochastic policy (`CategoricalMixin`, `MultiCategoricalMixin`, or `GaussianMixin`); deterministic value |
| CEM | policy search | `Discrete` or `MultiDiscrete` | `policy` | `CategoricalMixin` or `MultiCategoricalMixin` |
| DDPG | off-policy deterministic actor-critic | continuous `Box` | `policy`, `target_policy`, `critic`, `target_critic` | four `DeterministicMixin` models; critic consumes observations and taken actions |
| DDQN | off-policy discrete Q-learning | `Discrete` | `q_network`, `target_q_network` | two deterministic Q models returning action values |
| DQN | off-policy discrete Q-learning | `Discrete` | `q_network`, `target_q_network` | two deterministic Q models returning action values |
| PPO | on-policy clipped actor-critic | `Discrete`, `MultiDiscrete`, or bounded continuous `Box` | `policy`, `value` | stochastic policy plus deterministic value |
| RPO | on-policy robust actor-critic | continuous `Box` in the JAX implementation/tests | `policy`, `value` | `GaussianMixin` policy plus deterministic value |
| SAC | off-policy stochastic actor-critic | continuous `Box` | `policy`, `critic_1`, `target_critic_1`, `critic_2`, `target_critic_2` | `GaussianMixin` policy plus four deterministic critics |
| TD3 | off-policy deterministic twin-critic actor-critic | continuous `Box` | `policy`, `target_policy`, `critic_1`, `target_critic_1`, `critic_2`, `target_critic_2` | six deterministic actor/critic models |

A2C/PPO/RPO policies consume observations and return actions; their value model
normally consumes observations (or states in an asymmetric environment) and
returns one value. DDPG/SAC/TD3 target models must be separately initialized;
the agent updates target parameters internally. DQN/DDQN Q models consume an
observation and return one value per discrete action, even though the public
helper uses `deterministic_model`. The JAX tests are useful role/key fixtures:
each test constructs the required dictionary before instantiating its agent.

CEM is discrete in the public JAX implementation: do not route a continuous
Pendulum action space to it. The maintained JAX CEM example uses CartPole.
DDPG, SAC, and TD3 are continuous-action algorithms; do not repair a discrete
action error by swapping a Gaussian policy into a Q-learning agent.

## Configuration highlights

All configurations inherit the nested `experiment` settings. These are the
high-value fields; inspect the installed signature for the complete dataclass
when changing less common options.

| Configuration | First fields to set | Component-specific choices |
|---|---|---|
| `A2C_CFG` | `rollouts`, `mini_batches`, `discount_factor`, `gae_lambda`, `learning_rate` | optional observation/state/value preprocessors and scheduler |
| `CEM_CFG` | `rollouts`, `percentile`, `discount_factor`, `learning_rate` | policy search; no value model |
| `DDPG_CFG` | `gradient_steps`, `batch_size`, `discount_factor`, `polyak`, `learning_rate` | `exploration_noise`/kwargs and optional exploration scheduler |
| `DDQN_CFG` / `DQN_CFG` | `gradient_steps`, `batch_size`, `discount_factor`, `target_update_interval` | discrete exploration scheduler and optional update interval |
| `PPO_CFG` | `rollouts`, `learning_epochs`, `mini_batches`, `discount_factor`, `gae_lambda`, `ratio_clip`, `value_clip` | `learning_rate`, KL scheduler, preprocessors, entropy/value scales |
| `RPO_CFG` | PPO fields plus `alpha` | continuous robust-policy noise/regularization parameter |
| `SAC_CFG` | `gradient_steps`, `batch_size`, `discount_factor`, `polyak` | three learning rates may be supplied, entropy learning and target entropy |
| `TD3_CFG` | `gradient_steps`, `batch_size`, `discount_factor`, `polyak`, `policy_delay` | exploration noise, smoothing noise/clip, schedulers |

For PPO, `rollouts` should match the rollout memory's first dimension for the
usual one-to-one construction. `mini_batches` controls `RandomMemory.sample`;
start with a small divisor of the available rollout samples. For off-policy
agents, choose a replay memory large enough for `batch_size` and set
`learning_starts` so an update is not requested before useful samples exist.
The exact update scheduling remains algorithm-specific; this branch does not
infer a safe training budget from defaults.

## Model choices and output shapes

### Stochastic policies

- `GaussianMixin`: network output is the mean action and the auxiliary output
  must contain `log_std`. The mixin adds sampled actions, log probability, mean
  actions, and standard deviation. `reduction="sum"` (default) returns one
  reduced log probability per sample; use `"none"` only if the agent contract
  supports per-action values.
- `CategoricalMixin`: return unnormalized logits by default, with final width
  equal to the number of discrete actions. Set `unnormalized_log_prob=False`
  only when the network returns valid non-negative probabilities with a nonzero
  finite sum.
- `MultiCategoricalMixin`: final width is the occupied sum of the
  `MultiDiscrete.nvec` components. It splits that output into one categorical
  distribution per component and applies the selected log-probability
  reduction. It is not interchangeable with a single `CategoricalMixin` for a
  `MultiDiscrete` action space.

### Deterministic critics and Q models

A deterministic model returns `(value_or_action, extra_dict)`. A value critic
returns `(batch, 1)`. An action-value model returns the shape expected by its
algorithm; DQN/DDQN use one output per discrete action. A continuous critic
usually concatenates observation and `taken_actions` before the final scalar.
The input key is `"taken_actions"`, not `"actions"`, in the public model
contract. If a target model is a copy, initialize it with the same input shape
and architecture before the agent's target update logic runs.

## Factory/model-instantiator route

For a standard MLP, use the public JAX factories instead of writing a Flax
class:

```python
from skrl.utils.model_instantiators.jax import (
    categorical_model, deterministic_model, gaussian_model,
    multicategorical_model,
)

policy = gaussian_model(
    observation_space=env.observation_space,
    state_space=env.state_space,
    action_space=env.action_space,
    device=env.device,
    network=[{"name": "net", "input": "OBSERVATIONS",
              "layers": [64, 64], "activations": "relu"}],
    output="ACTIONS",
)
value = deterministic_model(
    observation_space=env.observation_space,
    state_space=env.state_space,
    action_space=env.action_space,
    device=env.device,
    network=[{"name": "net", "input": "OBSERVATIONS",
              "layers": [64, 64], "activations": "relu"}],
    output="ONE",
)
policy.init_state_dict(role="policy")
value.init_state_dict(role="value")
```

Use `input="STATES"` for an asymmetric value network, and use
`input="ACTIONS"` for a critic network that is conditioned on taken actions.
The factory accepts `return_source=True` when a caller needs to inspect the
constructed source, but do not execute generated source merely to choose a
model. Its network token grammar is public and tested for activations, linear,
convolution, flatten, and space/input substitutions.

Factories return initialized *model objects only after the caller still calls
`init_state_dict`*. `output="ACTIONS"`/`"ONE"` controls the generated final
shape; it does not waive the JAX state initialization requirement. If a custom
architecture has nonstandard inputs, prefer an explicit Flax class so the
role and output contract remain readable.

## Memory/resource pairings

| Need | JAX component | Typical algorithms |
|---|---|---|
| fixed rollout buffer | `RandomMemory(memory_size=rollouts, num_envs=env.num_envs, device=env.device)` | A2C, PPO, RPO, CEM |
| random replay batches | `RandomMemory(memory_size=..., replacement=...)` | DDPG, DDQN, DQN, SAC, TD3 |
| normalize observations/states/values | `RunningStandardScaler` in the matching cfg fields | A2C, PPO, RPO, CEM and optional off-policy configs |
| adaptive PPO learning rate | `KLAdaptiveLR` in `learning_rate_scheduler` | A2C/PPO/RPO; use the agent's supported scheduler fields |
| deterministic actor exploration | JAX `GaussianNoise` or `OrnsteinUhlenbeckNoise` | DDPG, TD3 |
| Adam updates | `skrl.resources.optimizers.jax.Adam` | used internally by JAX agents; useful for custom update code |

The resource class must come from the JAX namespace. A similarly named Torch
resource may import successfully in an all-framework environment but will not
be a valid JAX parameter/update object.

## Evidence anchors

- `[A2C]`, `[CEM]`, `[DDPG]`, `[DDQN]`, `[DQN]`, `[PPO]`, `[RPO]`, `[SAC]`, and
  `[TD3]`: public JAX agent documentation, `*_CFG` APIs, and corresponding
  JAX test fixtures.
- `[Models]`: public model documentation and JAX model-instantiator tests.
- `[Example]`: JAX Gymnasium CartPole CEM, CartPole DQN, Pendulum DDPG/PPO/SAC/
  TD3 construction examples.
- `[Resources]`: public JAX memory, noise, optimizer, preprocessor, and
  scheduler APIs.
