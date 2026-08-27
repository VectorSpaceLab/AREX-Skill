# Parallel Actor-Critic Workflows

## A2C synchronous vector rollout

1. Create `ParallelEnv(n_train_processes)` with one Gym environment per worker process.
2. Reset all workers and stack observations into shape `(n_envs, 4)`.
3. For `update_interval` steps:
   - compute batched policy probabilities with `softmax_dim=1`,
   - sample one action per environment,
   - send actions to workers,
   - store states, actions, rewards scaled by `1/100`, and masks `1 - done`.
4. Bootstrap from `v(s_final)` and call `compute_target` to reverse-scan returns.
5. Flatten rollout tensors across time and environment dimensions.
6. Compute advantage `td_target - v(s_vec)`, policy loss, and value smooth-L1 loss.
7. Optimize the shared actor-critic model.
8. Periodically run a short test/evaluation loop.

A2C is synchronous: every worker returns a step result before the next update proceeds.

## A3C asynchronous global/local workflow

1. Create a global `ActorCritic` and call `share_memory()` before spawning.
2. Spawn one test process and `n_train_processes` training workers under `if __name__ == '__main__'`.
3. In each training worker:
   - clone global weights into a local model,
   - collect up to `update_interval` steps,
   - compute bootstrapped returns and local loss,
   - backprop through the local model,
   - copy local gradients to global parameters,
   - step a global optimizer,
   - reload local model from global state.
4. Join all processes on exit.

A3C is asynchronous: workers update the shared model independently. Keep gradient copy and local reload logic explicit when adapting.

## Gym 0.26 migration recipe

Apply this before trying to run the full parallel scripts:

```python
# old: env.seed(worker_id); ob = env.reset()
ob, _ = env.reset(seed=worker_id)

# old: ob, reward, done, info = env.step(action)
ob, reward, terminated, truncated, info = env.step(action)
done = terminated or truncated

# when auto-resetting after done
if done:
    ob, _ = env.reset()
```

Also update the test loops in A2C/A3C so `s` is the observation array, not the reset tuple.

## Safe debugging checklist

- Start with `scripts/smoke_parallel_actor_critic.py --check all` to validate model and return math.
- Set `torch.set_num_threads(1)` before spawning many CPU workers if the host oversubscribes.
- Keep process creation inside `if __name__ == '__main__'`.
- Always send a close command and join workers in cleanup paths.
- Add timeouts or a maximum test episode count before experimenting with full scripts.
- Prefer a single worker while debugging Gym API migration, then restore the intended worker count.
