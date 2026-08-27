# Troubleshooting modules and policies

Start every investigation by printing or asserting `td.keys(True, True)`, relevant tensor shapes, and the policy module's `in_keys` / `out_keys`. Most TorchRL module failures are key-contract or spec-contract failures.

## Quick diagnosis table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `KeyError` for an observation, hidden, or parameter key | `in_keys` do not match TensorDict keys | Inspect recursive keys; use tuple nested keys; update wrapper `in_keys`. |
| `RuntimeError` about output keys/spec keys | `SafeModule`/`Actor` spec keys do not match `out_keys` | Use a `Composite` spec with exactly matching keys, or one non-composite spec for one output. |
| Probabilistic actor says a distribution arg is missing | Parameter module wrote wrong names | Use `in_keys` dict mapping distribution argument names to TensorDict keys. |
| Action is outside bounds | Distribution is not bounded, spec missing, or `safe=False` | Use `TanhNormal`/bounded distribution, pass action spec, and optionally enable `safe=True`. |
| `sample_log_prob` missing for PPO-style code | `return_log_prob=False` or wrong `log_prob_key` | Set `return_log_prob=True` and align the key with the objective. |
| Q-value actor chooses invalid action | Missing or wrong `action_mask_key` | Pass `action_mask_key` and assert mask shape matches action values. |
| Recurrent policy fails on missing hidden key | Primer not added or manual TensorDict not primed | Use recurrent primers in env setup or add zero hidden tensors manually for synthetic data. |
| Recurrent training leaks state across episodes | `is_init` missing, always false, or dropped by replay/transform | Preserve `is_init` and sample contiguous sequence slices. |
| Shape mismatch in recurrent mode | Time/batch dims or hidden layout mismatch | Use TensorDict batch shape plus `[num_layers, hidden_size]`; keep `batch_first=True` unless necessary. |
| Multi-agent model shape mismatch | Wrong `agent_dim` or nested per-agent keys fed to grouped model | Stack per-agent tensors or adjust `agent_dim`; keep grouped layout consistent. |

## `in_keys` / `out_keys` mismatch

Checklist:

1. Inspect recursive keys:
   ```python
   print(sorted(td.keys(True, True)))
   print(module.in_keys, module.out_keys)
   ```
2. For nested data, use tuple keys exactly:
   ```python
   in_keys=[('obs', 'state')]
   out_keys=[('policy', 'loc'), ('policy', 'scale')]
   ```
3. If a plain `nn.Module` receives multiple inputs, `in_keys` order is the positional argument order.
4. If a wrapped module returns a tuple, the tuple length must match `out_keys` length.
5. Avoid overwriting a key that a later module still needs unless the overwrite is intentional.

Difficult case: actor and critic built from nested observation specs. Use a small adapter body for each consumer rather than flattening the entire TensorDict. Example layout:

```text
('obs', 'state')       -> actor body -> action, sample_log_prob
('obs', 'state'), action -> critic body -> state_action_value
('obs', 'pixels')      -> untouched for other components
```

If the critic fails after actor execution, first confirm the actor did not overwrite the nested observation key.

## Missing distribution parameters

`ProbabilisticActor` constructs a distribution from TensorDict entries. Distribution constructor names matter.

Common examples:

```text
Normal/TanhNormal: loc, scale
Categorical/MaskedCategorical: logits or probs, optional mask
CompositeDistribution: grouped parameter tree plus distribution/name maps
```

Fix patterns:

- Rename module outputs to constructor names:
  ```python
  out_keys=['loc', 'scale']
  in_keys=['loc', 'scale']
  ```
- Or map argument names to arbitrary TensorDict keys:
  ```python
  in_keys={'loc': ('policy', 'mu'), 'scale': ('policy', 'sigma')}
  ```
- For `scale`, use a positive parameterization such as `NormalParamExtractor` or `softplus` plus epsilon.
- For `MaskedCategorical`, ensure the mask is boolean and broadcast-compatible with logits.

## Action bounds and spec projection

Symptoms:

- Continuous actions exceed environment bounds.
- `safe=True` raises because no spec was provided.
- Spec keys differ from output keys.

Fixes:

1. Prefer bounded distributions for bounded action spaces:
   ```python
   distribution_class=TanhNormal
   distribution_kwargs={'low': -1.0, 'high': 1.0}
   ```
2. Pass `spec=action_spec` to `Actor` / `ProbabilisticActor` when writing `action`.
3. For `SafeModule` with custom output keys, use matching `Composite` specs:
   ```python
   spec = Composite({'bounded_action': action_spec})
   SafeModule(net, in_keys=['x'], out_keys=['bounded_action'], spec=spec, safe=True)
   ```
4. Use spec projection as a guardrail. If every sample needs projection, fix the distribution or network output parameterization.

## Q-value actors and action masks

`QValueActor` wraps an action-value network and appends greedy action selection.

Debug steps:

1. Confirm the network writes the expected `action_value_key`.
2. Confirm `action_value.shape[-1]` matches the discrete action cardinality.
3. Provide `spec` or `action_space`; specs carry dtype/shape and are less ambiguous.
4. If using masks, assert:
   ```python
   assert td['action_mask'].dtype is torch.bool
   assert td['action_mask'].shape == td['action_value'].shape
   ```
5. For categorical specs with singleton action dimensions, use `strict_shape='auto'` when appropriate.

## Recurrent hidden keys and primers

The most common recurrent failure is a TensorDict that contains observations but no recurrent hidden state.

Minimal manual priming for a GRU one-step batch:

```python
td['rs'] = torch.zeros(*td.batch_size, 1, hidden_size)
td['is_init'] = torch.ones(*td.batch_size, 1, dtype=torch.bool)
```

For an LSTM:

```python
td['rs_h'] = torch.zeros(*td.batch_size, 1, hidden_size)
td['rs_c'] = torch.zeros(*td.batch_size, 1, hidden_size)
td['is_init'] = torch.ones(*td.batch_size, 1, dtype=torch.bool)
```

In environment/collector workflows, use the module's recurrent primer instead of hand-written hidden tensors. The primer registers hidden specs and fills reset TensorDicts. When a policy has multiple recurrent modules, use distinct hidden keys such as `actor_rs` and `critic_rs`.

Difficult case: recurrent policy fails because hidden keys or the reset signal are missing, then is fixed with primers or manual hidden-state priming. The bundled [recurrent smoke script](../scripts/smoke_recurrent_actor.py) covers the reset-signal variant as an assertion-backed example.

## `is_init` and trajectory boundaries

`is_init` is required for correct hidden reset behaviour.

- Missing `is_init`: usually a quick `KeyError`.
- Present but all false: dangerous silent leakage across episodes.
- Dropped by replay/transform: recurrent training diverges or depends on batch slicing.

Fixes:

1. Ensure env reset/collector output includes `is_init`.
2. Preserve `is_init` through transforms and replay buffers.
3. During sequence training, use trajectory-aware sampling so slices remain contiguous.
4. Wrap custom sequence forwards in `with set_recurrent_mode(True):`.

## `batch_first` and recurrent shapes

With default `batch_first=True`, TensorDict batch dimensions come first and the time dimension is the last TensorDict batch dimension in recurrent mode.

Examples:

```text
one-step batch [B]
  observation: [B, obs_dim]
  GRU hidden:  [B, num_layers, hidden_size]

sequence batch [B, T]
  observation: [B, T, obs_dim]
  GRU hidden:  [B, T, num_layers, hidden_size]
```

Do not pass PyTorch's raw RNN hidden layout `[num_layers, batch, hidden]` as a TensorDict hidden key unless you have intentionally reshaped it to match the TensorDict layout.

## Recurrent backend limitations

- Use `pad` as the default correctness baseline and for CPU helper scripts.
- Use `scan` for compile-friendly recurrent batches after confirming the module configuration is supported.
- Use `triton` only on CUDA/Triton-capable setups. It is optional backend coverage and should not be described as verified unless tested.
- `recurrent_recompute='full'` is backend-dependent; unsupported combinations raise.
- Dropout, bidirectionality, projections, and multi-layer configurations can change backend support. Reproduce with a tiny batch before launching long training.

## Multi-agent tensor grouping

Symptoms:

- `MultiAgentMLP` raises that output dimension does not equal `n_agents`.
- Model sees flattened agent observations when it expected grouped observations.
- Critic output has agent dimension where the loss expected a scalar/team value.

Fixes:

1. Decide grouped tensor layout: `[..., n_agents, feature_dim]`.
2. Pass the correct `agent_dim`, commonly `-2`.
3. Use `centralized=True` only when the model should see all agents jointly.
4. Use `share_params=True` for one shared network across agents; `False` for per-agent parameters.
5. If environment keys are per-agent nested leaves, stack them before `MultiAgentMLP` and unstack actions afterwards.
6. For recurrent multi-agent policies, include agent grouping in hidden-state shape and avoid one hidden key being shared by unrelated modules.

## When to stop and reroute

Stop this sub-skill and reroute when:

- The failure is an environment spec, transform, reset, or rollout problem.
- The failure is a loss `set_keys`, advantage estimator, target updater, trainer, or optimizer problem.
- The policy wrapper requires LLM/VLA model-serving dependencies, tokenizers, datasets, or external services.
- The task is about code contribution rules, CI labels, docs, or tests rather than runtime API assembly.
