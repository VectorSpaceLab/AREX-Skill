# On-Policy Discrete API Reference

## Purpose

Read this when adapting minimalRL's single-process discrete CartPole policy-gradient family. The contracts below are distilled from the repository's top-level algorithm scripts and verified with lightweight import/shape checks.

## Shared assumptions

| Item | Contract |
|---|---|
| Environment family | CartPole-style discrete control. |
| Observation shape | Length 4 state vector. |
| Action space | 2 discrete actions. |
| Core dependencies | PyTorch, Gym 0.26-compatible API, NumPy where needed. |
| Training length | Full scripts use many episodes; use bundled smoke checks before long training. |
| Step handling | Modern Gym returns `(obs, reward, terminated, truncated, info)`; treat `done = terminated or truncated` when modernizing. |

## REINFORCE

| Surface | Contract |
|---|---|
| Class | `Policy` |
| Network | `Linear(4,128) -> ReLU -> Linear(128,2) -> softmax(dim=0)` |
| Optimizer | Adam over policy parameters, `learning_rate = 0.0002` |
| Discount | `gamma = 0.98` |
| Data buffer | `self.data` list of `(reward, selected_action_probability)` tuples |
| `forward(x)` | accepts one observation tensor shaped `(4,)`; returns action probabilities shaped `(2,)` |
| `put_data(item)` | appends one `(r, prob[a])` transition item |
| `train_net()` | walks data in reverse, accumulates discounted return `R`, backprops `-log(prob) * R`, steps optimizer, then clears `self.data` |

Notes:
- Store the selected probability tensor, not only the sampled action id; the loss uses `torch.log(prob)`.
- The original workflow uses raw CartPole rewards, unlike later actor-critic/PPO scripts that divide rewards by `100.0`.

## Vanilla actor-critic

| Surface | Contract |
|---|---|
| Class | `ActorCritic` |
| Shared trunk | `Linear(4,256) -> ReLU` |
| Policy head | `fc_pi: Linear(256,2)`, softmax over requested dimension |
| Value head | `fc_v: Linear(256,1)` |
| Optimizer | Adam, `learning_rate = 0.0002` |
| Discount / rollout | `gamma = 0.98`, `n_rollout = 10` |
| `pi(x, softmax_dim=0)` | returns action probabilities for single observation (`dim=0`) or batch (`dim=1`) |
| `v(x)` | returns scalar value for one state or `(batch,1)` for a batch |
| `put_data(transition)` | appends `(s, a, r, s_prime, done)` |
| `make_batch()` | returns tensors `(s_batch, a_batch, r_batch, s_prime_batch, done_batch)`; rewards are scaled as `r/100.0` |
| `train_net()` | computes TD target, detached advantage, policy log-prob loss plus smooth-L1 value loss |

## Discrete PPO

| Surface | Contract |
|---|---|
| Class | `PPO` |
| Network | `Linear(4,256)` trunk with policy head `Linear(256,2)` and value head `Linear(256,1)` |
| Hyperparameters | `learning_rate=0.0005`, `gamma=0.98`, `lmbda=0.95`, `eps_clip=0.1`, `K_epoch=3`, `T_horizon=20` |
| Data tuple | `(s, a, r, s_prime, prob_a, done)` where `prob_a` is the behavior probability for the selected action |
| `make_batch()` | returns `s, a, r, s_prime, done_mask, prob_a`; rewards are expected already scaled by `1/100` in the caller |
| `train_net()` | builds TD target, computes GAE by reverse scan over deltas, then minimizes clipped PPO objective plus value loss for `K_epoch` passes |

Key shape rule: call `pi(s, softmax_dim=1)` for a batch before `gather(1, a)`, but call `pi(single_state)` with default `softmax_dim=0` during rollout.

## PPO-LSTM

| Surface | Contract |
|---|---|
| Class | `PPO` in the recurrent PPO script |
| Network | `Linear(4,64) -> LSTM(64,32) -> policy/value heads` |
| Hidden state | tuple `(h, c)`, each shaped `[1, 1, 32]` for one CartPole stream |
| Hyperparameters | `learning_rate=0.0005`, `gamma=0.98`, `lmbda=0.95`, `eps_clip=0.1`, `K_epoch=2`, `T_horizon=20` |
| Data tuple | `(s, a, r, s_prime, prob_a, h_in, h_out, done)` |
| `pi(x, hidden)` | returns probabilities shaped `[1,1,2]` plus new hidden state |
| `v(x, hidden)` | returns value shaped `[1,1,1]` for one timestep |
| `train_net()` | uses first and second hidden states from the stored rollout, detaches them before optimization, and calls backward with `retain_graph=True` in the source pattern |

When adapting, keep hidden-state detach points explicit; otherwise recurrent PPO changes often fail with graph-reuse errors.

## V-trace policy/value surface

| Surface | Contract |
|---|---|
| Class | `Vtrace` |
| Network | Same 4-to-256 trunk, policy head to 2 actions, value head to scalar |
| Hyperparameters | `learning_rate=0.0005`, `gamma=0.98`, `T_horizon=20`, `clip_rho_threshold=1.0`, `clip_c_threshold=1.0` |
| Data tuple | `(s, a, r, s_prime, mu_a, done)` where `mu_a` is the behavior probability for selected action |
| `vtrace(s,a,r,s_prime,done_mask,mu_a)` | returns corrected value targets `vs`, advantages, and clipped `rhos` |
| `train_net()` | computes value smooth-L1 loss plus policy loss `-rhos * log(pi_a) * advantage` |

Use [../../off-policy-value/SKILL.md](../../off-policy-value/SKILL.md) when the task is mainly about off-policy correction or replay rather than on-policy route selection.
