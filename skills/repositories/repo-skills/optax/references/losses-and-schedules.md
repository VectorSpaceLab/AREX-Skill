# Losses, Schedules, Microbatching, and Perturbations

This reference covers the Optax tasks that are not primarily about choosing the optimizer itself: objective functions, schedule families, microbatch helpers, and perturbation-based wrappers.

## Loss families

Optax groups many losses under `optax.losses`:

- **Classification**: `softmax_cross_entropy`, `softmax_cross_entropy_with_integer_labels`, `sigmoid_binary_cross_entropy`, `sigmoid_focal_loss`, `hinge_loss`, `multiclass_hinge_loss`, `perceptron_loss`, `multiclass_perceptron_loss`.
- **Regression / similarity**: `l2_loss`, `squared_error`, `huber_loss`, `log_cosh`, `cosine_similarity`, `cosine_distance`.
- **Ranking and contrastive**: `ranking_softmax_loss`, `triplet_margin_loss`, `ntxent`.
- **Segmentation / overlap**: `dice_loss`, `binary_dice_loss`, `multiclass_generalized_dice_loss`.
- **Fenchel-Young / sparsemax family**: `make_fenchel_young_loss`, `sparsemax_loss`, `multiclass_sparsemax_loss`.
- **KL / information divergence**: `kl_divergence`, `kl_divergence_with_log_targets`, `generalized_kl_divergence`, `convex_kl_divergence`.

## Schedules

Use `optax.schedules` when a scalar hyperparameter should change over training time:

- **Constant / warmup**: `constant_schedule`, `warmup_constant_schedule`, `warmup_exponential_decay_schedule`, `warmup_cosine_decay_schedule`.
- **Decay curves**: `exponential_decay`, `polynomial_schedule`, `linear_schedule`, `cosine_decay_schedule`.
- **One-cycle / SGDR**: `linear_onecycle_schedule`, `cosine_onecycle_schedule`, `sgdr_schedule`.
- **Piecewise / joins**: `piecewise_constant_schedule`, `piecewise_interpolate_schedule`, `join_schedules`.
- **Metric-driven adaptation**: `optax.contrib.reduce_on_plateau` when the learning rate should react to a monitored value.

A common pattern is to build the schedule first and inject it into the optimizer configuration rather than hard-coding learning rates everywhere.

## Microbatching and perturbations

- `optax.microbatching.microbatch`, `micro_vmap`, and `micro_grad` help when the full batch is too large or when you want gradient accumulation semantics.
- `reshape_batch_axis` and `AccumulationType`/`Accumulator` control how microbatches are partitioned and aggregated.
- `optax.perturbations.make_perturbed_fun` wraps a function with randomized perturbations for robustness-style or smoothed-objective experiments.

## Example snippet

```python
import jax.numpy as jnp
import optax

loss = optax.losses.softmax_cross_entropy(
    logits=jnp.array([[2.0, 1.0]]),
    labels=jnp.array([[1.0, 0.0]]),
)

schedule = optax.schedules.warmup_cosine_decay_schedule(
    init_value=0.0,
    peak_value=1e-3,
    warmup_steps=100,
    decay_steps=1000,
)
```

## Common failure modes

- **Logits vs labels confusion**: many losses expect logits, not probabilities; integer-label variants expect class ids, not one-hot arrays.
- **Axis mismatch**: classification losses often default to the last axis; confirm the class dimension is where you expect it.
- **Schedule step mismatch**: schedules are callables over the step index; make sure the caller supplies the same step convention as the training loop.
- **Microbatch semantics**: `microbatch` is not the same as a plain `vmap`; check the accumulator and output reduction mode.
- **Perturbation noise shape**: the perturbation wrapper must be able to broadcast over the underlying input tree.

## Good cross-checks

- Prefer this reference when a user is deciding between several losses or schedules.
- Use `advanced-topics` if the request is really about constrained optimization, tree math, assignment, or contrib algorithms rather than a loss or schedule.
