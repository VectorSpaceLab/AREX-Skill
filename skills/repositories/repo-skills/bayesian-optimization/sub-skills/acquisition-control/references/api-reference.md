# Acquisition API Reference

This reference distills the acquisition APIs and behavior for `bayesian-optimization` v3.3.x. It is designed so future agents can work from the generated skill tree without reopening package source, notebooks, examples, or tests.

## Imports

```python
from bayes_opt import BayesianOptimization, acquisition
from bayes_opt.acquisition import (
    AcquisitionFunction,
    UpperConfidenceBound,
    ExpectedImprovement,
    ProbabilityOfImprovement,
    ConstantLiar,
    GPHedge,
)
from bayes_opt.exception import (
    ConstraintNotSupportedError,
    NoValidPointRegisteredError,
    TargetSpaceEmptyError,
)
```

Prefer `optimizer = BayesianOptimization(..., acquisition_function=<AcquisitionFunction instance>)`. Current APIs do not use the removed `UtilityFunction` helper from older examples.

## Class signatures

| Class or method | Verified signature | Primary use |
|---|---|---|
| `AcquisitionFunction.suggest` | `suggest(gp, target_space, n_random=10000, n_smart=10, fit_gp=True, random_state=None)` | Lower-level next-point optimization over an already non-empty target space. |
| `UpperConfidenceBound` | `UpperConfidenceBound(kappa=2.576, exploration_decay=None, exploration_decay_delay=None, random_state=None)` | Default unconstrained acquisition; explore with posterior mean plus uncertainty. |
| `ExpectedImprovement` | `ExpectedImprovement(xi, exploration_decay=None, exploration_decay_delay=None, random_state=None)` | Improvement-size acquisition; default constrained acquisition when optimizer has constraints. |
| `ProbabilityOfImprovement` | `ProbabilityOfImprovement(xi, exploration_decay=None, exploration_decay_delay=None, random_state=None)` | Probability-only improvement acquisition; often more exploitative than EI. |
| `ConstantLiar` | `ConstantLiar(base_acquisition, strategy='max', random_state=None, atol=1e-5, rtol=1e-8)` | Meta acquisition for asynchronous workers; temporarily registers dummy suggestions in a copied target space. |
| `GPHedge` | `GPHedge(base_acquisitions, random_state=None)` | Meta acquisition portfolio that samples candidates from multiple base acquisitions and chooses with softmax-weighted gains. |

`random_state` still appears in acquisition constructors for compatibility, but package behavior provides the active random state during `suggest()`. Prefer setting `random_state` on `BayesianOptimization` or passing it to lower-level `suggest(...)`.

## Default acquisition selection

`BayesianOptimization(..., acquisition_function=None)` selects:

- `UpperConfidenceBound(kappa=2.576)` when no constraint is provided.
- `ExpectedImprovement(xi=0.01)` when a constraint is provided.

If you need a different constrained acquisition, pass it explicitly. If you pass an acquisition incompatible with constraints, the optimizer can initialize but suggestion can fail when the acquisition sees a constrained target space.

## Built-in base acquisitions

### Upper Confidence Bound (UCB)

Formula: `mean + kappa * std`.

Parameters and validation:

- `kappa >= 0`; negative values raise `ValueError`.
- Higher `kappa` explores uncertain regions more; lower `kappa` exploits high predicted mean.
- `exploration_decay` must be `None` or `0 < exploration_decay <= 1`.
- `exploration_decay_delay` must be `None` or a nonnegative integer.
- Decay is applied automatically after each successful `suggest()` call when the delay condition is met.

Compatibility:

- Does not support constrained optimization. Calling UCB with a constrained target space raises `ConstraintNotSupportedError`.
- `get_acquisition_params()` / `set_acquisition_params()` persist `kappa`, `exploration_decay`, and `exploration_decay_delay`.

### Expected Improvement (EI)

Formula: expected improvement over `y_max + xi`, using both improvement magnitude and probability.

Parameters and validation:

- `xi >= 0`; negative values raise `ValueError`.
- Lower `xi` exploits; higher `xi` encourages exploration by demanding larger improvements.
- `exploration_decay` must be `None` or `0 < exploration_decay <= 1`.
- `exploration_decay_delay` must be `None` or a nonnegative integer.
- Decay is applied to `xi` automatically after each successful `suggest()` call when the delay condition is met.

Compatibility:

- Works unconstrained.
- Works with constraints only after at least one registered point is allowed by the constraint. If observations exist but none are valid, `suggest()` raises `NoValidPointRegisteredError`.
- Calling `base_acq(...)` directly before `y_max` is set raises `ValueError`; normal `suggest()` sets `y_max` from the target space.
- `get_acquisition_params()` / `set_acquisition_params()` persist `xi`, `exploration_decay`, and `exploration_decay_delay`.

### Probability of Improvement (PI)

Formula: probability that the predicted target improves beyond `y_max + xi`.

Parameters, validation, and constrained behavior mirror EI:

- `xi >= 0`.
- `exploration_decay` is `None` or in `(0, 1]`.
- `exploration_decay_delay` is `None` or a nonnegative integer.
- Needs a valid `y_max`; constrained target spaces require at least one allowed registered point.
- `get_acquisition_params()` / `set_acquisition_params()` persist `xi`, `exploration_decay`, and `exploration_decay_delay`.

## Meta acquisitions

### ConstantLiar

Use `ConstantLiar(base_acquisition=<base>, strategy='max')` to spread out asynchronous suggestions before all workers have returned targets.

Important behavior:

- Requires a non-empty target space just like other lower-level acquisitions.
- Does not support constraints; constrained target spaces raise `ConstraintNotSupportedError`.
- Maintains `dummies`, a list of suggested points not yet evaluated.
- Before each suggestion, removes expired dummies that match registered observations within `atol`/`rtol`.
- Copies the target space, registers existing dummies with the lie value, fits the GP on the dummy space, suggests with the base acquisition, then appends the new dummy.
- `strategy` may be a float or one of `'min'`, `'mean'`, `'max'`; other strings raise `ValueError`.
- State persistence stores `dummies`, `base_acquisition_params`, `strategy`, `atol`, and `rtol`.

### GPHedge

Use `GPHedge([acq1, acq2, ...])` when no single acquisition is clearly best.

Important behavior:

- Requires a non-empty target space.
- `base_acq(...)` is intentionally ambiguous and raises `TypeError`; inspect or call individual `base_acquisitions[i].base_acq(...)` if needed.
- On each suggestion, optionally fits the GP, updates gains from the previous candidates, asks each base acquisition for a candidate, samples an acquisition index using softmax of gains, and returns the selected candidate.
- `n_random` and `n_smart` are divided across the base acquisitions. For three base acquisitions, values below `3` can leave each child with zero budget and trigger a lower-level budget error.
- If the selected candidate is a duplicate and a unique candidate exists, GPHedge can select a non-duplicate alternative. If all candidates are duplicates, registration can still fail unless duplicates are allowed or handled by the caller.
- Constraint compatibility depends on the base acquisitions. A portfolio containing UCB is not constraint-compatible; a portfolio using only EI/PI/custom constraint-compatible acquisitions can be used after valid constrained observations exist.
- State persistence stores each base acquisition's params, `gains`, and `previous_candidates`. Recreate the same base-acquisition classes in the same order before `load_state()`.

## Lower-level `suggest(...)` knobs

`AcquisitionFunction.suggest(...)` is useful when you need fine control that `BayesianOptimization.suggest()` does not expose.

- `gp`: the optimizer's Gaussian Process object or another compatible `GaussianProcessRegressor`.
- `target_space`: the optimizer target space; must contain at least one registered observation.
- `n_random`: random samples used to search the acquisition. Set `n_smart=0` for random-only acquisition optimization.
- `n_smart`: number of smart optimizer starts for continuous spaces, or differential-evolution seed budget for mixed/discrete spaces. Set `n_random=0` for smart-only, but `n_smart` must remain positive.
- `fit_gp`: keep `True` unless you have already fitted the GP on the exact same target-space data. Meta acquisitions may set this internally.
- `random_state`: integer or `RandomState`; pass for reproducible lower-level suggestions.

At least one of `n_random` or `n_smart` must be greater than zero. If both are zero, acquisition minimization raises `ValueError`.

## Empty target spaces and `y_max`

- `BayesianOptimization.suggest()` returns a random point if the optimizer has no registered observations.
- Direct `AcquisitionFunction.suggest(...)`, `ConstantLiar.suggest(...)`, and `GPHedge.suggest(...)` raise `TargetSpaceEmptyError` when the target space is empty.
- EI and PI require a best valid target (`y_max`). In constrained use, registered invalid points do not establish `y_max`; register at least one allowed point before asking EI/PI for an acquisition-driven suggestion.

## State persistence contract

`BayesianOptimization.save_state(path)` stores acquisition parameters from `optimizer.acquisition_function.get_acquisition_params()`. `load_state(path)` calls `set_acquisition_params(...)` on the acquisition instance already attached to the new optimizer.

Implications:

- Built-in acquisitions support this contract.
- Custom acquisitions must implement `get_acquisition_params` and `set_acquisition_params` if optimizer state will be saved and loaded.
- The state file does not create the acquisition class for you. Instantiate the new optimizer with the same custom acquisition class and compatible constructor arguments before calling `load_state()`.
- For nested acquisitions, recreate the same nesting shape. Example: load a `ConstantLiar(UpperConfidenceBound(...))` state into another `ConstantLiar(UpperConfidenceBound(...))`, not into plain UCB.
