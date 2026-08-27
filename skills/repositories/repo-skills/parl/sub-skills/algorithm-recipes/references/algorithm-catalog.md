# Algorithm Catalog

This catalog distills PARL's built-in algorithm families into operational selection guidance. Use it to choose an algorithm, check the required `parl.Model` surface, and decide which backend needs runtime verification before claiming support.

## Backend status

| Backend | Status in this skill | Practical guidance |
| --- | --- | --- |
| Torch | Runtime signatures for the major built-in classes were verified during production inspection. | Prefer Torch for fast API/signature smoke checks and synthetic shape tests. Set `PARL_BACKEND=torch` before importing PARL. |
| Paddle | Source-backed and documented, but not runtime-verified in the minimum inspection environment. | Use for examples that are explicitly Paddle-oriented. Verify imports and tensor behavior in the target runtime before running training. |
| Fluid | Legacy source-backed backend. | Treat as maintenance/reference material unless the target environment intentionally uses legacy Paddle Fluid. |

`parl.algorithms` selects a backend at import time. If `PARL_BACKEND` is unset, PARL chooses the first available supported framework. Always set the backend explicitly when reproducibility matters.

## Algorithm availability by backend

| Family | Torch | Paddle | Fluid / legacy |
| --- | --- | --- | --- |
| Policy gradient / QuickStart | `PolicyGradient` | `PolicyGradient` | `PolicyGradient` |
| Value-based discrete control | `DQN`, `DDQN` | `DQN`, `DDQN` | `DQN`, `DDQN` |
| Continuous actor-critic | `DDPG`, `TD3`, `SAC`, `OAC` | `DDPG`, `TD3`, `SAC`, `OAC` | `DDPG`, `TD3`, `SAC` |
| Offline RL | `CQL`, `IQL` source class | `CQL` | not covered |
| On-policy actor-critic | `PPO`, `A2C` | `PPO`, `A2C` | `PPO`, `A3C` |
| Distributed actor-learner | not exported as a Torch class in the inspected algorithm package | `IMPALA` | `IMPALA` |
| Multi-agent | `QMIX`, `MADDPG`, `COMA`, `MAPPO` | `QMIX`, `MADDPG` | `QMIX`, `MADDPG` |
| Sequence/offline transformer | `DecisionTransformer`; `IQL` source class may require module-level import if not exposed by the backend package initializer | not covered | not covered |
| Evolution strategies examples | Example-level ES workflow, not a built-in `parl.algorithms` class in the inspected catalog | Example-level ES workflow | not covered |

## Selection matrix

| Task shape | Prefer | Required model methods | Typical data loop | Notes |
| --- | --- | --- | --- | --- |
| Tiny discrete control, teaching, CartPole-style benchmark | `PolicyGradient` or `DQN` | `PolicyGradient`: `forward(obs) -> action_prob`; `DQN`: `forward(obs) -> q_values` | Collect one episode or replay transitions; call `agent.learn(...)`. | QuickStart uses `PolicyGradient` and reward-to-go. DQN uses replay and target sync. |
| Discrete value control where over-estimation matters | `DDQN`; optionally DQN variants with dueling model architecture | `forward(obs) -> q_values`; target model sync | Replay buffer with `(obs, action, reward, next_obs, done)` batches. | DDQN changes target action selection, not the model interface. Dueling is model architecture, not a separate core algorithm class in this catalog. |
| Continuous online control with deterministic policy | `DDPG` | `policy(obs) -> action`, `value(obs, action) -> q`, `get_actor_params()`, `get_critic_params()` | Replay buffer; exploration noise in the Agent; periodic `sync_target`. | Simpler than TD3/SAC but more sensitive to Q over-estimation and exploration. |
| Continuous online control with stronger baselines | `TD3` or `SAC` | TD3 adds `Q1(obs, action)`; SAC needs stochastic `policy(obs) -> (mean, log_std)` and twin `value`. Both need actor/critic parameter groups. | Replay buffer; target networks; tune action scaling and entropy/noise. | TD3 uses delayed policy update and target policy smoothing. SAC uses entropy regularization. |
| Optimistic exploration in continuous control | `OAC` | Same base methods as SAC: `policy`, `value`, actor/critic parameter groups. | Replay buffer with an optimistic exploration action during sampling. | Use only when the exploration method is part of the experiment design; otherwise prefer SAC/TD3. |
| Offline continuous control | `CQL` or `IQL` | CQL: SAC-like `policy`, `value`, actor/critic parameter groups. IQL: `policy`, `value`, `qvalue`, `get_actor_params`, `get_critic_params`, `get_value_params`. | Fixed dataset batches, no environment collection inside the learner loop. | Do not mix online exploration code into an offline learner unless intentionally doing fine-tuning. |
| On-policy single-agent RL | `PPO` or `A2C` | `PPO`: `policy(obs)`, `value(obs)`. `A2C`: `policy`, `value`, `policy_and_value`. | Rollout buffer, advantage/return computation, minibatch update. | PPO can handle discrete or continuous action by `continuous_action`. A2C examples commonly use xparl actors. |
| Actor-learner distributed Atari | `IMPALA` on Paddle/Fluid | `policy(obs)`, `value(obs)` | Remote actors collect trajectories; learner applies V-trace loss. | Requires xparl and many actor processes for the documented scale. Use `xparl-distributed` before adapting. |
| Cooperative value-based MARL | `QMIX` | `agent_model.init_hidden()`, `agent_model.forward(...)`; `qmixer_model.forward(...)`; mixer has `n_agents` | Episode batches with state, observations, actions, rewards, termination, availability masks. | Requires SMAC-like environment metadata and careful padding/mask handling. |
| Multi-agent actor-critic | `MADDPG`, `COMA`, or `MAPPO` | MADDPG/COMA: `policy`, `value`, actor/critic params. COMA actor model also needs `init_hidden`. MAPPO model exposes actor/critic submodules plus `policy`, `value`, and `act_dim`. | Multi-agent rollouts, centralized critic inputs, per-agent or shared policies. | Start from shape contracts before changing environments; most errors are observation/action list mismatches. |
| Offline sequence modeling | `DecisionTransformer` | `forward(...)` for training; `get_action(...)` for inference | Dataset of trajectories with states/actions/returns-to-go/timesteps. | This is not an environment-interaction loop. Confirm top-level export in the target PARL package. |

## Constructor signatures to remember

Use the helper script for live signatures in the current environment. The following signatures are source-backed for the inspected code and useful for planning:

### Torch

- `PolicyGradient(model, lr)`
- `DQN(model, gamma=None, lr=None)` and `DDQN(model, gamma=None, lr=None)`; pass concrete floats for `gamma` and `lr`.
- `DDPG(model, gamma=None, tau=None, actor_lr=None, critic_lr=None)`
- `TD3(model, gamma=None, tau=None, actor_lr=None, critic_lr=None, policy_noise=0.2, noise_clip=0.5, policy_freq=2)`
- `SAC(model, gamma=None, tau=None, alpha=None, actor_lr=None, critic_lr=None)`
- `OAC(model, gamma=None, tau=None, alpha=None, beta=None, delta=None, actor_lr=None, critic_lr=None)`
- `CQL(model, gamma=None, tau=None, actor_lr=None, critic_lr=None, policy_eval_start=40000, with_automatic_entropy_tuning=True, with_lagrange=False, lagrange_thresh=10.0, min_q_version=3, min_q_weight=5.0, alpha=1.0)`
- `PPO(model, clip_param=0.1, value_loss_coef=0.5, entropy_coef=0.01, initial_lr=0.00025, eps=1e-05, max_grad_norm=0.5, use_clipped_value_loss=True, norm_adv=True, continuous_action=False)`
- `A2C(model, config)` where `config` contains at least the learning-rate and value-loss settings used by the selected example.
- `QMIX(agent_model, qmixer_model, double_q=True, gamma=0.99, lr=0.0005, clip_grad_norm=None)`
- `MADDPG(model, agent_index=None, act_space=None, gamma=None, tau=None, actor_lr=None, critic_lr=None)`
- `COMA(model, n_actions, n_agents, grad_norm_clip=None, actor_lr=None, critic_lr=None, gamma=None, td_lambda=None)`
- `MAPPO(model, clip_param, value_loss_coef, entropy_coef, initial_lr, huber_delta, eps=None, max_grad_norm=None, use_popart=True, use_value_active_masks=True)`
- `DecisionTransformer(model, learning_rate, warmup_steps, weight_decay)`
- `IQL(model, max_steps, lr=0.0003, tau=0.7, beta=3.0, discount=0.99, alpha=0.005)`; inspect whether the target package exports it at `parl.algorithms.IQL` or only from its module.

### Paddle

- `PolicyGradient(model, lr)`
- `DQN(model, gamma=None, lr=None)`, `DDQN(model, gamma=None, lr=None)`
- `DDPG`, `TD3`, `SAC`, `OAC`, and `CQL` follow the same broad constructor shape as Torch.
- `PPO(model, clip_param=0.1, value_loss_coef=0.5, entropy_coef=0.01, initial_lr=0.00025, eps=1e-05, max_grad_norm=0.5, use_clipped_value_loss=True, norm_adv=True, continuous_action=False)`
- `A2C(model, vf_loss_coeff=None)`
- `QMIX(agent_model, qmixer_model, double_q=True, gamma=0.99, lr=0.0005, clip_grad_norm=None)`
- `MADDPG(model, agent_index=None, act_space=None, gamma=None, tau=None, actor_lr=None, critic_lr=None)`
- `IMPALA(model, sample_batch_steps=None, gamma=None, vf_loss_coeff=None, clip_rho_threshold=None, clip_pg_rho_threshold=None)`

### Fluid legacy

Fluid constructors differ in places: `DQN` and `DDQN` include `act_dim`; `TD3` includes `max_action`; `SAC` takes separate `actor`, `critic`, and `max_action`; `PPO` uses `act_dim`, `policy_lr`, `value_lr`, and `epsilon`. Treat these as legacy-specific and verify with the current package before coding.

## Required model method checklist

Before instantiating an algorithm, assert the model implements the correct surface:

```python
required = {
    "PolicyGradient": ["forward"],
    "DQN": ["forward"],
    "DDQN": ["forward"],
    "DDPG": ["policy", "value", "get_actor_params", "get_critic_params"],
    "TD3": ["policy", "value", "Q1", "get_actor_params", "get_critic_params"],
    "SAC": ["policy", "value", "get_actor_params", "get_critic_params"],
    "OAC": ["policy", "value", "get_actor_params", "get_critic_params"],
    "CQL": ["policy", "value", "get_actor_params", "get_critic_params"],
    "PPO": ["policy", "value"],
    "A2C": ["policy", "value", "policy_and_value"],
    "QMIX": ["agent_model.init_hidden", "agent_model.forward", "qmixer_model.forward", "qmixer_model.n_agents"],
    "MADDPG": ["policy", "value", "get_actor_params", "get_critic_params"],
    "COMA": ["policy", "value", "get_actor_params", "get_critic_params", "actor_model.init_hidden"],
    "MAPPO": ["policy", "value", "actor", "critic", "act_dim"],
    "DecisionTransformer": ["forward", "get_action"],
    "IQL": ["policy", "value", "qvalue", "get_actor_params", "get_critic_params", "get_value_params"],
}
```

Keep Agent methods thin: convert NumPy/environment observations into backend tensors, call `self.alg.predict` or `self.alg.sample`, and pass shaped training batches to `self.alg.learn` or `self.alg.update`.
