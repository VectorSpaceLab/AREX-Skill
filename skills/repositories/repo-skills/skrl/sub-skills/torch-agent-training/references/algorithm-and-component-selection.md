# Algorithm and component selection

Choose from the public single-agent Torch algorithms below. The model-role
keys are contractual: a key with a `*` is normally needed for training and can
be omitted only for a deliberately reduced evaluation-only instance. The
source implementations retrieve these names from `models` with `.get(...)`,
so a missing training role can surface later as an attribute or optimizer
failure rather than at constructor time.

## Selection matrix

| Algorithm | Use when | Action/observation family | Model dictionary (mixin family) | Memory and distinctive controls |
|---|---|---|---|---|
| **A2C** / `A2C_CFG` | On-policy synchronous actor-critic | Discrete or continuous actions | `policy` (Categorical, MultiCategorical, Gaussian, or MultivariateGaussian); `value` (Deterministic) | Rollout memory; `rollouts`, `gae_lambda`, entropy/value scales; KL scheduler supported |
| **AMP** / `AMP_CFG` | PPO-like adversarial motion-prior imitation | Continuous task and AMP observations | `policy` (Gaussian/MultivariateGaussian); `value` (Deterministic); `discriminator` (Deterministic) | Rollout memory plus `motion_dataset`, `reply_buffer`, and `collect_reference_motions`; AMP batch and discriminator scales |
| **CEM** / `CEM_CFG` | Cross-entropy search over a discrete policy | Discrete actions | `policy` (Categorical or MultiCategorical) | Rollout/episode memory; `rollouts`, `percentile`, and discount factor |
| **DDPG** / `DDPG_CFG` | Deterministic off-policy actor-critic in continuous action spaces | Continuous actions | `policy`, `target_policy`, `critic`, `target_critic` (all Deterministic) | Replay memory; `batch_size`, `gradient_steps`, `learning_starts`, Polyak `polyak`, optional exploration noise |
| **DDQN** / `DDQN_CFG` | Discrete off-policy value learning with double-Q selection | Discrete actions | `q_network`, `target_q_network` (Deterministic) | Replay memory; `batch_size`, `update_interval`, `target_update_interval`, exploration scheduler |
| **DQN** / `DQN_CFG` | Basic discrete deep Q-learning | Discrete actions | `q_network`, `target_q_network` (Deterministic) | Replay memory; same update/batch controls as DDQN |
| **PPO** / `PPO_CFG` | General on-policy clipped policy optimization | Discrete or continuous actions | `policy` (Categorical, MultiCategorical, Gaussian, or MultivariateGaussian); `value` (Deterministic) | Rollout memory; `rollouts`, epochs, mini-batches, ratio/value clipping, optional KL scheduler |
| **Q-learning** / `Q_LEARNING_CFG` | Tabular off-policy Q-learning | Discrete observations and actions | `policy` (Tabular) | No replay buffer is required by the update; one transition is retained internally; learning rate, discount, epsilon behavior from the tabular policy |
| **RPO** / `RPO_CFG` | PPO-like continuous policy with added distribution perturbation | Continuous actions | `policy` (Gaussian/MultivariateGaussian); `value` (Deterministic) | Rollout memory; PPO controls plus `alpha`; KL scheduler supported |
| **SAC** / `SAC_CFG` | Entropy-regularized stochastic off-policy actor-critic | Continuous actions | `policy` (Gaussian/MultivariateGaussian); `critic_1`, `critic_2`, `target_critic_1`, `target_critic_2` (Deterministic) | Replay memory; batch/gradient/learning-start controls, entropy tuning, Polyak update |
| **SARSA** / `SARSA_CFG` | Tabular on-policy temporal-difference learning | Discrete observations and actions | `policy` (Tabular) | No replay buffer is required by the update; one transition is retained internally; on-policy next action drives the update |
| **TD3** / `TD3_CFG` | Delayed, smoothed deterministic off-policy actor-critic | Continuous actions | `policy`, `target_policy`, `critic_1`, `critic_2`, `target_critic_1`, `target_critic_2` (Deterministic) | Replay memory; delayed `policy_delay`, exploration noise, target smoothing noise and clip |
| **TRPO** / `TRPO_CFG` | Trust-region on-policy optimization | Continuous actions | `policy` (Gaussian/MultivariateGaussian); `value` (Deterministic) | Rollout memory; KL constraint, damping, conjugate-gradient and backtrack controls |

`A2C`, `PPO`, `RPO`, and `TRPO` have RNN variants in their Torch packages;
`DDPG`, `SAC`, and `TD3` also expose RNN variants. Recurrent models need the
extra `.get_specification()` and `compute` RNN-state contract described in the
workflow reference. Do not select an RNN variant merely because a model
contains an RNN layer.

## Practical decision tree

1. Is the action space continuous? Start with PPO/RPO/TRPO for on-policy
   learning, or DDPG/TD3/SAC for replay-based learning. Use Gaussian or
   MultivariateGaussian for a stochastic policy, and Deterministic for an
   actor/critic/value output.
2. Is the action space `Discrete` or `MultiDiscrete`? Use Categorical for one
   discrete action and MultiCategorical for `MultiDiscrete`; use PPO/A2C/CEM
   for neural stochastic policies. Use DQN/DDQN for deep value learning.
3. Are both observation and action spaces discrete and small enough for a
   table? Use Q-learning or SARSA with `TabularMixin`; the table is indexed by
   observations and actions and is not an `nn.Linear` substitute.
4. Does the task require reference-motion discrimination? Use AMP only after
   supplying the AMP observation space, motion dataset, reply buffer, and
   reference-motion callback in addition to the normal PPO-like components.
5. Is the caller asking for many agents or a Runner configuration? Stop and
   route to the multi-agent/runner sibling instead of adapting these role
   tables.

## Components by role

### Policy distributions

- **Categorical:** `compute` returns logits by default. The mixin samples an
  integer action and returns a one-column `log_prob`.
- **MultiCategorical:** `compute` returns one concatenated output whose final
  dimension equals the sum of `action_space.nvec`; the mixin splits it and
  returns a vector of discrete actions.
- **Gaussian:** `compute` returns mean actions and `outputs["log_std"]`; use
  `reduction="sum"` unless a different log-probability reduction is required.
  `clip_actions=True` clips sampled actions to a bounded action space; this is
  not a replacement for a correctly scaled mean network.
- **MultivariateGaussian:** same mean/log-standard-deviation contract, with a
  diagonal multivariate normal and a scalar joint log probability.
- **Deterministic:** `compute` returns an action, scalar value, or scalar
  critic. `clip_actions=True` is meaningful for action outputs, not value or
  critic outputs.
- **Tabular:** implement `compute` around a registered table parameter and
  use `tables()` for updates. Q-learning and SARSA retrieve the first table.

Do not use a stochastic mixin for a deterministic critic/value. Do not return a
probability vector from `CategoricalMixin` unless
`unnormalized_log_prob=False`; invalid negative, non-finite, or zero-sum
probabilities will produce invalid distributions.

### Memories

`RandomMemory` is a generic circular buffer whose tensors have shape
`(memory_size, num_envs, data_size)`. `len(memory)` is the valid sample count;
it becomes `memory_size * num_envs` when filled. `replacement=False` samples a
maximum of the available valid entries if the request is too large;
`replacement=True` guarantees the requested batch by allowing repeats.

- On-policy PPO/A2C/RPO/TRPO use the buffer as a rollout store. Align
  `memory_size` and `cfg.rollouts`, and make the mini-batch split compatible
  with the collected sample count.
- Off-policy DDPG/TD3/SAC/DQN/DDQN use it as replay. Set a capacity comfortably
  above `batch_size`, and make `learning_starts` large enough to avoid sampling
  an underfilled buffer. The implementation's sampling behavior still applies
  if the requested batch exceeds valid entries.
- CEM stores complete sampled episodes/rollouts as required by its update.
- AMP also has a motion dataset and reply buffer, which are distinct from the
  task rollout memory.
- Q-learning and SARSA do not need memory for their update; their `memory`
  parameter remains part of the common agent signature for compatibility.

The base memory can optionally `create_tensor(name, size, dtype=...)`,
`add_samples(...)`, `sample(...)`, and `sample_all(...)`. Agent-owned tensor
names and dtypes are visible in the algorithm source; let the agent initialize
them unless you are implementing a compatible custom agent.

### Noises, preprocessors, and schedulers

- `GaussianNoise(mean, std, device=...)` samples independent normal noise.
- `OrnsteinUhlenbeckNoise(theta, sigma, base_scale, mean=0, std=1,
  device=...)` keeps a stateful temporally correlated process; reset/recreate
  it when the exploration episode policy requires a fresh state.
- Deterministic off-policy configs accept `exploration_noise` and
  `exploration_noise_kwargs`; TD3 additionally accepts
  `smooth_regularization_noise`, kwargs, and `smooth_regularization_clip`.
- `RunningStandardScaler(size, epsilon=1e-8, clip_threshold=5.0,
  device=...)` is a stateful `nn.Module`. Attach it through the relevant agent
  `observation_preprocessor`, `state_preprocessor`, or `value_preprocessor`
  fields and pass its constructor kwargs in the paired dictionary. Use
  `value_preprocessor` with `inverse=True` behavior handled by the agent.
- `KLAdaptiveLR` is a Torch `_LRScheduler` with
  `kl_threshold`, `min_lr`, `max_lr`, `kl_factor`, and `lr_factor`. Configure
  its class and kwargs without an optimizer argument; the agent supplies the
  optimizer. It is meaningful for A2C, AMP, PPO, and RPO. On other agents it
  does not change the learning rate according to the source note.

All resources must be on the same resolved device as the tensors they process.
