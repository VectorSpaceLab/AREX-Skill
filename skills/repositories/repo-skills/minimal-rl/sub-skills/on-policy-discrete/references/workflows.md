# On-Policy Discrete Workflows

## Choose the algorithm

| User intent | Best route | Why |
|---|---|---|
| Teach or inspect simplest Monte-Carlo policy gradient | REINFORCE | Smallest policy-only loop; stores selected action probabilities and discounted returns. |
| Add a value baseline but keep one process | Vanilla actor-critic | Shared policy/value trunk, TD target, short rollout batches. |
| Use modern clipped policy optimization | Discrete PPO | Adds GAE, behavior probabilities, clipped ratio, and repeated epochs over a horizon. |
| Add recurrence to PPO | PPO-LSTM | Same PPO objective with explicit LSTM hidden-state storage. |
| Discuss policy/value correction from behavior probabilities | V-trace bridge | Uses policy/value network like actor-critic but with clipped importance ratios. |

## REINFORCE adaptation recipe

1. Keep the policy output as probabilities from a softmax over the action dimension.
2. During rollout, sample from `Categorical(prob)` and store `(reward, prob[action])`.
3. In the update, reverse-scan rewards into `R = r + gamma * R` and backprop `-log(prob) * R`.
4. When porting to another discrete environment, change the first linear layer to the new observation dimension and the final layer to `env.action_space.n`.
5. Do not convert the stored probability to a Python float before training; the loss needs the tensor's graph.

## Vanilla actor-critic workflow

1. Collect up to `n_rollout` transitions `(s, a, r, s_prime, done)`.
2. Build batched tensors; source reward scaling divides rewards by `100.0` to keep TD errors small.
3. Compute `td_target = r + gamma * v(s_prime) * done_mask`.
4. Compute `delta = td_target - v(s)` and detach it for the policy term.
5. Use `pi(s, softmax_dim=1).gather(1, a)` for the selected-action probabilities in a batch.
6. Optimize `-log(pi_a) * delta.detach() + smooth_l1_loss(v(s), td_target.detach())`.

## Discrete PPO workflow

1. During rollout, store behavior probability `prob[a].item()` with each transition; PPO compares the new policy to this old behavior probability.
2. After each `T_horizon`, batch transitions into `s, a, r, s_prime, done_mask, prob_a`.
3. Compute TD targets and deltas with the value head.
4. Reverse-scan deltas into GAE: `advantage = gamma * lmbda * advantage + delta_t`.
5. Recompute current `pi_a`, then use `ratio = exp(log(pi_a) - log(prob_a))`.
6. Minimize `-min(ratio * advantage, clamp(ratio, 1-eps_clip, 1+eps_clip) * advantage)` plus value loss.

## PPO-LSTM workflow

1. Initialize hidden state `(h, c)` as zeros shaped `[1, 1, 32]` for the single environment stream.
2. Store both incoming and outgoing hidden states for each transition.
3. In training, detach the first and second hidden states before computing losses.
4. Keep the time/batch dimensions expected by the script: inputs are reshaped to `[-1, 1, 64]` before LSTM.
5. If you batch multiple environments, redesign hidden-state storage; do not simply concatenate hidden tuples from the one-env script.

## V-trace bridge workflow

Use V-trace when you need to reason about behavior-policy probabilities `mu_a` versus current policy probabilities `pi_a` without using ACER's replay structure.

1. Store `(s, a, r, s_prime, mu_a, done)` over a horizon.
2. Compute `ratio = exp(log(pi_a) - log(mu_a))`.
3. Clip `rho` and `c` by their thresholds.
4. Reverse-scan TD deltas into corrected targets `vs` and advantages.
5. Use `rhos` in the policy loss and smooth-L1 for value targets.

## Porting to a new discrete Gym environment

Checklist:

- Replace input dimension `4` with `env.observation_space.shape[0]` for vector observations.
- Replace output dimension `2` with `env.action_space.n`.
- Use `softmax_dim=0` for one observation and `softmax_dim=1` for a batch.
- Revisit reward scaling (`r/100.0` may be inappropriate outside CartPole).
- In Gym 0.26-style environments, unpack reset and step results and use `done = terminated or truncated`.
- Before long training, run the smoke helper for the relevant algorithm and add a tiny rollout test around your new environment.
