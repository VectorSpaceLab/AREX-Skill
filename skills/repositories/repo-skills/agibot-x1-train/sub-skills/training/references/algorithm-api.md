# DH PPO algorithm API

## Construction flow

`TaskRegistry.make_alg_runner` converts the nested environment and PPO config
objects with `class_to_dict`, merges them, evaluates the configured class names,
and constructs:

```text
DHOnPolicyRunner(env, all_cfg, log_dir, device=args.rl_device)
  -> ActorCriticDH(...).to(device)
  -> DHPPO(actor_critic, device=device, **algorithm_cfg)
  -> RolloutStorage(num_envs, 24, [num_obs], [num_critic_obs], [num_actions], ...)
```

For the default X1 task, use:

```text
num_short_obs = 235
num_proprio_obs = 47
num_critic_obs = 219
num_actions = 12
```

The runner uses privileged observations for the critic when provided. If
heights were enabled, it would derive a larger critic width from the privileged
single-frame width plus `terrain.num_height`; with the default no-height config,
219 is the expected width.

## ActorCriticDH

Constructor parameters relevant to this task:

```python
ActorCriticDH(
    num_short_obs=235,
    num_proprio_obs=47,
    num_critic_obs=219,
    num_actions=12,
    actor_hidden_dims=[512, 256, 128],
    critic_hidden_dims=[768, 256, 128],
    state_estimator_hidden_dims=[256, 128, 64],
    in_channels=66,
    kernel_size=[6, 4],
    filter_size=[32, 16],
    stride_size=[3, 2],
    lh_output_dim=64,
    init_noise_std=1.0,
)
```

The network contracts are:

- `act(observations)` takes `[batch, 3102]`, slices the last 235 values as
  short history, reshapes all input to `[batch, 66, 47]`, compresses long
  history to 64 values, estimates 3 values from short history, concatenates
  302 actor features, samples a 12-dimensional Normal action, and stores its
  distribution for log-probability/entropy calls.
- `act_inference(observations)` has the same input and feature path but returns
  the actor mean without sampling. This is the path used by downstream export
  or playback routes, not by the training launcher itself.
- `evaluate(critic_observations)` takes `[batch, 219]` and returns `[batch, 1]`.
- `std` is a trainable 12-vector. `get_actions_log_prob(actions)` returns one
  summed log probability per sample; `entropy` sums across actions.
- `reset(dones)` is a no-op because this policy has no recurrent hidden state.

A checkpoint must be rebuilt with the same dimensions and layer settings before
loading its state dict. A mismatch in history length or critic width is a
checkpoint incompatibility, not an Isaac Gym issue.

## DHPPO rollout/update contract

`DHPPO.act(obs, critic_obs)` calls the policy, evaluates the critic, records
sampled actions, values, action log probabilities, means, sigmas, and the input
observations in a transition. `process_env_step` stores rewards/dones and, when
`infos["time_outs"]` exists, adds `gamma * value` bootstrapping for timeouts.
`compute_returns(last_critic_obs)` evaluates the final critic state and calls
storage GAE with the configured `gamma=0.994` and `lam=0.9`.

During `update`, each mini-batch:

1. Recomputes the policy distribution and critic value.
2. Estimates linear velocity from the last 235 actor features.
3. Uses privileged critic features at `lin_vel_idx=199:202` as the reference
   linear velocity (default no-height case).
4. Computes clipped PPO surrogate/value losses, entropy, and an unweighted MSE
   state-estimator loss; clips gradients to `max_grad_norm=1`.
5. Averages value, surrogate, and estimator loss over
   `num_learning_epochs * num_mini_batches` and clears storage.

The adaptive schedule can change the optimizer learning rate using KL, but the
X1 config inherits `schedule='adaptive'` and desired KL 0.01 from the base
algorithm. The actor optimizer includes all actor-critic parameters, while a
separate estimator optimizer is created and saved; the update's main loss
already includes estimator MSE, so do not assume the separate optimizer is
stepped in this code path.

## RolloutStorage

For a normal no-height run:

```python
storage = RolloutStorage(
    num_envs=N,
    num_transitions_per_env=24,
    obs_shape=[3102],
    privileged_obs_shape=[219],
    actions_shape=[12],
    device="cpu",  # CPU shape smoke only
)
```

Allocated tensors are time-major `[24, N, ...]` for observations,
privileged observations, actions, rewards `[24,N,1]`, dones `[24,N,1]`,
values/returns/advantages, log-probabilities, means, and sigmas. The storage
raises `AssertionError("Rollout buffer overflow")` when more than 24 transitions
are added. `compute_returns` performs reverse GAE and normalizes advantages.
`mini_batch_generator(4, 2)` flattens time/environment to a batch of `24*N`,
uses mini-batch size `(24*N)//4`, and yields each batch twice across epochs.

The current DHPPO update expects the non-extended 11-item generator yield:
`obs, critic_obs, actions, target_values, advantages, returns,
old_log_prob, old_mu, old_sigma, hidden_states, masks`. Do not pass a
`num_single_obs` argument to this storage when reproducing the default update
shape; the extended yield has a different tuple layout.

## CPU-only shape smoke

The safe CPU check may instantiate `ActorCriticDH` with tiny hidden layers but
must retain the task dimensions and CNN geometry. It should assert:

```text
actor input [2, 3102] -> actions [2, 12]
critic input [2, 219] -> values [2, 1]
short history [2, 235] -> estimator [2, 3]
storage observations [24, 2, 3102]
storage privileged [24, 2, 219]
storage actions [24, 2, 12]
```

This smoke can call `act`, `get_actions_log_prob`, `evaluate`, add a tiny valid
transition, compute returns, and consume one generator batch. It must not import
or construct `X1DHStandEnv`, call Isaac Gym, simulate, load assets, or claim a
native run.

## Runner lifecycle and logging API

`DHOnPolicyRunner.learn(num_learning_iterations,
init_at_random_ep_len=False)` initializes TensorBoard if `log_dir` is not
`None`, resets the environment, rolls out 24 steps per iteration, computes
returns, updates PPO, logs, saves at the interval, and saves a final model.
`get_inference_policy(device=None)` switches the policy to eval mode and returns
`act_inference`; `get_inference_critic` returns `evaluate`. `save(path, infos)`
uses `torch.save`; `load(path, load_optimizer=True)` restores state dicts and,
when requested, both optimizers before setting `current_learning_iteration` to
the stored `iter`. The task registry resume flow passes `load_optimizer=False`.
