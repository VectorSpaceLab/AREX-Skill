---
name: advanced-domain-features
description: "Use BayesianOptimization advanced domain features: constraints,
  typed parameters, custom parameter classes, TargetSpace conversions, and
  sequential domain reduction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Advanced Domain Features

Use this sub-skill when a task involves constrained optimization, non-float
search variables, custom parameter encodings, low-level `TargetSpace`
conversion/debugging, or sequential domain reduction in the
`bayesian-optimization` package.

## Route here for

- SciPy `NonlinearConstraint` setup with `BayesianOptimization(..., constraint=...)`.
- `ConstraintModel` behavior: `eval`, `fit`, `predict`, `approx`, `allowed`,
  multiple constraints, and registering known constrained observations.
- Integer, categorical, float, or preconstructed `BayesParameter` entries in
  `pbounds`.
- Custom `BayesParameter` subclasses and kernel-space transforms.
- `TargetSpace.params_to_array`, `array_to_params`, masks, bounds, and typed
  conversion semantics.
- `SequentialDomainReductionTransformer` setup, validation, and limitations.

## Route elsewhere

- Basic optimizer lifecycle, `maximize`, ask-tell loops, state save/load,
  `predict`, and ordinary HPO recipes:
  [`../optimizer-workflows/SKILL.md`](../optimizer-workflows/SKILL.md)
- Acquisition selection, exploration/exploitation tuning, custom acquisition
  functions, Constant Liar, or GPHedge:
  [`../acquisition-control/SKILL.md`](../acquisition-control/SKILL.md)
- Editing the repository, running native test selections, docs, lint, CI, or
  release-maintenance checks:
  [`../repo-maintenance/SKILL.md`](../repo-maintenance/SKILL.md)

## Start with the relevant reference

- Read [`references/constraints.md`](references/constraints.md) when the user
  needs expensive/learned constraints, multi-output constraints, feasibility
  debugging, or manual registration of constrained observations.
- Read [`references/parameter-types.md`](references/parameter-types.md) when
  `pbounds` includes integers, categories, preconstructed parameters, or custom
  domain encodings.
- Read [`references/domain-reduction.md`](references/domain-reduction.md) when
  bounds should shrink during optimization or a bounds transformer fails.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) when
  errors mention mismatched constraint arguments, no allowed points, unsupported
  constrained acquisitions, invalid categorical categories, key/dimension
  mismatches, experimental non-float warnings, or domain reduction with typed
  parameters.

## Safe smoke check

Run [`scripts/advanced_features_smoke.py`](scripts/advanced_features_smoke.py)
only after the package and its normal runtime dependencies are importable:

```bash
python scripts/advanced_features_smoke.py --check all
```

The helper is deterministic, uses no network and no plots, and validates tiny
constraint, typed-parameter, and domain-reduction behavior. Use
`python scripts/advanced_features_smoke.py --help` to list narrower checks.

## Working rules for future agents

1. Treat constraints and typed parameters as part of the domain definition, not
   as after-the-fact filters. The optimizer wraps SciPy constraints in a
   `ConstraintModel`, and the internal GP kernels use the `TargetSpace`
   transform for typed domains.
2. Keep objective and constraint keyword names identical. `TargetSpace` calls
   both functions with the same `array_to_params(...)` result.
3. For known observations in a constrained optimizer, always register the raw
   constraint value with `constraint_value`; otherwise the target and
   constraint histories cannot stay aligned.
4. Expect a warning for non-float parameters. Integer/categorical optimization
   is useful, but still marked experimental by the package.
5. Do not combine sequential domain reduction with integer, categorical, or
   custom non-`FloatParameter` domains in the current implementation.
6. If a task asks both for advanced domains and acquisition strategy design,
   handle the domain facts here, then route acquisition-specific choices to
   the acquisition-control sub-skill.
