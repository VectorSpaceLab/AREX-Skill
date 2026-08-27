# Off-Policy Value API Reference

## Purpose

Read this when adapting minimalRL's DQN, ACER, or V-trace correction logic. The contracts below are distilled from the repository scripts and are intended for safe use without reopening the original checkout.

## DQN contracts

| Surface | Contract |
|---|---|
| Class | `ReplayBuffer` |
| Storage | `collections.deque(maxlen=buffer_limit)` with `buffer_limit = 50000` |
| `put(transition)` | appends `(s, a, r, s_prime, done_mask)` |
| `sample(n)` | random-samples `n` transitions and returns tensors `s, a, r, s_prime, done_mask` |
| `size()` | returns current replay length |
| Class | `Qnet` |
| Network | `Linear(4,128) -> ReLU -> Linear(128,128) -> ReLU -> Linear(128,2)` |
| `forward(x)` | returns Q values shaped `(2,)` for one state or `(batch,2)` for a batch |
| `sample_action(obs, epsilon)` | epsilon-greedy action; random action with probability `epsilon`, else `argmax` |
| Function | `train(q, q_target, memory, optimizer)` |
| Train loop | Samples `batch_size = 32` transitions 10 times, computes `target = r + gamma * max_q_prime * done_mask`, and optimizes smooth-L1 loss |
| Hyperparameters | `learning_rate=0.0005`, `gamma=0.98`, `buffer_limit=50000`, `batch_size=32` |

DQN stores rewards as `r/100.0` in the main loop and uses `done_mask = 0.0 if done else 1.0`. In the source workflow, training starts only after replay size exceeds 2000.

## ACER contracts

| Surface | Contract |
|---|---|
| Class | `ReplayBuffer` |
| Storage | deque of rollout sequences, each sequence is a list of transitions |
| Sequence transition | `(s, a, r, prob, done)` where `prob` is the full behavior action-probability vector |
| `sample(on_policy=False)` | returns flattened tensors/lists for `batch_size = 4` sequences, or the most recent sequence when `on_policy=True` |
| Class | `ActorCritic` |
| Network | Shared `Linear(4,256)` trunk; policy head `fc_pi(256,2)` and Q head `fc_q(256,2)` |
| `pi(x, softmax_dim=0)` | action probabilities for single observation or batch |
| `q(x)` | Q values for each action |
| Function | `train(model, optimizer, memory, on_policy=False)` |
| Importance ratio | `rho = pi.detach() / prob`; selected `rho_a` is clipped by `c = 1.0` |
| Bias correction | `(1 - c / rho).clamp(min=0)` multiplies the policy correction term |
| Hyperparameters | `learning_rate=0.0002`, `gamma=0.98`, `buffer_limit=6000`, `rollout_len=10`, `batch_size=4`, `c=1.0` |

ACER's replay unit is a sequence, not a single transition. Preserve `is_first` markers when flattening multiple sequences so returns reset at sequence boundaries.

## V-trace contracts

| Surface | Contract |
|---|---|
| Class | `Vtrace` |
| Data transition | `(s, a, r, s_prime, mu_a, done)` where `mu_a` is selected behavior probability |
| `make_batch()` | returns `s, a, r, s_prime, done_mask, mu_a` |
| `vtrace(s,a,r,s_prime,done_mask,mu_a)` | computes current `pi_a`, value estimates, ratio, clipped `rhos`/`cs`, corrected value targets `vs`, advantages, and returns `(vs, advantage, rhos)` |
| Thresholds | `clip_rho_threshold = 1.0`, `clip_c_threshold = 1.0` |
| Train loss | `F.smooth_l1_loss(v(s), vs) + -rhos * log(pi_a) * advantage` |

V-trace and ACER both depend on behavior-policy probabilities, but V-trace stores selected `mu_a` while ACER stores the full behavior probability vector.

## Shared adaptation rules

- For another discrete environment, update observation dimension `4` and action dimension `2` in all network heads.
- Keep action tensors shaped `(batch, 1)` before `gather(1, a)`.
- Keep target computations detached from the target network or corrected-return scans unless intentionally changing the algorithm.
- Do not train from replay until the buffer has at least the requested sample size; the source scripts use much larger warm-up thresholds for stable learning.
