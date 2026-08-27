# Constraints

## Purpose

Read this when a `bayesian-optimization` workflow needs feasibility constraints
that are expensive or only known after evaluating a candidate. For cheap,
fully-known constraints, it can still be simpler to encode the forbidden region
inside the objective or to reparameterize the problem before constructing the
optimizer.

## Core API pattern

Use SciPy's `NonlinearConstraint` as the public configuration object:

```python
import numpy as np
from scipy.optimize import NonlinearConstraint
from bayes_opt import BayesianOptimization


def objective(x, y):
    return np.cos(2 * x) * np.cos(y) + np.sin(x)


def constraint_function(x, y):
    return np.cos(x) * np.cos(y) - np.sin(x) * np.sin(y)

constraint = NonlinearConstraint(
    fun=constraint_function,
    lb=-np.inf,
    ub=0.5,
)

optimizer = BayesianOptimization(
    f=objective,
    pbounds={"x": (0.0, 6.0), "y": (0.0, 6.0)},
    constraint=constraint,
    random_state=1,
    verbose=0,
)
optimizer.maximize(init_points=3, n_iter=10)
```

`BayesianOptimization` passes the SciPy object into `TargetSpace`, which wraps
it as `ConstraintModel(constraint.fun, constraint.lb, constraint.ub,
transform=target_space.kernel_transform, random_state=...)`. The transform is
important for typed domains because the constraint GP sees the same rounded or
one-hot kernel representation as the target GP.

## Argument-name matching is required

The target function and constraint function must accept the same keyword names
as the optimizer's `pbounds` keys. Internally, `TargetSpace` converts a numeric
array to a parameter dictionary, then calls:

```python
target = target_func(**dict_params)
constraint_value = constraint_model.eval(**dict_params)
```

A constraint such as `def c(a, b): ...` with `pbounds={"x": ..., "y": ...}`
will fail when the optimizer evaluates it. The raised `TypeError` is rewritten
to explain that the constraint function may not use the same keyword arguments
as the target function.

For mixed typed domains, the constraint receives canonical parameter values:
integers as `int`, categoricals as their category object/string, and custom
parameters as returned by their `to_param(...)` method.

## Lower and upper bounds

- `lb` and `ub` may be scalars for one constraint or arrays for multiple
  constraints.
- Every lower bound must be strictly less than its paired upper bound. If any
  `lb >= ub`, `ConstraintModel` raises `ValueError: Lower bounds must be less
  than upper bounds.` during optimizer construction.
- Use `-np.inf` or `np.inf` for one-sided constraints.
- For a single constraint, scalar bounds and shape-`(1,)` arrays are both
  accepted by SciPy and handled as one internal GP.

## Multiple constraints

For multiple constraints, return a one-dimensional array and provide matching
lower/upper arrays:

```python
def vector_constraint(x, y):
    return np.array([
        -np.cos(x) * np.cos(y) + np.sin(x) * np.sin(y),
        -np.cos(x) * np.cos(-y) + np.sin(x) * np.sin(-y),
    ])

constraint = NonlinearConstraint(
    vector_constraint,
    lb=np.array([-np.inf, -np.inf]),
    ub=np.array([0.6, 0.6]),
)
```

`ConstraintModel` creates one Gaussian-process regressor per constraint output.
`predict(X)` returns the joint probability that all constraints are satisfied.
The implementation assumes conditional independence and multiplies the per-
constraint feasibility probabilities.

## `ConstraintModel` behavior

Important methods and meanings:

| Method | Use |
| --- | --- |
| `eval(**kwargs)` | Calls the original constraint function. Raises `ValueError` if no function was provided and rewrites keyword-name `TypeError`s with a clearer message. |
| `fit(X, Y)` | Fits the internal constraint GP(s) on observed parameter arrays and raw constraint values. Acquisition functions call this when fitting the target GP. |
| `predict(X)` | Returns feasibility probability, not the raw constraint estimate. For multiple constraints it returns the product probability. |
| `approx(X)` | Returns the GP approximation of the raw constraint value(s). Use this for debugging model fit, not as an allowed-mask check. |
| `allowed(constraint_values)` | Applies the actual lower/upper bounds to raw constraint values and returns a boolean mask. |

`TargetSpace.max()` and `optimizer.max` only consider points where
`ConstraintModel.allowed(...)` is true. `optimizer.res` includes `constraint`
and `allowed` entries for constrained optimizers.

## Manual `register` and `probe` behavior

### Eager probing

When a constrained optimizer has a callable `f`, `probe(..., lazy=False)` and
`maximize(...)` evaluate both target and constraint and store both histories:

```python
optimizer.probe({"x": 1.0, "y": 0.5}, lazy=False)
```

The target return and raw constraint value remain aligned in `TargetSpace`.

### Registering known observations

When manually adding an already evaluated constrained observation, include the
constraint value:

```python
params = {"x": 1.0, "y": 0.5}
target = objective(**params)
constraint_value = constraint_function(**params)
optimizer.register(params=params, target=target, constraint_value=constraint_value)
```

If `constraint_value` is omitted in a constrained `TargetSpace`, registration
raises:

```text
When registering a point to a constrained TargetSpace a constraint value needs to be present.
```

For multiple constraints, pass the same array shape returned by the constraint
function.

## Acquisition compatibility notes

The default acquisition changes when constraints are present:

- unconstrained default: `UpperConfidenceBound(kappa=2.576)`
- constrained default: `ExpectedImprovement(xi=0.01)`

The base acquisition wrapper can multiply an acquisition value by the
constraint feasibility probability, but not every acquisition class supports
that path. In current code, `UpperConfidenceBound` and `ConstantLiar` explicitly
raise `ConstraintNotSupportedError` when used with a constrained target space.
Expected Improvement and Probability of Improvement support constraints after
there is at least one allowed observation.

For deeper acquisition choice or custom acquisition implementation, route to
[`../../acquisition-control/SKILL.md`](../../acquisition-control/SKILL.md).

## No valid allowed point

Expected Improvement and Probability of Improvement need the best target value
among allowed observations. If all registered constrained points violate the
constraint, `suggest()` raises `NoValidPointRegisteredError` with guidance to
sample until at least one point satisfies the constraints.

Recovery pattern:

1. Check `optimizer.res` for `allowed: True` entries.
2. If none exist, add known feasible seed points with `register(...,
   constraint_value=...)` or run additional random/eager probes until feasible.
3. Verify the constraint function is not inverted and the lower/upper bounds are
   not too narrow.
4. Then resume `maximize(init_points=0, n_iter=...)` or call `suggest()`.

## Validation checklist

Before a constrained run:

- `pbounds` keys exactly match objective and constraint keyword names.
- `NonlinearConstraint.lb < NonlinearConstraint.ub` elementwise.
- Constraint return shape matches the shape of `lb` and `ub`.
- At least one feasible seed is likely, or the run has enough random points to
  discover feasibility.
- Known observations include `constraint_value`.
- The selected acquisition supports constraints, or acquisition selection is
  delegated to the default constrained EI.
