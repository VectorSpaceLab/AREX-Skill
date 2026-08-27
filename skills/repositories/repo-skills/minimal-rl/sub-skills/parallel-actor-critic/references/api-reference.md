# Parallel Actor-Critic API Reference

## Purpose

Read this when adapting minimalRL's A2C and A3C multiprocessing examples. These scripts are educational and compact, but they use process coordination and older Gym API patterns that should be modernized before full execution.

## Shared actor-critic network

| Surface | Contract |
|---|---|
| Class | `ActorCritic` in both A2C and A3C scripts |
| Network | `Linear(4,256) -> ReLU` shared trunk |
| Policy head | `fc_pi: Linear(256,2)` with softmax |
| Value head | `fc_v: Linear(256,1)` |
| `pi(x, softmax_dim=...)` | returns action probabilities; A2C defaults to batch `softmax_dim=1`, A3C defaults to single-state `softmax_dim=0` |
| `v(x)` | returns scalar value for one state or `(batch,1)` for a batch |
| Environment | CartPole-style observation length 4 and 2 discrete actions |

## A2C contracts

| Surface | Contract |
|---|---|
| `n_train_processes` | `3` worker environments |
| `update_interval` | `5` vector steps per update |
| `max_train_steps` | `60000` |
| `PRINT_INTERVAL` | `update_interval * 100` |
| `worker(worker_id, master_end, worker_end)` | child process that receives commands over a pipe and owns one Gym environment |
| `ParallelEnv.step_async(actions)` | sends `('step', action)` to every worker pipe |
| `ParallelEnv.step_wait()` | receives worker results, stacks observations/rewards/dones, returns `(obs, rews, dones, infos)` |
| `ParallelEnv.reset()` | sends `('reset', None)` to workers and stacks observations |
| `ParallelEnv.close()` | drains pending messages, sends close commands, joins workers |
| `compute_target(v_final, r_lst, mask_lst)` | reverse-scans rewards and masks into bootstrapped returns |

The source A2C update flattens `[update_interval, n_envs, ...]` rollout tensors into `(update_interval * n_envs, obs_dim)` and `(update_interval * n_envs, 1)` actions.

## A3C contracts

| Surface | Contract |
|---|---|
| `n_train_processes` | `3` training workers plus one test process |
| `max_train_ep` | `300` per train worker |
| `max_test_ep` | `400` for tester |
| `global_model.share_memory()` | required before spawning workers so parameters are shared across processes |
| `train(global_model, rank)` | creates local model, collects rollouts, computes local gradients, assigns them to global params, steps global optimizer, reloads local weights |
| `test(global_model)` | runs evaluation episodes and prints average score |
| Gradient copy | `global_param._grad = local_param.grad` before optimizer step |

## Gym API migration facts

The parallel scripts include older Gym calls such as `env.seed(worker_id)`, `s = env.reset()` without unpacking, and `s_prime, r, done, info = env.step(a)`. For Gym 0.26-compatible environments, use:

```python
s, _ = env.reset(seed=worker_id)
s_prime, r, terminated, truncated, info = env.step(a)
done = terminated or truncated
```

Worker responses should send only the observation array, not the full reset tuple, unless all downstream code is updated to handle tuples.
