# Sequential Domain Reduction

## Purpose

Read this when an optimization should shrink its search bounds as promising
regions are discovered, or when a `bounds_transformer` configuration fails.
The package implements `SequentialDomainReductionTransformer`, based on the
Stander-Craig sequential domain reduction scheme.

## Basic setup

Create the transformer and pass it as `bounds_transformer` when constructing
the optimizer:

```python
from bayes_opt import BayesianOptimization, SequentialDomainReductionTransformer


def objective(x, y):
    return -(x**2) - (y - 1.0) ** 2 + 1.0

bounds_transformer = SequentialDomainReductionTransformer(
    gamma_osc=0.7,
    gamma_pan=1.0,
    eta=0.9,
    minimum_window=0.5,
)

optimizer = BayesianOptimization(
    f=objective,
    pbounds={"x": (-5.0, 5.0), "y": (-5.0, 5.0)},
    bounds_transformer=bounds_transformer,
    random_state=1,
    verbose=0,
)
optimizer.maximize(init_points=2, n_iter=10)
```

During `BayesianOptimization.__init__`, the transformer is initialized with the
optimizer's `TargetSpace`. During `maximize`, bounds are transformed only after
initial random points have been consumed and true optimization iterations have
started. New bounds are applied through `optimizer.set_bounds(...)`.

The transformer stores a history of bound arrays in `bounds_transformer.bounds`.
The first entry is the original global bounds; later entries are reduced bounds.

## Parameters

Signature:

```python
SequentialDomainReductionTransformer(
    parameters=None,
    gamma_osc=0.7,
    gamma_pan=1.0,
    eta=0.9,
    minimum_window=0.0,
)
```

Practical meanings:

- `gamma_osc`: scales oscillation damping. The documentation examples describe
  typical values around `0.5` to `0.7`; default is `0.7`.
- `gamma_pan`: panning scale; default is `1.0`.
- `eta`: zooming/shrinkage factor; default is `0.9`.
- `minimum_window`: lower bound on the width retained for each parameter.
- `parameters`: accepted by the constructor, but current transform output uses
  the target space's keys when creating the new bounds mapping.

## `minimum_window` forms

`minimum_window` may be one of:

- scalar float: same minimum width for every parameter.
- sequence or NumPy array: one width per expanded parameter/bounds row.
- mapping from target-space key to width: reordered internally to match
  `target_space.keys`.

Validation rules:

- Sequence/array length must equal the number of parameter bounds rows.
- Mapping keys should cover the target-space keys; missing keys fail during
  initialization when the mapping is reordered.
- Each minimum window must fit inside the corresponding original global bounds.
  If a global width is smaller than the requested window, initialization raises
  `ValueError: Global bounds are not compatible with the minimum window size.`

Examples:

```python
SequentialDomainReductionTransformer(minimum_window=1.0)
SequentialDomainReductionTransformer(minimum_window=[1.0, 0.5])
SequentialDomainReductionTransformer(minimum_window={"x": 3.0, "y": 1.0})
```

Mapping input is useful when `pbounds` order is not visually obvious, because
it is reordered using `TargetSpace.keys`.

## Current limitation: all parameters must be float parameters

Current code explicitly checks the target space parameter configuration during
`initialize(...)` and raises:

```text
Domain reduction is only supported for all-FloatParameter optimization.
```

This means `SequentialDomainReductionTransformer` cannot be used with:

- integer bounds such as `(1, 10, int)`;
- categorical bounds such as `("rbf", "poly")`;
- preconstructed custom parameters that are not instances of `FloatParameter`.

If the user's problem contains mixed typed parameters, use one of these
alternatives:

1. Optimize without sequential domain reduction and rely on typed kernel
   transforms.
2. Reparameterize the domain so the reduced variables are all ordinary floats
   and convert/cast inside the objective, accepting that the GP no longer uses
   typed kernel semantics for those variables.
3. Run a two-stage search: coarse typed search first, then a float-only refined
   search over a fixed subset of categorical/integer choices.

Do not silently drop a typed parameter from `pbounds` just to make domain
reduction work.

## How bounds are transformed

The transformer tracks:

- the original global bounds;
- previous and current optimum locations from `target_space.max()["params"]`;
- contraction and panning factors derived from movement between optima;
- a current window size `r` for each parameter.

`transform(target_space)`:

1. Calls `_update(target_space)` to move the window center toward the current
   best allowed point.
2. Creates new bounds centered on the current optimum.
3. Sorts and trims proposed bounds to stay inside the original global bounds.
4. Expands any too-small window to satisfy `minimum_window` when possible.
5. Appends the adjusted bounds to `bounds_transformer.bounds` and returns a
   `{parameter_name: bounds_array}` mapping.

For constrained optimizers, `target_space.max()` uses the constrained mask, so
bounds shrink around the best allowed observation. If there is no allowed point,
fix feasibility first; see [`constraints.md`](constraints.md) and
[`troubleshooting.md`](troubleshooting.md).

## Warnings and trimming behavior

The `_trim(...)` logic keeps reduced bounds within original global bounds. It
sorts each lower/upper pair and clips windows that exceed the global bounds.
If a proposed lower bound is greater than the global upper bound, or a proposed
upper bound is less than the global lower bound, the transformer resets the
boundary and emits a domain-reduction warning.

A narrow `minimum_window` is normal for convergence; an impossible
`minimum_window` is a configuration error. If trimming causes surprising wide
windows, inspect both the original `pbounds` and `bounds_transformer.bounds`.

## Validation checklist

Before using sequential domain reduction:

- All `pbounds` entries are ordinary float bounds, not `(low, high, int)`,
  categorical sequences, or custom non-float parameters.
- `minimum_window` has the right length or keys and fits inside the original
  global bounds.
- The objective is reasonably smooth in the float search variables; shrinking
  bounds around noisy or highly multimodal observations can over-focus early.
- If constraints are present, at least one allowed point can be found; otherwise
  the current best point is undefined for acquisition/domain updates.
- The user understands that domain reduction changes the active search bounds,
  not the original objective function or the stored historical observations.

## Inspecting reduced bounds

After a run, inspect:

```python
original = bounds_transformer.bounds[0]
latest = bounds_transformer.bounds[-1]
current_bounds = optimizer.space.bounds
```

`optimizer.space.bounds` is the active bounds array used for later suggestions.
`bounds_transformer.bounds` is the transformer history. To compare against
parameter names, use `optimizer.space.keys` in order.

For ordinary manual bound changes unrelated to sequential domain reduction,
route to the basic optimizer workflow guidance.
