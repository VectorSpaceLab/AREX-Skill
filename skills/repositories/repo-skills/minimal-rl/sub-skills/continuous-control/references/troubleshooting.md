# Continuous-Control Troubleshooting

## Actions exceed the environment range

**Symptoms**: environment clips actions, rewards are very poor, or ported DDPG/SAC acts outside valid bounds.

**Likely cause**: the source code assumes Pendulum's `[-2, 2]` action range.

**Fix**:
- Replace `tanh(x) * 2` and `[2.0 * action]` with a scale/shift based on `action_space.low` and `action_space.high`.
- Keep the replay action values in the same scale expected by the critic.
- Re-run the continuous smoke helper after changing action dimensions.

## `mat1 and mat2 shapes cannot be multiplied`

**Likely causes**:
- Observation dimension is not 3 after porting.
- Action dimension is not 1 but the critic action encoder still uses `Linear(1, 64)`.
- State and action tensors are missing the batch dimension.

**Fix**:
- Update every actor input, critic state input, critic action input, and replay tensor shape together.
- Use state shape `(batch, obs_dim)` and action shape `(batch, action_dim)` for critic calls.

## SAC `log_prob` has the wrong shape or becomes NaN

**Likely causes**:
- Tanh correction was removed or applied after converting tensors to Python floats.
- `std` became zero or negative after replacing `softplus`.
- Action/log-prob was squeezed inconsistently before Q-network calls.

**Fix**:
- Keep `std = F.softplus(fc_std(x))` or add a positive lower bound.
- Preserve corrected log probability: `log_prob - log(1 - tanh(action)^2 + 1e-7)`.
- Keep action and log-prob shaped `(batch, action_dim)`.

## DDPG or SAC target network moves in the wrong direction

**Symptom**: target parameters jump to current weights or never change.

**Fix**: preserve the source soft-update direction:

```python
target_param.data.copy_(target_param.data * (1.0 - tau) + source_param.data * tau)
```

Use DDPG's `tau=0.005` and SAC's `tau=0.01` unless you intentionally retune.

## Replay sampling fails

**Likely cause**: the replay buffer has fewer entries than `batch_size`.

**Fix**:
- Wait for the source warm-up thresholds: DDPG uses `memory.size() > 2000`; SAC uses `memory.size() > 1000`.
- For tiny tests, lower the synthetic batch size rather than running full training.

## Continuous PPO minibatch construction underflows

The source `train_net()` only trains when `len(self.data) == minibatch_size * buffer_size`. If you reduce `rollout_len`, `buffer_size`, or `minibatch_size`, update that equality and the nested batch construction together.

## Gym reset/step compatibility problems

Use modern Gym handling:

```python
s, _ = env.reset()
s_prime, r, terminated, truncated, info = env.step([action])
done = terminated or truncated
```

For vector actions, pass a list/array with the correct action dimension.
