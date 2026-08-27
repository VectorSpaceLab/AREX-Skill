# Training and policy API reference

This reference distills the checked-in `go1_gym_learn/ppo`,
`go1_gym_learn/ppo_cse`, and history-wrapper APIs. It is a shape and control
contract, not a promise that the Isaac Gym backend is installed.

## ActorCritic and `AC_Args`

Both PPO variants expose an `ActorCritic` and an `AC_Args` class. The checked-in
defaults include:

- `init_noise_std = 1.0`;
- actor and critic hidden layers `[512, 256, 128]`;
- ELU activation;
- `PPO`'s encoder branch is configured with an 18-input/18-latent environment
  factor encoder and a history adaptation branch `[[256, 32]]`;
- `PPO-CSE`'s adaptation hidden layers are `[256, 128]` and its output width is
  `num_privileged_obs`.

The constructor shape is:

```text
ActorCritic(num_obs, num_privileged_obs, num_obs_history, num_actions)
```

The ordinary PPO actor-critic uses the current observation plus the encoded
privileged latent for its actor and critic. Its adaptation module consumes the
flattened history and predicts the same latent width as the configured encoder.
The PPO-CSE/RMA actor-critic consumes the flattened history plus the privileged
representation: the adaptation module maps `num_obs_history` to
`num_privileged_obs`, and the student actor maps their concatenation to
`num_actions`. The PPO-CSE critic uses the history plus the privileged
representation during training. `act_student` is the deployment-side path; it
uses the learned adaptation module rather than privileged observations.

`act` samples from a Normal policy distribution for rollout collection.
`act_student` and `act_teacher` return deterministic actor means. `evaluate`
returns a scalar value per batch element. `get_student_latent` exposes the
PPO-CSE adaptation output. `reset` is currently a no-op and the classes are not
recurrent (`is_recurrent = False`).

### Verified PPO-CSE shape smoke

With the checked-in default `AC_Args`, a CPU-only structural smoke was run as:

```python
model = ActorCritic(70, 2, 2100, 12)
history = torch.zeros(2, 2100)
latent = model.get_student_latent(history)
action = model.act_student(history)
```

The observed contracts were:

```text
latent: (2, 2)
action: (2, 12)
```

This smoke used lightweight import stubs for the absent `ml_logger` and
`params_proto` packages so that only the actor-critic module was exercised. It
did not import Isaac Gym, allocate a simulator, step an environment, train, or
validate numerical policy quality. Re-run it with the repository's pinned
packages when validating a real environment.

## `PPO` and `PPO_Args`

`PPO(actor_critic, device='cpu')` moves the actor-critic to the requested
`device`, creates Adam optimizers, and initializes a transition object. Call
`init_storage(num_envs, num_transitions_per_env, actor_obs_shape,
privileged_obs_shape, obs_history_shape, action_shape)` before learning.

The common checked-in defaults in `PPO_Args` are:

| Field | Value | Meaning |
|---|---:|---|
| `value_loss_coef` | `1.0` | critic loss weight |
| `use_clipped_value_loss` | `True` | clipped value objective |
| `clip_param` | `0.2` | PPO ratio/value clip |
| `entropy_coef` | `0.01` | entropy bonus coefficient |
| `num_learning_epochs` | `5` | passes over each rollout |
| `num_mini_batches` | `4` | rollout partitions per epoch |
| `learning_rate` | `1e-3` | PPO Adam rate |
| `adaptation_module_learning_rate` | `1e-3` | adaptation Adam rate |
| `num_adaptation_module_substeps` | `1` | adaptation updates per minibatch |
| `schedule` | `adaptive` | KL-based learning-rate schedule |
| `gamma` | `0.99` | return discount |
| `lam` | `0.95` | GAE parameter |
| `desired_kl` | `0.01` | adaptive schedule target |
| `max_grad_norm` | `1.0` | gradient clipping |

PPO-CSE additionally has `selective_adaptation_module_loss = False`. During a
step, `act` records action distribution statistics and pre-step observations;
`process_env_step` records rewards/dones and time-out bootstrapping; then
`compute_returns` applies GAE and `update` performs clipped PPO and adaptation
loss updates. The CSE implementation also reports adaptation train/test loss
fields and returns a longer metrics tuple.

## `Runner` and `RunnerArgs`

`Runner(env, device='cpu')` constructs the variant's actor-critic from the
environment's `num_obs`, `num_privileged_obs`, `num_obs_history`, and
`num_actions`, creates storage for `env.num_train_envs`, and resets the
environment. `get_inference_policy()` returns `act_inference`;
`get_expert_policy()` returns `act_expert`.

The PPO and PPO-CSE runner classes live in their package `__init__.py` files.
Their common `RunnerArgs` values are:

```text
num_steps_per_env = 24
max_iterations = 1500
save_interval = 400
save_video_interval = 100
log_freq = 10
resume = False
load_run = -1
checkpoint = -1
resume_path = None
```

The CSE/RMA variant also has `algorithm_class_name = 'RMA'` and
`resume_curriculum = True`; the ordinary PPO variant uses
`algorithm_class_name = 'PPO'`. `max_iterations` is a declared default, while
`scripts/train.py` explicitly calls `learn(num_learning_iterations=100000, ...)`;
do not confuse the two values.

`learn` collects `num_steps_per_env` transitions, computes returns, updates the
algorithm, logs metrics, optionally records videos, and periodically saves
artifacts. It asserts `logger.prefix` before starting because an empty prefix
would overwrite the entire instrument server. See
[training-workflow.md](training-workflow.md) for the safe boundary around this
method.

## `RolloutStorage`

`RolloutStorage(num_envs, num_transitions_per_env, obs_shape,
privileged_obs_shape, obs_history_shape, actions_shape, device='cpu')` allocates
all core tensors with leading shape `[T, N, ...]`, where `T` is
`num_transitions_per_env` and `N` is `num_envs`:

- `observations`: `[T, N, *obs_shape]`;
- `privileged_observations`: `[T, N, *privileged_obs_shape]`;
- `observation_histories`: `[T, N, *obs_history_shape]`;
- `actions`: `[T, N, *actions_shape]`;
- `rewards`, `values`, `returns`, `advantages`, and log probabilities:
  `[T, N, 1]`;
- `dones`: `[T, N, 1]` byte tensor;
- `mu` and `sigma`: `[T, N, *actions_shape]`;
- `env_bins`: `[T, N, 1]`.

`Transition` is the per-step staging object. `add_transitions` raises
`AssertionError("Rollout buffer overflow")` when the fixed horizon is full.
`compute_returns(last_values, gamma, lam)` walks backward with terminal masks,
bootstraps the last value, and normalizes advantages. The standard minibatch
generator flattens the first two axes, discards any remainder when the total is
not divisible by the requested number of minibatches, and yields shuffled
batches for each epoch. The recurrent generator exists for compatibility, but
these actor-critic classes are non-recurrent.

## `HistoryWrapper`

Both `go1_gym/envs/wrappers/history_wrapper.py` and
`go1_gym_deploy/envs/history_wrapper.py` implement the same core contract:

```text
obs_history_length = cfg.env.num_observation_history
num_obs_history = obs_history_length * env.num_obs
obs_history.shape = (env.num_envs, num_obs_history)

For the training recipe, `30 * 70 = 2100`; do not confuse the frame count
(`num_observation_history`) with the flattened history width (`num_obs_history`).
```

`step(action)` gets `privileged_obs` from `info["privileged_obs"]`, drops the
oldest `env.num_obs` values, appends the current observation, and returns:

```python
{
    "obs": obs,
    "privileged_obs": privileged_obs,
    "obs_history": obs_history,
}, rew, done, info
```

`get_observations` performs the same append; `reset` zeros the whole history;
`reset_idx` zeros only selected environments. The deployment wrapper also
forwards unknown attributes to its wrapped environment and supports `get_obs`.
The simulation wrapper subclasses `gym.Wrapper` and imports Isaac Gym at module
load time, so it is not a CPU inspection dependency.
