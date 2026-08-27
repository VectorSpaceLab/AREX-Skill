# Objectives and training troubleshooting

Start here when a TorchRL loss forward pass, value estimator, target updater, trainer hook, or Hydra config fails.

## Quick diagnostic order

1. Run `scripts/inspect_loss_keys.py --loss <LossClass>` to confirm signature, `set_keys`, default keys, and default value estimator.
2. Print `batch.keys(True, True)` and compare to `loss.tensor_keys`.
3. Check that all transition targets are nested under `"next"`: reward, done, terminated, and next observations/values used by the value estimator.
4. Check actor/critic module `in_keys`/`out_keys` and action spec ownership in `modules-and-policies` and `envs-and-transforms`.
5. Check replay sample metadata and `priority_weight` ownership in `collectors-and-replay`.
6. Only after keys and shapes match, debug optimizer/trainer hook cadence.

## Symptom-to-fix table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `KeyError` for `action`, `state_value`, `action_log_prob`, `reward`, or a nested agent key | Loss default keys do not match actor/critic/replay batch keys | Inspect accepted keys and call `loss.set_keys(...)`. Use tuple `NestedKey`s for nested data, e.g. `("agents", "action")`. |
| `ValueError: <key> is not an accepted tensordict key` from `set_keys` | Used constructor-style `*_key` name or misspelled `_AcceptedKeys` field | Use accepted field names such as `action`, `reward`, `done`, `terminated`, `priority_weight`; configs may expose `action_key` but factories must call `set_keys(action=...)`. |
| Value estimator fails on missing `("next", "reward")`, `("next", "done")`, or `("next", "terminated")` | Batch is not a TorchRL transition TensorDict or `step_mdp`/collector layout was altered | Restore `"next"` layout. If custom names are required, call `loss.set_keys(reward=..., done=..., terminated=...)` before `make_value_estimator`. |
| PPO loss says `advantage` or `value_target` is missing | GAE/value estimator was not applied to the batch before minibatch loss | Run `loss.value_estimator(batch)` under `torch.no_grad()` before optimization, or run a standalone `GAE` module that writes the expected keys. |
| PPO/MAPPO advantage normalization gives poor shapes or errors | Normalization includes the agent dimension or wrong time dimension | For multi-agent losses keep `normalize_advantage_exclude_dims=(-2,)` when the agent dimension is second-to-last, or set `normalize_advantage=False` for tutorial-style MAPPO. |
| MAPPO value estimator cannot broadcast done/reward | Team-shared reward/done tensors do not match per-agent value shape | Expand root `("next", "done")` and `("next", "terminated")` to per-agent shape when needed, or use `MAPPOLoss`/`MAGAE` with the documented multi-agent layout. |
| SAC/TD3/CQL action bounds or target entropy errors | Missing or wrong `action_spec`; actor distribution bounds do not match env action spec | Route spec construction to `envs-and-transforms`; pass `action_spec` to the loss when supported; verify actor outputs are projected or bounded consistently. |
| Target updater raises no target parameters found | Loss was built without delayed target networks or the algorithm does not need a target updater | Enable the relevant `delay_value`, `delay_qvalue`, or `delay_actor` flag, or remove the updater. Instantiate updater after loss construction. |
| Target network warning before forward | Loss has target parameters but no updater was associated | Create `SoftUpdate`/`HardUpdate` and call `step()` at the algorithm cadence, or explicitly document manual target updates. |
| Hard target update never seems to happen | `HardUpdate.step()` is called at the wrong cadence or interval is too large | Count optimizer steps, not collector batches, unless the algorithm says otherwise. Register at `post_optim` for optimizer-step cadence. |
| Prioritized replay weights ignored or shape mismatch | Replay sample lacks `priority_weight`, key was remapped inconsistently, or loss reduction masks changed shape | Configure `priority_weight` with `set_keys`, ensure sampler writes the key, and update replay priorities from the batch after loss. Check `loss_mask_key` and sequence padding masks. |
| `td_error` is missing after loss | `priority` key was remapped or priority output disabled by the algorithm | Inspect `loss.tensor_keys.priority` and update replay with that key. For losses without priority support, do not force prioritized updates. |
| `vmap` error in SAC/TD3/IQL/CQL/REDQ/TQC/CrossQ | Q ensemble module has side effects, unsupported control flow, or incompatible parameter structure | First fix the module in `modules-and-policies`. For diagnosis, set `deactivate_vmap=True` and compare outputs; keep it only if performance trade-off is acceptable. |
| Compile test fails on objective | Data-dependent shapes, `.item()` in hot path, unsupported vmap/module behavior, or non-static key structure | Reduce to the smallest objective test, preserve TensorDict key stability, and check `test/compile/` patterns before changing public behavior. |
| Hydra config instantiation passes an unknown kwarg to a loss | Config field is forwarded to the wrong concrete loss or helper fields were not popped | Update `_make_*` factory to dispatch by loss type, pop irrelevant fields, normalize keys, then call `set_keys` or `make_value_estimator`. |
| New loss kwarg works in Python but not Hydra | Missing config/class parity | Add the field to the matching `*Config` dataclass with the same default, forward/pop correctly in the factory, add tests, update docs/reference, and update affected SOTA configs. |
| Trainer hook is rejected with `learner_backend='ray'` | Hook stage runs inside the local optimization loop and is unavailable for remote learners | Move the behavior into an `OptimizationStepper` or learner-owned component, or use only the allowed local-side hook stages. |
| `post_loss`/`optimizer` hook warning appears | Legacy trainer hook stage is used | For new code, prefer `post_optim`, `DefaultOptimizationStepper`, or a custom `OptimizationStepper`. Existing tutorials may still show older patterns. |

## Debugging missing nested keys

Use this pattern before editing the loss:

```python
print("batch keys:", sorted(map(str, batch.keys(True, True))))
print("loss keys:", loss.tensor_keys)

# Example: actor writes nested multi-agent actions but loss defaults to root action.
loss.set_keys(
    action=("agents", "action"),
    value=("agents", "state_value"),
    reward="reward",
    done="done",
    terminated="terminated",
)
loss.make_value_estimator(ValueEstimators.MAGAE, gamma=0.99, lmbda=0.95)
```

If the value estimator was already built before remapping, either call `loss.value_estimator.set_keys(...)` with the estimator's accepted names or rebuild it after `loss.set_keys(...)`.

## Wrong action spec checklist

- Does the environment expose a continuous or discrete action spec compatible with the loss?
- Does the actor distribution use the same low/high bounds or categorical/one-hot convention?
- Does the loss constructor accept `action_spec`, `bounds`, or `action_space`, and was the correct one passed?
- Did a transform such as action scaling change the action key or inverse key? Route transform details to `envs-and-transforms`.
- For DQN-like losses, is `action_space` one-hot/categorical/index aligned with `QValueActor` output?

## Value-estimator key checklist

- `reward`, `done`, and `terminated` keys in `loss.tensor_keys` refer to base names; estimators usually read them under `"next"`.
- `GAE` and `MAGAE` write `advantage` and `value_target`.
- `TD0`, `TD1`, and `TDLambda` require next values or next observations sufficient for the target network.
- `VTrace` has actor/log-prob dependencies; do not swap it into a loss that does not support it.
- If using custom names, set them on the loss and confirm they propagate to `loss.value_estimator`.

## Prioritized replay checklist

1. Replay buffer sampler returns an importance key such as `priority_weight`.
2. Loss was created with `use_prioritized_weights=True` or `"auto"` and the key exists.
3. Loss writes `loss.tensor_keys.priority`, usually `td_error`.
4. A post-optimization step updates replay priorities from the same batch.
5. Reductions and masks do not collapse the priority tensor shape expected by replay.

## Hydra parity repair checklist

When a user adds a loss kwarg and Hydra breaks:

1. Compare `inspect.signature(LossClass)` to the matching `*Config` dataclass.
2. Add the field with the same default and type.
3. In `_make_*`, instantiate nested config objects before constructing the loss.
4. Pop helper-only fields such as `gamma`, `*_key`, or variant selectors before calling a raw loss constructor that does not accept them.
5. For `*_key` fields, normalize Hydra list/tuple values and call `loss.set_keys(...)`.
6. For discount/estimator fields, call `loss.make_value_estimator(...)` after construction.
7. Extend existing tests; do not create new test files unless adding a brand-new objective.
8. Update docs/reference and SOTA configs when user-facing behavior changes.

## Difficult usability cases for verification

- **Config parity edit:** Add a synthetic kwarg to a small loss in a local branch and require the agent to identify all matching `*Config`, factory, docs, and tests that must change, including the case where the raw constructor rejects `gamma` and the factory must route it through `make_value_estimator`.
- **Nested-key loss failure:** Build a tiny multi-agent TensorDict whose actor outputs `("agents", "action")` and critic outputs `("agents", "state_value")`, then show that the default PPO key map fails until `loss.set_keys(...)` and `MAGAE`/agent-done expansion are applied.
