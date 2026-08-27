# Model Components API Reference

This reference covers the core importable Python components used by the A2C, PPO, and ACKTR implementations. It is intended for direct API use and safe modification; use the training-workflows sub-skill for full CLI runs.

## Imports

```python
from a2c_ppo_acktr.model import Policy, CNNBase, MLPBase
from a2c_ppo_acktr.storage import RolloutStorage
from a2c_ppo_acktr.algo.a2c_acktr import A2C_ACKTR
from a2c_ppo_acktr.algo.ppo import PPO
from a2c_ppo_acktr.algo.kfac import KFACOptimizer
from a2c_ppo_acktr import distributions, utils
```

## Verified Constructor Signatures

These signatures were verified against the installed package and source snapshot:

```text
Policy(obs_shape, action_space, base=None, base_kwargs=None)
CNNBase(num_inputs, recurrent=False, hidden_size=512)
MLPBase(num_inputs, recurrent=False, hidden_size=64)
RolloutStorage(num_steps, num_processes, obs_shape, action_space, recurrent_hidden_state_size)
A2C_ACKTR(actor_critic, value_loss_coef, entropy_coef, lr=None, eps=None, alpha=None, max_grad_norm=None, acktr=False)
PPO(actor_critic, clip_param, ppo_epoch, num_mini_batch, value_loss_coef, entropy_coef, lr=None, eps=None, max_grad_norm=None, use_clipped_value_loss=True)
KFACOptimizer(model, lr=0.25, momentum=0.9, stat_decay=0.99, kl_clip=0.001, damping=0.01, weight_decay=0, fast_cnn=False, Ts=1, Tf=10)
```

## Policy

`Policy(obs_shape, action_space, base=None, base_kwargs=None)` chooses a base network from observation rank unless a custom `base` is supplied:

- `len(obs_shape) == 1` -> `MLPBase(obs_shape[0], **base_kwargs)`.
- `len(obs_shape) == 3` -> `CNNBase(obs_shape[0], **base_kwargs)`.
- Any other observation rank raises `NotImplementedError`.

The policy chooses its action distribution from `action_space.__class__.__name__`:

| Action space class name | Distribution module | Action tensor convention |
| --- | --- | --- |
| `Discrete` | `Categorical` / `FixedCategorical` | shape `(N, 1)`, dtype `long` |
| `Box` | `DiagGaussian` / `FixedNormal` | shape `(N, action_dim)`, floating point |
| `MultiBinary` | `Bernoulli` / `FixedBernoulli` | shape `(N, action_dim)`, floating point binary values |

Useful properties and methods:

```python
policy.is_recurrent                  # bool from the base
policy.recurrent_hidden_state_size   # hidden size if recurrent else 1
policy.act(inputs, rnn_hxs, masks, deterministic=False)
policy.get_value(inputs, rnn_hxs, masks)
policy.evaluate_actions(inputs, rnn_hxs, masks, action)
```

`act` returns `(value, action, action_log_probs, rnn_hxs)`.
`evaluate_actions` returns `(value, action_log_probs, dist_entropy, rnn_hxs)`.
`forward` is intentionally not implemented directly on `Policy`; use `act`, `get_value`, or `evaluate_actions`.

Batch conventions:

- `inputs`: `(N, *obs_shape)` for a single step, or flattened `(T * N, *obs_shape)` for rollout minibatches.
- `rnn_hxs`: `(N, recurrent_hidden_state_size)`.
- `masks`: `(N, 1)` float tensor; zero resets recurrent state for an environment.

## Bases

### `CNNBase(num_inputs, recurrent=False, hidden_size=512)`

- Inherits common recurrent handling from `NNBase`.
- Convolution stack: `Conv2d(num_inputs,32,kernel=8,stride=4)`, `Conv2d(32,64,kernel=4,stride=2)`, `Conv2d(64,32,kernel=3,stride=1)`, flatten, `Linear(32 * 7 * 7, hidden_size)`.
- Divides image inputs by `255.0` before the convolutional stack.
- Has `critic_linear(hidden_size -> 1)`.
- Return from `forward(inputs, rnn_hxs, masks)`: `(value, actor_features, rnn_hxs)`.

The fixed `32 * 7 * 7` linear input assumes Atari-style 84x84 image wrappers and channel-first tensors after frame stacking/transpose.

### `MLPBase(num_inputs, recurrent=False, hidden_size=64)`

- Uses separate actor and critic MLP towers.
- Each tower has two `Linear(..., hidden_size) + Tanh` layers.
- If recurrent, the GRU transforms the raw observation features before the actor/critic towers.
- Return from `forward(inputs, rnn_hxs, masks)`: `(value, actor_features, rnn_hxs)`.

## Distributions

The distribution wrappers standardize methods expected by `Policy`:

- `FixedCategorical.sample()` returns shape `(N, 1)`.
- `FixedCategorical.log_probs(actions)` sums over the action dimension and returns `(N, 1)`.
- `FixedCategorical.mode()` returns the argmax action with shape `(N, 1)`.
- `FixedNormal.log_probs(actions)` sums per-action log probabilities and returns `(N, 1)`.
- `FixedNormal.entropy()` sums entropy over the action dimension.
- `FixedNormal.mode()` returns the mean action.
- `FixedBernoulli.entropy()` sums entropy over the binary action dimension.
- `FixedBernoulli.mode()` thresholds probabilities at `0.5`.

`Categorical`, `DiagGaussian`, and `Bernoulli` are `nn.Module` heads that map policy features to the corresponding fixed distribution. `DiagGaussian` uses `utils.AddBias` to hold log standard deviations.

## RolloutStorage

`RolloutStorage(num_steps, num_processes, obs_shape, action_space, recurrent_hidden_state_size)` allocates tensors for a complete on-policy rollout:

| Tensor | Shape |
| --- | --- |
| `obs` | `(num_steps + 1, num_processes, *obs_shape)` |
| `recurrent_hidden_states` | `(num_steps + 1, num_processes, recurrent_hidden_state_size)` |
| `rewards` | `(num_steps, num_processes, 1)` |
| `value_preds` | `(num_steps + 1, num_processes, 1)` |
| `returns` | `(num_steps + 1, num_processes, 1)` |
| `action_log_probs` | `(num_steps, num_processes, 1)` |
| `actions` | `(num_steps, num_processes, 1)` for `Discrete`, otherwise `(num_steps, num_processes, action_space.shape[0])` |
| `masks` | `(num_steps + 1, num_processes, 1)` |
| `bad_masks` | `(num_steps + 1, num_processes, 1)` |

Important methods:

```python
rollouts.to(device)
rollouts.insert(obs, recurrent_hidden_states, actions, action_log_probs, value_preds, rewards, masks, bad_masks)
rollouts.after_update()
rollouts.compute_returns(next_value, use_gae, gamma, gae_lambda, use_proper_time_limits=True)
rollouts.feed_forward_generator(advantages, num_mini_batch=None, mini_batch_size=None)
rollouts.recurrent_generator(advantages, num_mini_batch)
```

`bad_masks` distinguishes true terminal states from time-limit truncations when `use_proper_time_limits=True`.

## Algorithms

### `A2C_ACKTR`

`A2C_ACKTR(..., acktr=False)` uses RMSprop when `acktr=False` and `KFACOptimizer(actor_critic)` when `acktr=True`.

`update(rollouts)`:

1. Flattens rollout observations/actions across `(num_steps, num_processes)`.
2. Calls `actor_critic.evaluate_actions`.
3. Computes value loss, policy action loss, and entropy.
4. For ACKTR, optionally accumulates Fisher statistics before the actual update.
5. Clips gradients only for the non-ACKTR path.
6. Returns `(value_loss.item(), action_loss.item(), dist_entropy.item())`.

### `PPO`

`PPO.update(rollouts)`:

1. Computes normalized advantages from `returns[:-1] - value_preds[:-1]`.
2. Uses `rollouts.recurrent_generator` for recurrent policies, otherwise `feed_forward_generator`.
3. Runs `ppo_epoch * num_mini_batch` minibatch updates.
4. Applies clipped policy loss and optionally clipped value loss.
5. Returns epoch-averaged `(value_loss, action_loss, dist_entropy)`.

## KFACOptimizer

`KFACOptimizer` is an `optim.Optimizer` subclass used by ACKTR. It:

- Splits biases into separate `AddBias` modules before optimization.
- Registers hooks on `Linear`, `Conv2d`, and `AddBias` modules.
- Tracks activation and gradient-output covariance statistics.
- Periodically eigendecomposes covariances and applies a KL-clipped natural-gradient-style update.

Treat this implementation as tightly coupled to the repository's policy modules and PyTorch version. See troubleshooting before using ACKTR on newer PyTorch releases.

## Utility Functions

```python
utils.update_linear_schedule(optimizer, epoch, total_num_epochs, initial_lr)
utils.cleanup_log_dir(log_dir)
utils.init(module, weight_init, bias_init, gain=1)
utils.get_render_func(venv)
utils.get_vec_normalize(venv)
utils.AddBias(bias)
```

- `update_linear_schedule` sets each optimizer param group's learning rate to `initial_lr - initial_lr * epoch / total_num_epochs`.
- `cleanup_log_dir` creates `log_dir` when missing; when it already exists, it deletes `*.monitor.csv` files in that directory.
- `init` initializes a module's `weight` and `bias` tensors and returns the module.
- `get_render_func` and `get_vec_normalize` recursively unwrap vectorized environments.
