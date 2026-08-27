# Procedural API Reference

This is a concise Tianshou 2.0.1 reference for low-level object wiring. Use live Python introspection when exact optional parameters matter, but the notes below capture the stable construction patterns and current signatures relevant to procedural training.

## Core Objects

| Object | Role | Notes |
| --- | --- | --- |
| `Policy` | Maps observation batches to actions or action distributions. | Inherits `torch.nn.Module`; `forward` returns a `Batch` with at least `act`; `compute_action` is convenient for single observations. |
| `Algorithm` | Owns learning logic and update orchestration. | Wraps a policy, optimizers, critics/targets as needed; call `algorithm.run_training(params)`. |
| `Collector` | Connects policy/algorithm with envs and buffers. | Signature: `Collector(policy, env, buffer=None, exploration_noise=False, on_episode_done_hook=None, on_step_hook=None, raise_on_nan_in_buffer=False, collect_stats_class=CollectStats)`. |
| `ReplayBuffer` | Stores single-env transitions. | Signature: `ReplayBuffer(size, stack_num=1, ignore_obs_next=False, save_only_last_obs=False, sample_avail=False, random_seed=42, **kwargs)`. |
| `DummyVectorEnv` | In-process vectorized env wrapper. | Signature: `DummyVectorEnv(env_fns, wait_num=None, timeout=None)`. Good default for CPU smoke tests. |
| `SubprocVectorEnv` | Multi-process vectorized env wrapper. | Signature: `SubprocVectorEnv(env_fns, wait_num=None, timeout=None, share_memory=False, context=None)`. Use only when env constructors are pickle-safe. |

## Trainer Params

| Class | Use For | Required/Important Fields |
| --- | --- | --- |
| `OffPolicyTrainerParams` | DQN, SAC, DDPG, TD3, Q-learning variants. | `training_collector`, `max_epochs`, `epoch_num_steps`, exactly one collection count, `batch_size`, `update_step_num_gradient_steps_per_sample`. |
| `OnPolicyTrainerParams` | PPO, A2C, NPG, TRPO, Reinforce. | `training_collector`, `max_epochs`, `epoch_num_steps`, exactly one collection count, `batch_size`, `update_step_num_repetitions`. |
| `OfflineTrainerParams` | Fixed-buffer offline learning. | `buffer`, `batch_size`; no online collection loop. |

Common online fields include `test_collector`, `test_step_num_episodes`, `stop_fn`, `training_fn`, `test_fn`, `save_best_fn`, `logger`, and `test_in_training`.

## Optimizer Factories

| Factory | Use |
| --- | --- |
| `AdamOptimizerFactory(lr=1e-3, betas=(0.9, 0.999), eps=1e-08, weight_decay=0)` | Standard procedural default for DQN/PPO/SAC examples. |
| `RMSpropOptimizerFactory(...)` | A2C-style or legacy RMSprop setups. |
| `TorchOptimizerFactory(torch.optim.SomeOptimizer, **kwargs)` | Custom PyTorch optimizer class while preserving Tianshou's factory contract. |
| `LRSchedulerFactoryLinear(max_epochs, epoch_num_steps, collection_step_num_env_steps)` | Attach with `.with_lr_scheduler_factory(...)` when linear LR decay should follow trainer progress. |

Pass factories to algorithms. Do not pass already-instantiated `torch.optim.Optimizer` objects unless you are intentionally modifying internals.

## Network Helpers

| Helper | Typical Role | Important Parameters |
| --- | --- | --- |
| `Net` | General MLP/action-representation network. | `state_shape`, `action_shape=0`, `hidden_sizes=()`, `softmax=False`, `concat=False`, `num_atoms=1`, `dueling_param=None`. |
| `MLP` | Plain vector MLP backbone. | `input_dim`, `output_dim=0`, `hidden_sizes`, `activation`, `flatten_input=True`. |
| `DiscreteActor` | Discrete stochastic actor. | `preprocess_net`, `action_shape`, `hidden_sizes=()`, `softmax_output=True`. |
| `DiscreteCritic` | Discrete value critic. | `preprocess_net`, `hidden_sizes=()`, `last_size=1`. |
| `ContinuousActor` | Deterministic continuous actor. | `preprocess_net`, `action_shape`, `hidden_sizes=()`, `max_action=1.0`. |
| `ContinuousActorProbabilistic` | Gaussian-style continuous actor for PPO/SAC. | `preprocess_net`, `action_shape`, `hidden_sizes=()`, `max_action=1.0`, `unbounded=False`, `conditioned_sigma=False`. |
| `ContinuousCritic` | Continuous value/Q critic. | `preprocess_net`, `hidden_sizes=()`, `apply_preprocess_net_to_obs_only=False`; accepts optional `act` in `forward`. |
| `ActorCritic` | Utility wrapper for actor + critic modules. | Useful for joint initialization and saving. |

Use `SpaceInfo.from_env(env)` to get `observation_info.obs_shape` and `action_info.action_shape` for standard Gymnasium spaces.

## Algorithm Family Map

| Family | Policy | Algorithm | Trainer | Action Space |
| --- | --- | --- | --- | --- |
| DQN / Double DQN / Dueling DQN | `DiscreteQLearningPolicy` | `DQN` and distributional DQN variants | `OffPolicyTrainerParams` | `gym.spaces.Discrete` |
| PPO | `ProbabilisticActorPolicy` | `PPO` | `OnPolicyTrainerParams` | Discrete or continuous, depending on actor/dist function |
| A2C | `ProbabilisticActorPolicy` | `A2C` | `OnPolicyTrainerParams` | Discrete or continuous |
| NPG / TRPO | `ProbabilisticActorPolicy` | `NPG`, `TRPO` | `OnPolicyTrainerParams` | Discrete or continuous |
| Reinforce | `ProbabilisticActorPolicy` | `Reinforce` | `OnPolicyTrainerParams` | Discrete or continuous |
| DDPG | `ContinuousDeterministicPolicy` | `DDPG` | `OffPolicyTrainerParams` | `gym.spaces.Box` |
| TD3 | `ContinuousDeterministicPolicy` | `TD3` | `OffPolicyTrainerParams` | `gym.spaces.Box` |
| SAC | `SACPolicy` | `SAC` | `OffPolicyTrainerParams` | `gym.spaces.Box` |
| Discrete SAC | Discrete SAC policy | Discrete SAC algorithm | `OffPolicyTrainerParams` | `gym.spaces.Discrete` |
| Offline/imitation/model-based/MARL | Specialized policies/algorithms | BCQ/CQL/GAIL/ICM/PSRL/MARL, etc. | Usually offline/specialized | Route to `../offline-and-specialized-rl/SKILL.md` |

## Current Constructor Notes

### DQN

- `DiscreteQLearningPolicy(model, action_space, observation_space=None, eps_training=0.0, eps_inference=0.0)`.
- `DQN(policy, optim, gamma=0.99, n_step_return_horizon=1, target_update_freq=0, is_double=True, huber_loss_delta=None)`.
- The model maps observations to Q-values with shape `[batch, action_dim]`.
- For action masks, `DiscreteQLearningPolicy.forward` expects `batch.obs.mask` where valid actions are marked and unavailable actions can be masked before selection.

### PPO

- `PPO(policy, critic, optim, eps_clip=0.2, dual_clip=None, value_clip=False, advantage_normalization=True, recompute_advantage=False, vf_coef=0.5, ent_coef=0.01, max_grad_norm=None, gae_lambda=0.95, max_batchsize=256, gamma=0.99, return_scaling=False)`.
- Use `ProbabilisticActorPolicy` with a distribution function compatible with actor output.
- Continuous PPO commonly uses `ContinuousActorProbabilistic(..., unbounded=True)` plus `Independent(Normal(loc, scale), 1)` and a `ContinuousCritic`.

### SAC

- `SACPolicy(actor, exploration_noise=None, deterministic_eval=True, action_scaling=True, action_space, observation_space=None)`.
- `SAC(policy, policy_optim, critic, critic_optim, critic2=None, critic2_optim=None, tau=0.005, gamma=0.99, alpha=0.2, n_step_return_horizon=1, deterministic_eval=True)`.
- `SACPolicy` supports `gym.spaces.Box`; use a discrete SAC variant for discrete tasks.
- SAC actor output is tanh-squashed; the policy uses `action_bound_method=None` internally and can scale to the env's Box range.

### DDPG / TD3

- Use `ContinuousDeterministicPolicy(actor, exploration_noise='default' or custom noise, action_space=env.action_space, action_scaling=True, action_bound_method='clip')`.
- DDPG uses one critic and Polyak target updates; TD3 uses dual critics, target policy smoothing, and delayed actor updates.
- If the actor already outputs environment-scale actions, set `action_scaling=False` and `action_bound_method=None` to avoid double scaling.

### TRPO / NPG / A2C / Reinforce

- These are on-policy actor-critic or policy-gradient algorithms using `ProbabilisticActorPolicy` and compatible critics when required.
- TRPO/NPG optimizers generally apply to the critic side; policy updates use natural-gradient/trust-region logic.
- `return_scaling`, `gae_lambda`, `advantage_normalization`, and `max_batchsize` are the common stability levers.

## Import Patterns

Prefer explicit imports in procedural examples:

```python
import gymnasium as gym
import tianshou as ts
from tianshou.algorithm import DQN, PPO, SAC
from tianshou.algorithm.modelfree.dqn import DiscreteQLearningPolicy
from tianshou.algorithm.optim import AdamOptimizerFactory
from tianshou.data import Collector, CollectStats, ReplayBuffer, VectorReplayBuffer
from tianshou.env import DummyVectorEnv
from tianshou.trainer import OffPolicyTrainerParams, OnPolicyTrainerParams
from tianshou.utils.net.common import Net
from tianshou.utils.space_info import SpaceInfo
```

Use fully qualified module imports when subclassing internals so future readers can locate base classes and training stats.
