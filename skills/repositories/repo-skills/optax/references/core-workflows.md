# Core Optimizer Workflows

This reference covers the most common Optax task family: building a gradient transformation pipeline, initializing its state, applying an update, and deciding where learning-rate schedules or wrappers belong.

## What belongs here

- Choosing a base optimizer such as `adam`, `adamw`, `sgd`, `lamb`, `lion`, `rmsprop`, `lbfgs`, `adafactor`, or `adan`.
- Composing transforms with `chain`, `named_chain`, `partition`, `masked`, `freeze`, `lookahead`, `MultiSteps`, `apply_if_finite`, `skip_large_updates`, and `skip_not_finite`.
- Turning raw gradients into parameter updates with `update` and `apply_updates`.
- Injecting schedules into optimizer hyperparameters with `scale_by_schedule`, `inject_hyperparams`, or explicit callable hyperparameters.

## Standard update loop

```python
import jax
import jax.numpy as jnp
import optax

params = {"w": jnp.ones((3,))}
grads = {"w": jnp.array([0.1, -0.2, 0.3])}

# One common pattern: clip first, then apply Adam.
tx = optax.chain(
    optax.clip_by_global_norm(1.0),
    optax.adam(1e-3),
)
state = tx.init(params)
updates, state = tx.update(grads, state, params)
params = optax.apply_updates(params, updates)
```

## Decision points

- Use `optax.chain(...)` when every transform should run sequentially on the same gradient tree.
- Use `optax.named_chain(...)` when you want named intermediate states for debugging or inspection.
- Use `optax.partition(...)` when different parameter subsets need different update rules.
- Use wrappers such as `lookahead`, `masked`, `freeze`, or `MultiSteps` when the update rule itself should change behavior across steps.
- Use `apply_if_finite` or `skip_not_finite` when the optimizer should pause on NaNs/Infs instead of corrupting state.

## Common families and their role

| Family | Typical functions | Why it matters |
| --- | --- | --- |
| Base optimizers | `adam`, `adamw`, `sgd`, `lamb`, `lion`, `rmsprop`, `lbfgs` | Useful starting points when the user just needs a working optimizer |
| Transform primitives | `clip_by_global_norm`, `add_decayed_weights`, `trace`, `scale_by_*` | Build custom optimizers by composing low-level pieces |
| Wrappers | `lookahead`, `masked`, `freeze`, `apply_if_finite`, `MultiSteps` | Add control logic without rewriting the optimizer |
| Composition helpers | `chain`, `named_chain`, `partition` | Combine multiple transforms or parameter groups |
| Update helpers | `apply_updates`, `with_extra_args_support` | Apply updates safely and support extra arguments when needed |

## Common failure modes

- **Tree mismatch**: params and gradients must have matching PyTree structure.
- **Missing params in update**: some transforms need the current parameters as the third `update(...)` argument.
- **Wrong state reuse**: the state from one optimizer pipeline cannot be reused with a different pipeline.
- **Schedule step confusion**: step counters are often `int`-like scalars; make sure the schedule sees the same semantics the optimizer expects.
- **Extra-args mismatch**: if a custom transform expects extra data, wrap it with `with_extra_args_support` or pass the required argument set consistently.

## Good cross-checks

- The root doctor script should be able to initialize the pipeline and apply one update on a tiny tree.
- If the user is unsure whether to use a wrapper or a transform, prefer the simplest pipeline that keeps all state in one place and route to `advanced-topics` only when the workflow truly needs projection, assignment, tree math, or contrib features.
