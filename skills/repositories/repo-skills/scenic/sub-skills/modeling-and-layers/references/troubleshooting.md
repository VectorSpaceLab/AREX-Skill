# Troubleshooting

Use this reference when the model registry, Flax module construction, metric aggregation, matcher dependencies, or checkpoint loading behave unexpectedly.

## Unrecognized model

**Symptom:** `get_model_cls(name)` raises `ValueError('Unrecognized model: ...')`.

**Check:**

1. Run [`scripts/model_registry_probe.py`](../scripts/model_registry_probe.py) to confirm the registered name spelling.
2. Verify that the config uses the exact registry key, not a class name or project name.
3. Confirm that the new model class is registered before you try to instantiate it.

**Recovery:**

- Use the registered name exactly as it appears in the registry.
- If the model is new, add it to the registry and keep the config name aligned with the registration key.
- Do not send the issue to training or data-pipeline code until the registry name is fixed.

## Flax/JAX shape or RNG mistakes

**Symptom:** `init` or `apply` fails with shape, rank, dtype, or RNG errors.

**Check:**

- The dummy input matches the expected input rank and dtype for the model family.
- `train=False` is used for the first init smoke check unless the module explicitly needs training behavior.
- `rngs={'dropout': rng}` is passed only when dropout is active.
- `mutable=['batch_stats']` is requested only for modules that carry mutable state.
- Attention modules receive the right hidden-size-to-head-count ratio.
- Position embedding modules receive the expected tensor rank: 3D for 1D positions and 4D for 2D positions.

**Recovery:**

- Shrink to a minimal dummy batch and re-run `init`/`apply`.
- Fix the dummy input shape before debugging the module internals.
- If only the output head changed, compare the head shapes first instead of rebuilding the entire model.

## Metric aggregation mistakes

**Symptom:** distributed metrics look too small, too large, or unstable across device counts.

**Check:**

- The metric function returns `(sum, normalizer)` pairs, not local averages.
- The normalizer counts real examples, tokens, or pixels after masking.
- The trainer or caller divides by the normalizer only after the cross-device sum.
- The loss itself remains a local scalar average and is not averaged again as if it were a metric.

**Recovery:**

- Replace local averaging with sum/normalizer metrics.
- Use the shared psum-style metric helpers for pmapped code paths.
- If you are working in a JIT/global-array path, use the JIT metric helper that sums global arrays directly.

## Optional matcher dependency failure

**Symptom:** importing or running a matcher fails because an optional dependency is missing.

**Check:**

- `hungarian_matcher` needs `scipy`.
- `sinkhorn_matcher` needs `ott-jax`.
- CPU-callback matchers do not provide gradients and should be validated on CPU first.

**Recovery:**

- Switch to a matcher that matches the available dependencies.
- Install the missing optional package only when that matcher is actually required.
- For a quick smoke check, prefer a lazy or exact tiny-cost case before trying a large detection alignment.

## Checkpoint parameter mismatch

**Symptom:** loading a checkpoint reports missing keys, extra keys, or shape mismatches.

**Check:**

- The registry name still matches the intended class.
- The model width, head count, positional embedding size, or output classes did not change.
- The module names in the new Flax graph still line up with the saved tree.

**Recovery:**

- Compare the freshly initialized parameter tree against the checkpoint tree.
- Reinitialize only the changed layers when the backbone is still compatible.
- If the graph changed broadly, start from a fresh checkpoint instead of forcing a partial load.

## Quick recovery checklist

1. Confirm the registry name.
2. Re-run a tiny `init`/`apply` smoke check.
3. Verify the metric tuple contract.
4. Confirm optional matcher dependencies.
5. Compare the new parameter tree against the checkpoint tree.
