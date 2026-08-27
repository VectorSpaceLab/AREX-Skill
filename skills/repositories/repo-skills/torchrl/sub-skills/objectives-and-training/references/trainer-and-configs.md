# Trainer and Hydra configs

Use this reference when the task involves `torchrl.trainers`, trainer hooks, algorithm config dataclasses, or changing loss constructor/config parity.

## Trainer role

`torchrl.trainers.Trainer` owns the nested collection/optimization loop but does not build the environment, policy, replay buffer, loss, optimizer, or logger for you. You provide those components and register hook operations at named stages.

Important constructor fields observed in source:

```text
Trainer(*, collector, total_frames, frame_skip, optim_steps_per_batch, loss_module,
        optimizer=None, optimization_stepper=None, replay_buffer=None,
        target_net_updater=None, batch_size=None, learner_backend='local',
        learner_backend_options=None, learner_poll_interval=0.05, logger=None,
        clip_grad_norm=True, clip_norm=None, progress_bar=True, seed=None,
        save_trainer_interval=10000, log_interval=10000,
        save_trainer_file=None, checkpoint=None, checkpoint_rotation=None,
        checkpoint_metadata=None, num_epochs=1, async_collection=False,
        log_timings=False, auto_log_optim_steps=True)
```

Route component ownership:

- collector and replay object construction: `collectors-and-replay`;
- policy/critic modules: `modules-and-policies`;
- env specs and transforms: `envs-and-transforms`;
- objective, estimator, target updater, optimizer, and trainer hook placement: this sub-skill.

## Hook stages

Register hooks with `trainer.register_op(dest, op, **kwargs)` or `register_hook` alias.

| Stage | Input/output expectation | Common use | Notes |
| --- | --- | --- | --- |
| `setup` / `shutdown` | no TensorDict | resource initialization and cleanup | Allowed with local and ray learner backends. |
| `batch_process` | `TensorDict -> TensorDict` | extend replay, normalize or filter collected batch | Safe for replay ingestion hooks. |
| `pre_optim_steps` | no TensorDict | clear caches, pre-update side effects | Local optimization loop only. |
| `process_optim_batch` | `TensorDict -> TensorDict` | sample replay/minibatches, normalize sampled batch | Local optimization loop only. |
| `process_loss` | `TensorDict -> TensorDict` | transform loss output before optimizer | Emits a future-warning in current source; prefer custom `OptimizationStepper` for new designs. |
| `optimizer` | loss TensorDict/optimizer call contract | legacy optimizer hook | Emits a future-warning; prefer `DefaultOptimizationStepper` or explicit optimizer. |
| `post_loss` | `TensorDict -> TensorDict` | replay priority update in older examples | Emits a future-warning; for new code prefer `post_optim` or an `OptimizationStepper` that owns priority updates. |
| `post_optim` | no TensorDict | target-network updater step | Good place for `TargetNetUpdaterHook` or `target_updater.step`. |
| `post_steps` | no TensorDict | collector weight sync, exploration schedule step | `UpdateWeights` commonly registers here. |
| `pre_steps_log`, `post_steps_log`, `post_optim_log`, `pre_epoch_log`, `post_epoch_log` | returns `(name, scalar)` | custom metrics | Input is the current batch for most log hooks. |
| `post_optim_complete_log` | `(optim_count, averaged_losses) -> (name, scalar)` | summary logging after optimization loop | Works with averaged loss TensorDict. |
| `pre_epoch`, `post_epoch` | no TensorDict | epoch-level side effects | Local training loop hooks. |

When `learner_backend='ray'`, only a reduced set of local-side stages is available: `batch_process`, `post_steps`, `pre_steps_log`, `post_steps_log`, `setup`, and `shutdown`. Move optimization-side logic into an optimizer/learner-owned component for remote learners.

## Common hook helper classes

| Helper | Signature summary | Register/use pattern |
| --- | --- | --- |
| `ReplayBufferTrainer` | `(replay_buffer, batch_size=None, memmap=False, device=None, flatten_tensordicts=False, max_dims=None, iterate=False)` | Typical legacy pattern: register `extend` at `batch_process`, `sample` at `process_optim_batch`, `update_priority` after loss/optimization. |
| `UpdateWeights` | `(collector, update_weights_interval, policy_weights_getter=None, weight_update_map=None, trainer=None)` | Registers or is registered at `post_steps` to sync learner policy weights to collectors. |
| `BatchSubSampler` | `(batch_size, sub_traj_len=0, min_sub_traj_len=0)` | Use for recurrent or trajectory minibatches where time/sub-trajectory length matters. |
| `OptimizerHook` | `(optimizer, loss_components=None)` | Legacy optimizer hook; new code should consider `OptimizationStepper`. |
| `TargetNetUpdaterHook` | `(target_params_updater)` | Register at `post_optim` or `post_steps` depending on whether cadence is optimizer-step or collection-step based. |
| `ValueEstimatorHook` | `(value_estimator)` | Registers estimator application, typically before optimization over on-policy data. |

## Hydra algorithm configs

Algorithm config dataclasses live under `torchrl/trainers/algorithms/configs/`. Objective config evidence is concentrated in `configs/objectives.py` and trainer config evidence in `configs/trainers.py`.

Objective configs currently cover or dispatch key loss families including:

- `SACLossConfig` for `SACLoss` and `DiscreteSACLoss`;
- `TQCLossConfig`;
- `PPOLossConfig` dispatching `ClipPPOLoss`, `KLPENPPOLoss`, and `PPOLoss`;
- `A2CLossConfig`;
- `ReinforceLossConfig`;
- `DQNLossConfig`;
- `QMixerLossConfig`;
- `DDPGLossConfig`;
- `TD3LossConfig`;
- `IQLLossConfig` for continuous/discrete variants;
- `CQLLossConfig`.

Config factories often instantiate nested config objects, pop keys that the raw constructor rejects, call `loss.set_keys(...)`, and call `loss.make_value_estimator(gamma=...)` after construction. This is intentional and should be preserved.

## Config/class parity rules for edits

When adding, removing, or changing a public loss/trainer constructor kwarg:

1. Update the matching `*Config` dataclass field with the same default and compatible type.
2. Update the `_make_*` factory so unsupported helper fields are popped before constructing the loss and supported fields are forwarded.
3. If a field configures a TensorDict key, expose it as a config field such as `action_key` or `reward_key`, normalize Hydra list/tuple forms, then call `loss.set_keys(action=..., reward=...)`.
4. If a field configures discount/estimator behavior that the raw constructor rejects, route it through `loss.make_value_estimator(...)` rather than passing it to `__init__`.
5. Update tests in existing objective/config test files and docs/reference entries for the public class/function.
6. If the change affects SOTA algorithms, update the relevant config YAML and trainer/non-trainer recipe consistently.

TorchRL project rules require public signatures to be typed, new public classes/functions to have docs/tests, and Hydra `*Config` parity for trainers/losses/replay/transforms. Do not add a new loss kwarg in source only.

## Patterns for common algorithms

### DQN trainer pattern

```python
loss = DQNLoss(q_actor, delay_value=True)
loss.make_value_estimator(gamma=gamma)
target_updater = SoftUpdate(loss, eps=0.995)
trainer = Trainer(
    collector=collector,
    total_frames=total_frames,
    frame_skip=frame_skip,
    optim_steps_per_batch=optim_steps,
    loss_module=loss,
    optimizer=optimizer,
)
trainer.register_op("post_optim", target_updater.step)
trainer.register_op("post_steps", weight_updater)
```

Add replay ingestion/sampling hooks via `ReplayBufferTrainer` only after collector/replay ownership is settled.

### PPO trainer/manual pattern

PPO often runs a manual loop or trainer loop where a value estimator is applied to collected data before minibatches:

```python
loss = ClipPPOLoss(policy, critic)
loss.make_value_estimator(ValueEstimators.GAE, gamma=gamma, lmbda=lmbda)
with torch.no_grad():
    loss.value_estimator(batch)
```

If the actor/critic use nested keys, call `loss.set_keys(...)` before constructing/applying the estimator.

### Multi-agent trainer pattern

Use `MAPPOLoss`/`IPPOLoss` when the critic value shape contains an agent dimension. Keep `normalize_advantage_exclude_dims=(-2,)` unless the agent dimension is elsewhere. If a tutorial-style loop expands root done/terminated to `("agents", ...)`, preserve that expansion before GAE.

## Avoid common trainer/config mistakes

- Do not register target updates at collection cadence when the algorithm requires optimizer-step cadence.
- Do not use `post_loss` for new priority-update logic without noting the future-warning; prefer `post_optim` or an `OptimizationStepper`.
- Do not pass Hydra list keys directly to `set_keys` when a tuple `NestedKey` is intended; normalize them first.
- Do not add optional simulator, Ray, or LLM dependencies to a config smoke just because a SOTA recipe references them.
- Do not forget docs/tests/SOTA config parity when changing a public trainer or loss signature.
