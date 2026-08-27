# On-Policy Discrete Troubleshooting

## `IndexError` or wrong probabilities from `gather`

**Symptoms**: `gather(1, a)` fails, policy loss has unexpected shape, or `pi_a` is empty.

**Likely causes**:
- Using `softmax_dim=0` on a batched tensor.
- `a` is shaped `(batch,)` instead of `(batch, 1)`.
- Final policy head still outputs 2 actions after porting to a different environment.

**Fix**:
1. For batched states, call `pi(s, softmax_dim=1)`.
2. Store/actions as `[[a0], [a1], ...]` or call `a.unsqueeze(1)`.
3. Set the policy head output dimension to `env.action_space.n`.
4. Run `python sub-skills/on-policy-discrete/scripts/smoke_on_policy_discrete.py --algorithm ppo` to check the expected shape pattern.

## `log(0)`, NaN loss, or unstable PPO ratios

**Symptoms**: NaN policy loss, infinite ratio, or exploding gradients.

**Likely causes**:
- Behavior probability `prob_a` was not stored at action time.
- Probabilities were rounded, detached too early, or replaced with logits.
- Current or behavior probabilities reached exact zero.

**Fix**:
- Store selected behavior probabilities from the rollout policy.
- Use `Categorical(probs=prob)` when sampling from probabilities; use `Categorical(logits=...)` only after rewriting the loss consistently.
- Clamp probabilities to a small epsilon only as a defensive adaptation, and document that it changes the exact minimalRL math.

## `RuntimeError: Trying to backward through the graph a second time`

**Common in**: PPO-LSTM adaptations.

**Likely causes**:
- Reusing recurrent hidden states without detaching them between optimization passes.
- Storing graph-bearing tensors across rollout batches.
- Removing the source script's detach points around hidden states.

**Fix**:
1. Detach incoming/outgoing hidden states before the PPO optimization loop.
2. Store scalar old action probabilities with `.item()` for PPO-style behavior probabilities unless you intentionally need graph retention.
3. Clear the rollout buffer after `make_batch()`.
4. If you redesign multi-step recurrence, prefer truncated BPTT with explicit sequence boundaries.

## Gym reset/step tuple errors

**Symptoms**: `ValueError: too many values to unpack`, tensors are built from `(obs, info)` tuples, or `done` never triggers on truncation.

**Cause**: Modern Gym returns `(obs, info)` from `reset()` and five values from `step()`.

**Fix**:
```python
s, _ = env.reset()
s_prime, r, terminated, truncated, info = env.step(a)
done = terminated or truncated
```

## Full training appears to hang

The original minimalRL scripts use up to 10000 episodes. Even though the README describes them as quick educational examples, construction and debugging should start with shape and one-step smoke checks. Run the bundled smoke helper first, then reduce episode counts or add explicit stop conditions before trying full training.

## Reward scaling gives poor learning after porting

Actor-critic and PPO variants divide rewards by `100.0` in the stored data. That scaling is tuned for simple CartPole examples. For other environments, inspect reward magnitude and adjust scaling before blaming the optimizer or policy architecture.
