# Acquisition Troubleshooting

Use this when acquisition configuration or suggestion behavior fails. The remedies below assume current `bayesian-optimization` v3.3.x APIs.

## Invalid acquisition parameters

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ValueError: kappa must be greater than or equal to 0.` | `UpperConfidenceBound(kappa=<negative>)`. | Use `kappa >= 0`. Try `0.1` for exploitation, `2.576` default, or higher values for exploration. |
| `ValueError: xi must be greater than or equal to 0.` | `ExpectedImprovement` or `ProbabilityOfImprovement` received negative `xi`. | Use `xi >= 0`; increase `xi` only when more exploration is desired. |
| `ValueError: exploration_decay must be greater than 0 and less than or equal to 1.` | Decay is `0`, negative, greater than `1`, or infinite. | Use `None` for no decay, `1.0` for no effective change, or a value such as `0.9` / `0.95` for gradual decay. |
| `ValueError: exploration_decay_delay must be an integer greater than or equal to 0.` | Delay is negative, fractional, or a string. | Use `None` or an integer such as `0`, `2`, or `5`. |
| `ValueError: Received invalid argument ... for strategy.` | `ConstantLiar(strategy=...)` is not `'min'`, `'mean'`, `'max'`, or a float. | Choose a valid string strategy or pass a numeric lie value. |

## Empty target space

Symptom:

```text
TargetSpaceEmptyError: Cannot suggest a point without previous samples
```

Likely causes:

- Calling `AcquisitionFunction.suggest(...)`, `ConstantLiar.suggest(...)`, or `GPHedge.suggest(...)` directly before registering observations.
- Using lower-level acquisition APIs instead of `BayesianOptimization.suggest()`.

Recovery:

1. For normal workflows, call `optimizer.suggest()` first; it returns random initial samples while the optimizer is empty.
2. For lower-level acquisition calls, register at least one observation first:

```python
optimizer.register({"x": 0.0}, target=-0.69)
raw = optimizer.acquisition_function.suggest(
    gp=optimizer._gp,
    target_space=optimizer.space,
    n_random=256,
    n_smart=3,
    fit_gp=True,
    random_state=7,
)
```

For basic lifecycle details, route from this sub-skill's router to [optimizer workflows](../../optimizer-workflows/SKILL.md).

## Constrained EI/PI has no valid point

Symptom:

```text
NoValidPointRegisteredError: Cannot suggest a point without an allowed point
```

Likely cause: the constrained target space contains observations, but none satisfy the constraint bounds, so EI/PI cannot determine a valid `y_max`.

Recovery:

1. Randomly sample or manually register points until at least one observation satisfies the constraint.
2. When registering historical data, include `constraint_value` and ensure it is inside the allowed interval.
3. Keep using EI/PI or a constraint-compatible custom acquisition. Do not switch to UCB just to bypass this error; UCB rejects constraints.

For detailed constraint modeling and allowed-point registration, route from this sub-skill's router to [advanced domain features](../../advanced-domain-features/SKILL.md).

## Constraint unsupported errors

Symptom:

```text
ConstraintNotSupportedError: Received constraints, but acquisition function ... does not support constrained optimization.
```

Likely causes:

- UCB was used with a constrained optimizer.
- Constant Liar was used with a constrained optimizer.
- GPHedge contains a constraint-incompatible base acquisition such as UCB.
- A custom acquisition overrides `_get_acq(...)` and rejects constraints.

Recovery:

- For constrained optimization, use `ExpectedImprovement(xi=0.01)` or `ProbabilityOfImprovement(xi=0.01)` after valid constrained observations exist.
- For constrained GPHedge, build the portfolio only from constraint-compatible acquisitions.
- For custom acquisitions, either let the inherited `_get_acq(...)` multiply by constraint probability or explicitly document and raise `ConstraintNotSupportedError`.
- Do not use Constant Liar for constrained optimization in v3.3.x.

## `UtilityFunction` import or stale async examples

Symptoms:

```text
ImportError: cannot import name 'UtilityFunction' from 'bayes_opt.util'
TypeError: BayesianOptimization.suggest() takes 1 positional argument but ... were given
```

Likely cause: old code copied from pre-v3 examples where `UtilityFunction(kind='ucb', ...)` was passed into `optimizer.suggest(...)`.

Recovery:

```python
from bayes_opt import BayesianOptimization, acquisition

optimizer = BayesianOptimization(
    f=None,
    pbounds={"x": (-4.0, 4.0), "y": (-3.0, 3.0)},
    acquisition_function=acquisition.UpperConfidenceBound(kappa=3.0),
    random_state=7,
)
next_point = optimizer.suggest()
```

For async dummy suggestions, wrap the acquisition:

```python
acq = acquisition.ConstantLiar(acquisition.UpperConfidenceBound(kappa=3.0), strategy="max")
optimizer = BayesianOptimization(f=None, pbounds={"x": (-4.0, 4.0)}, acquisition_function=acq)
```

The generated workflow adapts the current dummy-suggestion example and excludes the old server example as runnable guidance because it starts local services and uses removed APIs.

## Duplicate suggestions and registration failures

Symptoms:

```text
NotUniqueError: Data point ... is not unique
```

or repeated suggestions that collide with previously registered points.

Likely causes:

- The acquisition maximum is at an already observed point.
- Search budgets are too small, especially with GPHedge splitting budgets across base acquisitions.
- Noise makes repeated probing desirable but `allow_duplicate_points=False`.
- Constant Liar dummies were not removed because returned params differ slightly beyond `atol`/`rtol`.

Recovery:

- Increase `n_random` and `n_smart` for lower-level suggestions.
- For noisy objectives where repeats are acceptable, construct the optimizer with `allow_duplicate_points=True`.
- For Constant Liar, register exact parameter dictionaries returned by `optimizer.suggest()` when worker results arrive, or tune `atol`/`rtol` if external systems round parameters.
- For GPHedge, ensure at least one base acquisition can generate non-duplicate candidates; if all portfolio candidates are duplicates, handle registration failure or allow duplicates.

## Lower-level random/smart budget failures

Symptoms:

```text
ValueError: Either n_random or n_smart needs to be greater than 0.
RuntimeError: Differential evolution optimization failed. Message: ...
```

Likely causes:

- Both `n_random` and `n_smart` were set to zero.
- GPHedge divided small budgets across base acquisitions, leaving each child with zero budget.
- Mixed/discrete parameter optimization used differential evolution and the solver failed.

Recovery:

- Keep at least one budget positive.
- For GPHedge with `m` base acquisitions, use `n_random >= m` or `n_smart >= m`; usually use much larger values such as `n_random=3000`, `n_smart=9` for three bases.
- For quick deterministic smoke tests, use random-only: `n_random=256`, `n_smart=0`.
- For production-quality suggestions, increase budgets and keep `fit_gp=True`.

## EI/PI `y_max` errors outside `suggest()`

Symptom:

```text
ValueError: y_max is not set
```

Likely cause: calling `ExpectedImprovement.base_acq(...)` or `ProbabilityOfImprovement.base_acq(...)` directly before `suggest()` has set `y_max`.

Recovery:

- Prefer normal `suggest()` calls.
- If directly plotting or inspecting `base_acq`, set `acq.y_max` from the valid target maximum first.
- In constrained contexts, ensure the maximum is from allowed observations only.

## GPHedge base acquisition ambiguity

Symptom:

```text
TypeError: GPHedge base acquisition function is ambiguous.
```

Likely cause: code called `portfolio.base_acq(mean, std)`.

Recovery:

```python
portfolio.base_acquisitions[0].base_acq(mean, std)
```

Use individual base acquisitions for diagnostics. Use `portfolio.suggest(...)` for actual portfolio suggestions.

## Custom acquisition state method errors

Symptoms:

```text
NotImplementedError: Custom AcquisitionFunction subclasses must implement their own get_acquisition_params method.
NotImplementedError: Custom AcquisitionFunction subclasses must implement their own set_acquisition_params method.
```

Likely cause: optimizer `save_state()` or `load_state()` touched a custom acquisition that did not implement state methods.

Recovery:

```python
class MyAcq(acquisition.AcquisitionFunction):
    def __init__(self, weight=1.0):
        super().__init__()
        self.weight = float(weight)

    def base_acq(self, mean, std):
        return mean + self.weight * std

    def get_acquisition_params(self):
        return {"weight": self.weight}

    def set_acquisition_params(self, params):
        self.weight = float(params["weight"])
```

Also instantiate the same custom class before `load_state()`; optimizer state does not serialize the class definition.

## Validate the local acquisition setup

Run the bundled helper when you need a quick acquisition sanity check:

```bash
python scripts/acquisition_probe.py --include-constant-liar --include-gphedge
```

Expected result: concise `PASS` lines for UCB, EI, PI, and selected meta acquisitions, with every suggestion inside bounds.
