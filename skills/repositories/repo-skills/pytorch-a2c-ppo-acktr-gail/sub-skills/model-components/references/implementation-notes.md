# Model Component Implementation Notes

Use these notes when adapting model, rollout, or algorithm internals. They summarize behavior that future agents need before editing code or constructing synthetic checks.

## Policy Selection and Custom Bases

`Policy` selects its base from observation rank:

- Vector observations (`len(obs_shape) == 1`) use `MLPBase`.
- Image observations (`len(obs_shape) == 3`) use `CNNBase`.
- Other shapes are unsupported unless a custom `base` is passed.

A custom base should be constructible as `base(obs_shape[0], **base_kwargs)` and should expose:

```python
base.output_size
base.is_recurrent
base.recurrent_hidden_state_size
base.forward(inputs, rnn_hxs, masks) -> (value, actor_features, rnn_hxs)
```

`actor_features` must have width `base.output_size` because the action distribution head is created immediately after the base.

## CNNBase Is Atari-Shape Specific

`CNNBase` has a fixed linear layer sized for a `32 x 7 x 7` final convolution map. In the repository workflow this comes from Atari-style preprocessing: frame warp to 84x84, transpose to channel-first, and frame stacking. A custom pixel environment with a different spatial size may select `CNNBase` but then fail at the linear layer unless you change the convolution stack or add a wrapper that produces the expected shape.

For end-to-end environment wrapper behavior, route to `../training-workflows/`.

## MLPBase and Recurrent Flow

`MLPBase` is the default for one-dimensional continuous-control observations. Without recurrence, the actor and critic towers each receive raw observations. With `recurrent=True`, the GRU processes the raw observation first and the actor/critic towers receive the recurrent hidden features.

`NNBase._forward_gru` supports two cases:

1. Single-step batches where `x.size(0) == hxs.size(0)`.
2. Flattened rollout batches where `x` is `(T * N, features)` and `hxs` is `(N, hidden_size)`.

`masks` zero out recurrent state at episode boundaries. When debugging recurrence, check both `recurrent_hidden_states` shape and whether masks are flattened consistently with the observation batch.

## Rollout Lifecycle

A typical rollout lifecycle is:

```python
rollouts = RolloutStorage(num_steps, num_processes, obs_shape, action_space, policy.recurrent_hidden_state_size)
rollouts.obs[0].copy_(initial_obs)
rollouts.to(device)

for step in range(num_steps):
    with torch.no_grad():
        value, action, action_log_prob, hxs = policy.act(
            rollouts.obs[step], rollouts.recurrent_hidden_states[step], rollouts.masks[step]
        )
    rollouts.insert(next_obs, hxs, action, action_log_prob, value, reward, masks, bad_masks)

with torch.no_grad():
    next_value = policy.get_value(rollouts.obs[-1], rollouts.recurrent_hidden_states[-1], rollouts.masks[-1])
rollouts.compute_returns(next_value, use_gae, gamma, gae_lambda, use_proper_time_limits=True)
agent.update(rollouts)
rollouts.after_update()
```

`after_update` carries the last observation, hidden state, mask, and bad mask into index `0` for the next rollout.

## Proper Time Limits and Returns

When `use_proper_time_limits=True`, `bad_masks` changes return computation:

- `bad_masks[t + 1] == 1`: normal bootstrapping/GAE behavior.
- `bad_masks[t + 1] == 0`: time-limit truncation; return is corrected with `value_preds[step]` rather than treated as a true terminal state.

If a synthetic test does not model time-limit truncation, use all-one `bad_masks`.

## A2C Versus ACKTR

`A2C_ACKTR` shares the same class for A2C and ACKTR:

- `acktr=False`: optimizer is `torch.optim.RMSprop(actor_critic.parameters(), lr, eps=eps, alpha=alpha)`; gradients are clipped with `max_grad_norm`.
- `acktr=True`: optimizer is `KFACOptimizer(actor_critic)`; the class performs an additional Fisher-statistics backward pass every `optimizer.Ts` steps; gradient clipping is skipped.

The command-line argument parser forbids `--recurrent-policy` with `--algo acktr`. The `A2C_ACKTR` class itself does not enforce this, so callers constructing it programmatically should enforce the same rule.

## PPO Update Mechanics

PPO normalizes advantages before minibatch iteration. It uses:

- `rollouts.feed_forward_generator` for non-recurrent policies.
- `rollouts.recurrent_generator` for recurrent policies.

The generators have assertions that are easy to trip with tiny rollouts:

- Feed-forward PPO requires `num_steps * num_processes >= num_mini_batch` when `mini_batch_size` is not supplied.
- Recurrent PPO requires `num_processes >= num_mini_batch`.

Use small synthetic rollouts with `num_mini_batch=1` unless the test is intentionally exercising these assertions.

## KFAC Mutates the Model Structure

`KFACOptimizer` calls a recursive bias-splitting routine before registering hooks. Any `Linear` or `Conv2d` with a bias is replaced by a wrapper that removes the native bias and adds a separate `AddBias` module. This is required because the optimizer expects every known module to expose exactly one parameter tensor.

Consequences for modifications:

- Do not assume the module tree is unchanged after constructing `KFACOptimizer`.
- If adding new module types, KFAC will ignore them unless `known_modules` and covariance logic are extended.
- Hook behavior and eigendecomposition calls are sensitive to PyTorch versions; verify ACKTR/KFAC separately from A2C/PPO.

## Distribution Head Modification Checklist

When changing action distributions or adding an action-space type:

1. Confirm `Policy.__init__` maps the action space to a distribution head.
2. Ensure the distribution returned by the head implements `sample`, `log_probs`, `entropy`, and `mode` with the shapes expected by `Policy`.
3. Update `RolloutStorage` action shape/dtype logic.
4. Add a synthetic smoke case for `Policy.act` and `Policy.evaluate_actions`.
5. Confirm the training command/workflow documents the action-space limitation.

## Learning-Rate Schedules

`utils.update_linear_schedule` directly mutates every optimizer param group's `lr`. In the training loop, ACKTR passes `agent.optimizer.lr` while A2C/PPO pass the CLI learning rate. If you wrap or replace optimizers, keep a stable initial learning-rate value available to avoid decaying from an already-decayed rate.

## Log Cleanup Side Effects

`utils.cleanup_log_dir(log_dir)` is intentionally simple: it creates the directory if missing, otherwise deletes existing `*.monitor.csv` files in that directory. It does not recursively clean subdirectories and it does not ask for confirmation. Avoid pointing it at a directory containing monitor CSVs that should be preserved.

## Safe Modification Workflow

For component-level changes:

1. Run the smoke script in `scripts/smoke_model_components.py` before editing.
2. Make a narrow change to one component class or distribution wrapper.
3. Add/extend a synthetic CPU check that exercises the changed component without creating Gym environments.
4. If changing training-loop semantics, route to `../training-workflows/` for command and wrapper implications.
5. If changing GAIL rewards, discriminator, or expert data, route to `../gail-imitation/`.
