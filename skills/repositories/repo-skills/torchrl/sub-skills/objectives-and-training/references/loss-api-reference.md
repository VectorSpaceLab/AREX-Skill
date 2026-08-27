# Loss API reference

Evidence used for this reference: `torchrl/objectives/`, `docs/source/reference/objectives*.rst`, `test/objectives/`, `test/compile/`, trainer config code, tutorials, and inspected package signatures. Paths are provenance only, not runtime dependencies.

## Core TorchRL loss contract

- Losses inherit from `torchrl.objectives.LossModule`: they read and write `TensorDict` data and return a `TensorDict` whose optimization tensors are named `loss_*`.
- Configurable input/output TensorDict keys live in an `_AcceptedKeys` dataclass. Call `loss.set_keys(accepted_name=nested_key)`; do not guess constructor keyword names when the loss exposes `set_keys`.
- Most bootstrapped losses expose `loss.make_value_estimator(...)`; the resulting `loss.value_estimator` must see the same reward/done/terminated/value keys as the loss.
- `loss.loss_mask_key` defaults to `"auto"` and discovers TorchRL validity masks such as collector masks and `shifted_valid`. Set it to a `NestedKey` for one custom mask or `None` to disable masking.
- When a loss has target parameters (`delay_value`, `delay_qvalue`, or `delay_actor`), create a `SoftUpdate` or `HardUpdate` object and call `step()` after optimizer steps.

## Loss selection by algorithm family

| Task family | Use these loss classes | Required modules/data | Key operating notes |
| --- | --- | --- | --- |
| PPO / clipped policy gradient | `ClipPPOLoss`; `KLPENPPOLoss` for KL-penalty; `PPOLoss` parent | Probabilistic actor, critic/value operator, on-policy collector batch | Default value estimator is `ValueEstimators.GAE`. The loss consumes `advantage`, `value_target`, `state_value`, `action_log_prob`, `action`, and `("next", reward/done/terminated)`. Compute advantage before minibatch optimization. |
| A2C / REINFORCE | `A2CLoss`, `ReinforceLoss` | Probabilistic actor, optional critic depending on algorithm | Same on-policy advantage/value-target pattern as PPO. `gamma`, `advantage_key`, and `value_target_key` are handled through `make_value_estimator` and `set_keys` in trainer configs. |
| DQN / distributional DQN | `DQNLoss`, `DistributionalDQNLoss` | `QValueActor` or equivalent Q module, discrete action spec/space, replay samples | Default value estimator is `TD0`. Use target updates when `delay_value=True`. Prioritized replay uses `priority_weight` input and writes `td_error` by default. Distributional DQN also uses `steps_to_next_obs`. |
| Continuous off-policy actor-critic | `DDPGLoss`, `TD3Loss`, `SACLoss`, `TQCLoss`, `REDQLoss`, `CrossQLoss` | Actor, Q/value networks, continuous `action_spec`, replay samples with current and next fields | Prefer passing an explicit `action_spec` for stochastic actor losses. Ensemble Q losses may use `vmap`; set `deactivate_vmap=True` only for debugging or unsupported modules. Target updates are usually required. |
| Offline RL | `CQLLoss`, `DiscreteCQLLoss`, `IQLLoss`, `DiscreteIQLLoss`, `TD3BCLoss`, `BCLoss`, `DTLoss`, `OnlineDTLoss`, `DiffusionBCLoss` | Offline dataset batches with behavior actions, rewards, done/terminated, and next observations; algorithm-specific actor/critic modules | CQL/IQL still need bootstrapped next-state fields. BC/DT/Diffusion BC focus on action targets and may not need a value estimator. Do not mix online replay assumptions into a static offline dataset unless the algorithm recipe requires it. |
| Multi-agent objectives | `MAPPOLoss`, `IPPOLoss`, `QMixerLoss` | Per-agent tensors under group keys such as `("agents", "action")`; centralized or decentralized critic per algorithm | `MAPPOLoss`/`IPPOLoss` default to `ValueEstimators.MAGAE` and exclude the agent dim `(-2,)` from advantage normalization. `QMixerLoss` uses local agent Q values and a global mixed value. |
| Model-based / auxiliary | `DreamerModelLoss`, `DreamerActorLoss`, `DreamerValueLoss`, DreamerV3 losses, `WorldModelLoss`, `GAILLoss`, `RNDLoss`, `ExponentialQuadraticCost`, `ACTLoss` | Algorithm-specific model, discriminator, reward, or world-model data | Treat these as specialized workflows. Verify expected TensorDict keys with `inspect_loss_keys.py` and the source tests before editing. |

## Observed constructor signatures

Use `scripts/inspect_loss_keys.py` for a fresh local read. During skill drafting, these package facts were observed:

```text
ClipPPOLoss(actor_network=None, critic_network=None, *, clip_epsilon=0.2, entropy_bonus=True, samples_mc_entropy=1, entropy_coeff=None, critic_coeff=None, loss_critic_type='smooth_l1', normalize_advantage=False, normalize_advantage_exclude_dims=(), gamma=None, separate_losses=False, reduction=None, clip_value=None, device=None, **kwargs)
SACLoss(actor_network, qvalue_network, value_network=None, *, num_qvalue_nets=2, loss_function='smooth_l1', alpha_init=1.0, min_alpha=None, max_alpha=None, action_spec=None, fixed_alpha=False, target_entropy='auto', delay_actor=False, delay_qvalue=True, delay_value=True, gamma=None, priority_key=None, separate_losses=False, reduction=None, skip_done_states=False, deactivate_vmap=False, use_prioritized_weights='auto', scalar_output_mode=None)
DQNLoss(value_network, *, loss_function='l2', delay_value=True, double_dqn=False, gamma=None, action_space=None, priority_key=None, reduction=None, use_prioritized_weights='auto')
DDPGLoss(actor_network, value_network, *, loss_function='l2', delay_actor=False, delay_value=True, gamma=None, separate_losses=False, reduction=None, use_prioritized_weights='auto')
TD3Loss(actor_network, qvalue_network, *, action_spec=None, bounds=None, num_qvalue_nets=2, policy_noise=0.2, noise_clip=0.5, loss_function='smooth_l1', delay_actor=True, delay_qvalue=True, gamma=None, priority_key=None, separate_losses=False, reduction=None, deactivate_vmap=False, use_prioritized_weights='auto')
IQLLoss(actor_network, qvalue_network, value_network, *, num_qvalue_nets=2, loss_function='smooth_l1', temperature=1.0, expectile=0.5, gamma=None, priority_key=None, separate_losses=False, reduction=None, deactivate_vmap=False, scalar_output_mode=None)
CQLLoss(actor_network, qvalue_network, *, loss_function='smooth_l1', alpha_init=1.0, min_alpha=None, max_alpha=None, action_spec=None, fixed_alpha=False, target_entropy='auto', delay_actor=False, delay_qvalue=True, gamma=None, temperature=1.0, min_q_weight=1.0, max_q_backup=False, deterministic_backup=True, num_random=10, with_lagrange=False, lagrange_thresh=0.0, reduction=None, deactivate_vmap=False, scalar_output_mode=None)
MAPPOLoss(actor_network=None, critic_network=None, *, value_norm=None, entropy_coeff=0.01, normalize_advantage=True, normalize_advantage_exclude_dims=(-2,), **kwargs)
SoftUpdate(loss_module, *, eps=None, tau=None)
HardUpdate(loss_module, *, value_network_update_interval=1000)
ValueEstimators: TD0, TD1, TDLambda, GAE, MAGAE, VTrace
```

## Default key maps to check first

| Class family | Default configurable keys |
| --- | --- |
| `PPOLoss`, `ClipPPOLoss`, `KLPENPPOLoss` | `advantage='advantage'`, `value_target='value_target'`, `value='state_value'`, `sample_log_prob='action_log_prob'`, `action='action'`, `reward='reward'`, `done='done'`, `terminated='terminated'` |
| `MAPPOLoss`, `IPPOLoss` | Same PPO key names, but use multi-agent nested values such as `value=("agents", "state_value")`, `action=("agents", "action")`, and agent-expanded done/terminated when required. |
| `SACLoss`, `TQCLoss` | `action='action'`, `value='state_value'`, `state_action_value='state_action_value'`, `log_prob='action_log_prob'`, `priority='td_error'`, `reward='reward'`, `done='done'`, `terminated='terminated'`, `priority_weight='priority_weight'` |
| `DQNLoss` | `advantage='advantage'`, `value_target='value_target'`, `value='chosen_action_value'`, `action_value='action_value'`, `action='action'`, `priority='td_error'`, `reward='reward'`, `done='done'`, `terminated='terminated'`, `priority_weight='priority_weight'` |
| `DistributionalDQNLoss` | `action_value='action_value'`, `action='action'`, `priority='td_error'`, `reward='reward'`, `done='done'`, `terminated='terminated'`, `steps_to_next_obs='steps_to_next_obs'`, `priority_weight='priority_weight'` |
| `DDPGLoss` | `state_action_value='state_action_value'`, `priority='td_error'`, `reward='reward'`, `done='done'`, `terminated='terminated'`, `priority_weight='priority_weight'` |
| `TD3Loss`, `TD3BCLoss` | `action='action'`, `state_action_value='state_action_value'`, `priority='td_error'`, `reward='reward'`, `done='done'`, `terminated='terminated'`, `priority_weight='priority_weight'` |
| `IQLLoss`, `DiscreteIQLLoss` | `value='state_value'`, `action='action'`, `log_prob='_log_prob'`, `priority='td_error'`, `state_action_value='state_action_value'`, `reward='reward'`, `done='done'`, `terminated='terminated'` |
| `CQLLoss` | `action='action'`, `value='state_value'`, `state_action_value='state_action_value'`, `log_prob='_log_prob'`, `pred_q1='pred_q1'`, `pred_q2='pred_q2'`, `priority='td_error'`, `cql_q1_loss='cql_q1_loss'`, `cql_q2_loss='cql_q2_loss'`, `reward='reward'`, `done='done'`, `terminated='terminated'` |
| `DiscreteCQLLoss` | `value_target='value_target'`, `value='chosen_action_value'`, `action_value='action_value'`, `action='action'`, `priority='td_error'`, `reward='reward'`, `done='done'`, `terminated='terminated'`, `pred_val='pred_val'` |
| `QMixerLoss` | `local_value=("agents", "chosen_action_value")`, `global_value='chosen_action_value'`, `action_value=("agents", "action_value")`, `action=("agents", "action")`, plus `advantage`, `value_target`, `priority`, `reward`, `done`, `terminated` |
| `BCLoss` | `action='action'`, `pad_mask=None` |
| `DTLoss`, `OnlineDTLoss` | `action_target='action'`, `action_pred='action'` |
| `GAILLoss` | `expert_action='action'`, `expert_observation='observation'`, `collector_action='collector_action'`, `collector_observation='collector_observation'`, `discriminator_pred='d_logits'` |
| `RNDLoss` | `observation=("next", "observation")` |

## `set_keys` and `_AcceptedKeys` rules

- Accepted names are the dataclass field names (`action`, `reward`, `priority_weight`), not necessarily constructor fields ending with `_key`.
- A `NestedKey` may be a string or tuple. For nested multi-agent data, prefer tuples: `loss.set_keys(action=("agents", "action"), value=("agents", "state_value"))`.
- Passing `None` to `set_keys` resets that key to the loss default.
- If a key is changed after a value estimator was constructed, verify the change propagated. When in doubt, call `loss.set_keys(...)` first, then `loss.make_value_estimator(...)`, or explicitly call `loss.value_estimator.set_keys(...)` for estimator-specific keys.
- Constructor key kwargs marked deprecated in source should be replaced with `set_keys`; trainer configs may keep user-facing `*_key` fields but route them through factories.

## Value estimators and next-state fields

`ValueEstimators` contains `TD0`, `TD1`, `TDLambda`, `GAE`, `MAGAE`, and `VTrace`. Registry defaults include `gamma=0.99` for all built-ins and `lmbda=0.95` for `TDLambda`, `GAE`, and `MAGAE`.

Losses generally expect current-step model outputs at root keys and transition targets under `"next"`:

```python
loss.set_keys(reward="reward", done="done", terminated="terminated")
# The value estimator then reads ("next", "reward"), ("next", "done"),
# ("next", "terminated") plus whatever next observation/value keys the model uses.
loss.make_value_estimator(ValueEstimators.TD0, gamma=0.99)
```

For PPO-style losses, either run a standalone `GAE` module before the loss or call `loss.make_value_estimator(ValueEstimators.GAE, gamma=..., lmbda=...)` and apply `loss.value_estimator(batch)` before minibatch loss calls so `advantage` and `value_target` exist.

## Target-network updates

- `SoftUpdate(loss_module, tau=...)` or `SoftUpdate(loss_module, eps=...)`: pass exactly one of `tau` or `eps`. `tau` is the Polyak interpolation weight; internally `eps = 1 - tau`.
- `HardUpdate(loss_module, value_network_update_interval=N)`: copies source parameters to target every `N` calls.
- Create the updater after the loss so target parameters are registered. Call `step()` after the optimizer step, commonly in a `post_optim` trainer hook or in the manual loop.
- If updater construction fails with no target parameters, confirm the loss was created with the relevant `delay_*` flag enabled and that a target updater is actually needed.

## Prioritized replay weights

`DQNLoss`, `SACLoss`, `DDPGLoss`, `TD3Loss`, `TQCLoss`, and `TD3BCLoss` support `use_prioritized_weights` in current inspected APIs. With prioritized replay:

1. The replay buffer sample should contain `priority_weight` unless the key was remapped.
2. The loss writes priority/TD-error under `td_error` by default.
3. After optimization, pass the batch back to replay priority update logic so sampled priorities change.
4. If losses become shape-inconsistent, inspect `reduction`, `loss_mask_key`, sequence sampler padding masks, and `priority_weight` broadcasting.

## `vmap` and `deactivate_vmap`

Several ensemble-Q losses use vectorized calls over duplicated Q networks. Keep the default vectorized path for normal training. Set `deactivate_vmap=True` only when debugging a module that is not vmap-compatible, when module side effects break vectorization, or when comparing against a non-vectorized reference. If `deactivate_vmap=True` fixes the issue, route the module implementation details to `modules-and-policies` before accepting the slower path.
