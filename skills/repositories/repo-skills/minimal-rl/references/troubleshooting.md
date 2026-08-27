# minimalRL Cross-Cutting Troubleshooting

## Install/import failures

**Symptoms**: `ModuleNotFoundError: No module named 'torch'`, `No module named 'gym'`, or NumPy/Gym compatibility warnings.

**Fix**:
```bash
python -m pip install "torch" "gym==0.26.2" "numpy<2"
python scripts/check_minimal_rl_env.py --make-envs
```

Use Gym 0.26 for source compatibility. Gym may print a deprecation warning recommending Gymnasium; that warning alone is not a failure for this repository's examples.

## `np.bool8` or NumPy 2.x errors with Gym

**Cause**: Gym 0.26 is unmaintained and can break with NumPy 2.x.

**Fix**: pin NumPy below 2 in the environment used for these algorithms:

```bash
python -m pip install "numpy<2" "gym==0.26.2"
```

## Gym reset/step arity errors

Modern Gym reset/step handling should look like:

```python
s, _ = env.reset()
s_prime, r, terminated, truncated, info = env.step(action)
done = terminated or truncated
```

For continuous environments, pass actions in the expected vector/list shape, for example `[action]` for Pendulum's one-dimensional action.

## Full training is too slow for debugging

The minimalRL scripts are educational full training loops, often with 10000 episodes or multiprocessing workers. Before full training:

1. Run `python scripts/check_minimal_rl_env.py --make-envs`.
2. Run the nearest sub-skill smoke helper.
3. Reduce episode counts, worker counts, and max steps while debugging.
4. Only then restore full script-style training if the task actually requires it.

## Observation/action dimension mismatch after porting

**Symptoms**: PyTorch matrix-shape errors, wrong action count, failed `gather`, or critic concatenation errors.

**Fix**:
- For CartPole-style discrete scripts, replace observation input `4` and action output `2` consistently.
- For Pendulum-style continuous scripts, replace observation input `3`, action dimension `1`, and action scaling together.
- Re-run the owning sub-skill smoke helper after shape changes.

## Reward scaling causes unexpected learning behavior

Many scripts divide rewards by `100.0`; PPO-Continuous and SAC divide Pendulum rewards by `10.0`. These are teaching choices, not universal constants. When adapting to another environment, inspect reward magnitude and retune scaling before changing optimizers or model depth.

## GPU expectations

The selected skill scope is CPU. The repository README says examples can train without GPU, and no generated workflow claims CUDA/ROCm/MPS coverage. If a future task introduces GPU-specific requirements, treat that as a new extension or refresh need and verify the backend explicitly.
