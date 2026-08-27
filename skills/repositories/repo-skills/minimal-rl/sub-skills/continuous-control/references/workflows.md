# Continuous-Control Workflows

## Choose the algorithm

| User intent | Route | Notes |
|---|---|---|
| Deterministic continuous actor with replay | DDPG | Uses OU exploration, separate actor/critic targets, and soft target updates. |
| On-policy continuous clipped objective | PPO-Continuous | Uses Gaussian policy, short rollouts, buffer of rollout minibatches, and GAE. |
| Stochastic off-policy maximum-entropy learning | SAC | Uses tanh-squashed Gaussian policy, twin Q networks, entropy temperature update. |

## DDPG workflow

1. Initialize actor `mu`, actor target `mu_target`, critic `q`, and critic target `q_target`.
2. Copy source weights into both targets.
3. During rollout, compute `a = mu(state)` and add OU noise.
4. Store `(s, a, r/100.0, s_prime, done)` in replay.
5. After replay warm-up, sample batches and update:
   - critic target `r + gamma * q_target(s_prime, mu_target(s_prime)) * done_mask`,
   - critic smooth-L1 loss,
   - actor loss `-q(s, mu(s)).mean()`,
   - soft-update actor and critic targets.
6. Keep action scaling aligned with the environment. The source actor uses `tanh * 2` because Pendulum actions are in `[-2, 2]`.

## Continuous PPO workflow

1. Sample a Gaussian action from `(mu, std) = model.pi(state)`.
2. Store short rollouts of length `rollout_len=3` with state, action, reward scaling `r/10.0`, next state, old log probability, and done.
3. Once `minibatch_size * buffer_size` rollouts are available, convert them into minibatches.
4. Compute TD targets and GAE.
5. For each epoch, recompute current log probabilities and apply PPO clipped ratio using old log probabilities.
6. Clip gradients with max norm `1.0` as in the source script.

## SAC workflow

1. Initialize policy `pi`, critics `q1/q2`, and critic targets.
2. During rollout, sample tanh action and corrected log probability from `PolicyNet.forward`; the source steps Pendulum with `[2.0 * action]`.
3. Store `(s, action, r/10.0, s_prime, done)` in replay.
4. After replay warm-up, sample batches and compute `calc_target` with target critics and entropy.
5. Train both critics to the target.
6. Train policy against the minimum of the two critics and update `log_alpha`.
7. Soft-update both target critics.

## Porting to another continuous environment

- Replace observation dimension `3` with the new flattened observation dimension.
- Replace action dimension `1` with the new action dimension in actor heads, action encoders, and replay action tensors.
- Replace hard-coded action scaling (`*2` or `tanh * 2`) with a transform derived from the environment's action low/high bounds.
- Revisit reward scaling (`r/100.0` for DDPG, `r/10.0` for PPO/SAC) before judging learning quality.
- Ensure Gym step handling uses `done = terminated or truncated`.
- Run `scripts/smoke_continuous_control.py` after changing shapes and before long training.

## Safe smoke strategy

The bundled smoke helper validates actor/critic tensor shapes, stochastic policy outputs, target calculations, OU noise shape, and soft-update direction. It does not prove learning performance. Use it before reduced-episode experiments, then add a tiny environment rollout once shape checks pass.
