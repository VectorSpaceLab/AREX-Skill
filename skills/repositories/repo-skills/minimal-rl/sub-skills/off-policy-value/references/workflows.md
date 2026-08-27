# Off-Policy Value Workflows

## DQN workflow

1. Create current and target Q networks with identical architecture.
2. Copy current weights into the target network before training.
3. During rollout, choose actions with `sample_action(obs, epsilon)` and store `(s, a, r/100.0, s_prime, done_mask)`.
4. Wait for replay warm-up. The source script starts optimization after replay size exceeds 2000, even though `batch_size` is 32.
5. For each update:
   - sample a batch,
   - compute `q_a = q(s).gather(1, a)`,
   - compute `max_q_prime = q_target(s_prime).max(1)[0].unsqueeze(1)`,
   - compute `target = r + gamma * max_q_prime * done_mask`,
   - optimize smooth-L1 loss between `q_a` and `target`.
6. Periodically copy current weights to the target network.

When porting, update observation/action dimensions and revisit epsilon schedule, reward scaling, replay warm-up, and target-update frequency.

## ACER workflow

1. Collect `rollout_len` transitions into a sequence.
2. Store the full behavior probability vector `prob.detach().numpy()` with each transition, not just the selected probability.
3. Append the sequence to replay.
4. When replay size is sufficient, run one on-policy update from the latest sequence and one replay update from sampled sequences.
5. During training:
   - flatten selected sequences,
   - compute Q values and current policy probabilities,
   - compute `rho = pi.detach() / prob`,
   - clip selected ratios with `c`,
   - reverse-scan corrected returns, resetting at sequence starts,
   - combine truncated importance-sampling policy loss, bias correction, and Q-value smooth-L1 loss.

ACER in this repo is intentionally minimal: it is discrete-action and single-threaded, and it does not include trust-region updates.

## V-trace workflow

1. Store selected behavior probability `mu_a` for each sampled action.
2. Batch a horizon into tensors `s, a, r, s_prime, done_mask, mu_a`.
3. Recompute current policy probabilities and selected `pi_a`.
4. Compute ratios via `exp(log(pi_a) - log(mu_a))`.
5. Clip `rho` and `c`, then reverse-scan TD deltas to produce corrected value targets.
6. Use clipped `rhos` in the policy loss and corrected `vs` in the value loss.

Use V-trace guidance when the task is about off-policy correction from behavior probabilities. Use [on-policy-discrete](../../on-policy-discrete/SKILL.md) only for the network-shape and basic actor-critic route.

## Safe smoke strategy

Full DQN/ACER/V-trace training runs can take many episodes. For development or skill verification:

1. Run the bundled helper with `--algorithm all`.
2. Add tiny synthetic replay entries to verify tensor shapes.
3. Run a single optimizer step only after replay sample sizes are valid.
4. Use a one-episode environment smoke only after Gym reset/step handling is known to work.

## Porting to another discrete environment

- Replace all `Linear(4, ...)` observation inputs with the new flattened observation dimension.
- Replace all action outputs of size `2` with `env.action_space.n`.
- Ensure replay stores NumPy arrays or tensors that can be converted into consistent `torch.tensor(..., dtype=torch.float)` batches.
- Revisit reward scaling. `r/100.0` is a CartPole teaching simplification, not a universal RL rule.
- In modern Gym, compute `done = terminated or truncated` before building `done_mask`.
