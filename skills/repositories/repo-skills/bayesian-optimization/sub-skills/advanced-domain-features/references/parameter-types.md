# Parameter Types and TargetSpace Conversion

## Purpose

Read this when `pbounds` contains anything beyond ordinary float intervals, or
when debugging how `TargetSpace` converts between user dictionaries and the
float arrays used by Gaussian processes and acquisition optimization.

Non-float parameters are useful for mixed search spaces, but the package emits a
warning that they are experimental and may not work as expected. Treat the
warning as a design reminder: keep the search space small enough to validate,
seed representative points, and inspect `optimizer.res` for canonical values.

## `pbounds` patterns

`TargetSpace.make_params(...)` maps each `pbounds` entry to a parameter object:

| Pattern | Result | Notes |
| --- | --- | --- |
| `"x": (low, high)` | `FloatParameter("x", (float(low), float(high)))` | Standard continuous interval. |
| `"x": (low, high, float)` | `FloatParameter` | Explicit float marker. |
| `"depth": (1, 8, int)` | `IntParameter("depth", (int(low), int(high)))` | Inclusive integer range; random samples use integers from `low` through `high`. |
| `"kernel": ["rbf", "poly"]` or tuple of categories | `CategoricalParameter` | One-hot float representation; categories must be unique and there must be at least two. |
| `"sides": MyParameter(...)` | The supplied `BayesParameter` subclass | Name, bounds, dimensionality, conversion, sampling, and kernel transform are supplied by the custom class. |

Any non-`FloatParameter` causes the experimental non-float warning.

## Float parameters

`FloatParameter` is one-dimensional, continuous, and keeps values unchanged:

- `to_float(value)` returns the numeric value.
- `to_param(value)` returns the single value from the array slice.
- `kernel_transform(value)` returns the original value.
- `dim == 1`.

Use ordinary float bounds for continuous variables and for log-transformed HPO
values such as `log10_C` or `log_learning_rate`.

## Integer parameters

Use `(low, high, int)` for integer-valued search dimensions:

```python
pbounds = {
    "log_learning_rate": (-10.0, 0.0),
    "max_depth": (1, 6, int),
    "min_samples_split": (2, 6, int),
}
```

Important behavior:

- Random samples are integer-valued but stored as floats in `TargetSpace.params`.
- `to_param(...)` rounds the float representation and returns a Python `int`.
- `kernel_transform(...)` rounds values before the GP kernel sees them. This
  makes values such as `2.2` and `2.4` behave like the same integer location in
  kernel space.
- Bounds are inclusive for random sampling.

When a downstream estimator still expects an integer, the objective normally
receives an `int` from the optimizer. If you manually call code outside the
optimizer with raw floats, cast or round explicitly.

## Categorical parameters

Use a sequence of unique categories:

```python
pbounds = {
    "kernel": ["rbf", "poly2", "poly3"],
    "log10_C": (-1.0, 1.0),
}
```

Important behavior:

- Categories must be unique. Duplicate values raise `ValueError: Categories
  must be unique.`
- At least two categories are required. A single category raises `ValueError:
  At least two categories are required.`
- A categorical parameter has one float dimension per category.
- Bounds for those dimensions are `[0, 1]`.
- `to_float(category)` produces a one-hot vector.
- `to_param(vector)` returns the category at `argmax(vector)`.
- `kernel_transform(value)` coerces a row to the nearest one-hot representation
  by setting the `argmax` category to one and all others to zero.

Because categorical dimensions live in `[0, 1]`, scale nearby continuous
features thoughtfully. The package examples note that an isotropic GP may treat
unscaled continuous features very differently from one-hot categorical axes;
for larger mixed spaces, consider setting an anisotropic kernel through the
optimizer workflow's GP-parameter guidance.

## HPO guidance for typed domains

For hyperparameter optimization:

1. Use typed integer bounds for parameters that truly must be integers,
   instead of optimizing floats and casting only inside the objective. Kernel
   rounding lets the GP understand that nearby floats can represent the same
   discrete setting.
2. Encode categorical modeling choices as categories, not arbitrary ordinal
   integers, unless the categories have a meaningful numeric order.
3. Transform positive continuous ranges into log space when appropriate, e.g.
   optimize `log10_C` and compute `C = 10 ** log10_C` inside the objective.
4. Remember the package maximizes. Return negative loss for loss metrics.
5. Keep expensive HPO recipes and baseline optimizer lifecycle details in
   [`../../optimizer-workflows/SKILL.md`](../../optimizer-workflows/SKILL.md); use
   this reference for the domain typing decisions.

## Custom `BayesParameter` subclasses

Subclass `bayes_opt.parameter.BayesParameter` when a domain needs a custom
float representation, nonuniform discrete spacing, a manifold constraint, or a
symmetry-aware kernel transform.

A custom parameter must provide:

| Member | Requirement |
| --- | --- |
| `__init__(name, bounds, ...)` | Call `super().__init__(name, bounds)` with float-space bounds shaped `(dim, 2)` for multi-dimensional parameters or `(2,)` for one-dimensional ones. |
| `is_continuous` | Return whether the acquisition optimizer may treat this parameter as continuous. Non-continuous dimensions avoid pure gradient-based minimization. |
| `random_sample(n_samples, random_state)` | Return float-format samples with shape `(n_samples, dim)` or compatible one-dimensional output. Use `bayes_opt.util.ensure_rng` for reproducibility. |
| `to_float(value)` | Convert canonical user value into the stored float representation. |
| `to_param(value)` | Convert a stored float slice back into the canonical value passed to the objective and shown in results. Do binning/rounding/normalization here when needed. |
| `kernel_transform(value)` | Convert float representations into the representation used by the GP kernel. This is where rounding, one-hot coercion, normalization, or symmetry sorting belongs. |
| `to_string(value, str_len)` | Optional but useful for custom table display; the base method is available for simple values. |
| `dim` | Return the number of float dimensions this parameter occupies. |

### Triangle-style custom parameter pattern

The repository tests and examples use a fixed-perimeter triangle parameter:

- Canonical value: an array of three side lengths.
- Float representation: three dimensions in `TargetSpace`.
- `random_sample`: Dirichlet samples scaled to the perimeter and filtered by
  per-side bounds.
- `to_param` and `kernel_transform`: normalize values so the sides sum to the
  fixed perimeter.
- Symmetry variant: sort the side vector before conversion/transform so
  permutation-equivalent triangles share a kernel representation.

Use this pattern for constrained encodings only when the constraint is a natural
property of one parameter. If the constraint spans multiple named parameters,
use `NonlinearConstraint` instead.

## `TargetSpace` conversions and masks

`TargetSpace` stores all observations as floats in `space.params` and exposes
canonical values through `array_to_params`, `res`, and `max`.

Key properties:

- `space.keys` preserves the insertion order of `pbounds` keys.
- `space.dim` is the sum of `param.dim` across keys. A categorical with three
  categories contributes three dimensions.
- `space.masks[name]` is a boolean mask selecting that parameter's columns in
  the internal float array.
- `space.bounds` is a `(space.dim, 2)` array assembled from every parameter's
  float-space bounds.
- `space.continuous_dimensions` marks each internal dimension according to the
  owning parameter's `is_continuous` property.

Conversion methods:

```python
arr = optimizer.space.params_to_array({"kernel": "rbf", "max_depth": 3})
params = optimizer.space.array_to_params(arr)
```

Validation rules:

- `params_to_array(...)` requires exactly the same keys as `space.keys`, no
  missing keys and no extras. Key order in the input dictionary does not matter.
- `array_to_params(...)` requires `len(x) == space.dim`.
- Raw array registration/probing uses `pbounds` order and the expanded internal
  dimensions. Prefer dictionaries for typed or custom parameters unless you are
  deliberately testing conversion behavior.

## Bounds updates with typed parameters

`TargetSpace.set_bounds(...)` accepts a mapping of existing keys to new bounds
and ignores unknown keys. For updated keys:

- The new parameter type must match the existing type.
- The total expanded dimension must remain unchanged.
- Changing a categorical category set changes dimensionality and raises.
- Changing an integer parameter to float, or a float parameter to integer,
  raises a type mismatch.

Sequential domain reduction calls `set_bounds` automatically, but current code
only supports all-float parameters for that transformer. See
[`domain-reduction.md`](domain-reduction.md) for details.

## Kernel transform implications

The optimizer wraps its GP kernel with `wrap_kernel(...,
transform=space.kernel_transform)`. `TargetSpace.kernel_transform(...)` applies
each parameter's `kernel_transform` to that parameter's slice and horizontally
stacks the results.

Consequences:

- Integer parameters are rounded before the kernel computes distances.
- Categorical parameters are coerced to one-hot before the kernel computes
  distances.
- Custom parameters can encode equivalences or invariants that should be visible
  to the GP.
- If a custom `kernel_transform` changes shape or returns non-finite values, GP
  fitting and acquisition optimization will fail downstream. Keep transforms
  vectorized and shape-preserving.
