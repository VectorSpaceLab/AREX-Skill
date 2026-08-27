# Parallel Actor-Critic Troubleshooting

## `AttributeError: 'TimeLimit' object has no attribute 'seed'`

**Cause**: Gym 0.26 removed the old `env.seed(...)` method.

**Fix**: seed through reset:

```python
ob, _ = env.reset(seed=worker_id)
```

## `ValueError: too many values to unpack` or tuple observations

**Cause**: reset/step API mismatch between old Gym examples and Gym 0.26-compatible environments.

**Fix**:
```python
ob, _ = env.reset()
ob, reward, terminated, truncated, info = env.step(action)
done = terminated or truncated
```

Ensure worker pipes send observations, not `(obs, info)` tuples, unless the master code is updated accordingly.

## Worker hangs or `step_wait()` never returns

**Likely causes**:
- A worker crashed before sending a response.
- Master sent a command not handled by `worker`.
- A pending `step_async` result was not drained before `close`.
- Full training/test loop has no reduced stop condition during debugging.

**Fix**:
- Add bounded debug logging around worker command receive/send points.
- Validate the command names: `step`, `reset`, `reset_task`, `close`, `get_spaces`.
- Use `ParallelEnv.close()` and drain pending messages when `waiting` is true.
- Debug with one worker before restoring `n_train_processes=3`.

## A3C gradients are missing or global model does not learn

**Likely causes**:
- `global_model.share_memory()` was not called before spawning.
- Local gradients were not copied to global parameters.
- Optimizer is attached to the wrong parameter set.
- Local model is not reloaded after the global update.

**Fix**:
- Construct the optimizer over `global_model.parameters()`.
- After `loss.backward()`, assign `global_param._grad = local_param.grad` for each parameter pair before `optimizer.step()`.
- Reload local model with `local_model.load_state_dict(global_model.state_dict())` after stepping.

## CPU oversubscription or poor throughput

Multiprocessing plus PyTorch CPU threading can create too many threads.

**Fix**:
- Try `torch.set_num_threads(1)` before spawning worker processes.
- Reduce `n_train_processes` during debugging.
- Avoid running multiple full parallel training jobs in the same shell.

## Process start method problems

On platforms that use `spawn`, missing `if __name__ == '__main__'` guards can recursively spawn processes. Keep all process creation under the main guard, including test process creation.

## Full script runs too long

A2C uses `max_train_steps=60000`; A3C uses multiple workers with `max_train_ep=300` plus a test process. Before full runs, use the smoke helper, then reduce max steps/episodes and worker count for debugging.
