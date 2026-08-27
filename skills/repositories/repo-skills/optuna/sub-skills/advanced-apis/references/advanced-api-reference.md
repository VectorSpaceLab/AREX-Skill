# Optuna Advanced API Reference

This reference covers advanced support APIs that are useful when a task goes beyond the basic optimize/ask-tell lifecycle. It is self-contained and assumes only that the `optuna` package is installed.

## Terminator APIs

The `optuna.terminator` module implements automatic study termination based on estimated room for improvement versus statistical error. In Optuna 5.0.0.dev0 source, this module emits `FutureWarning`: it is deprecated in v4.9.0 and planned for removal in v6.0.0.

Important imports:

```python
from optuna.terminator import BaseTerminator
from optuna.terminator import Terminator
from optuna.terminator import TerminatorCallback
from optuna.terminator import BaseImprovementEvaluator
from optuna.terminator import RegretBoundEvaluator
from optuna.terminator import BestValueStagnationEvaluator
from optuna.terminator import EMMREvaluator
from optuna.terminator import BaseErrorEvaluator
from optuna.terminator import CrossValidationErrorEvaluator
from optuna.terminator import StaticErrorEvaluator
from optuna.terminator import MedianErrorEvaluator
from optuna.terminator import report_cross_validation_scores
```

Verified signatures:

- `Terminator(improvement_evaluator=None, error_evaluator=None, min_n_trials=20)`
- `TerminatorCallback(terminator=None)`
- `report_cross_validation_scores(trial, scores)`
- `StaticErrorEvaluator(constant)`
- `MedianErrorEvaluator(paired_improvement_evaluator, warm_up_trials=10, n_initial_trials=20, threshold_ratio=0.01)`
- `BestValueStagnationEvaluator(max_stagnation_trials=30)`
- `RegretBoundEvaluator(top_trials_ratio=0.5, min_n_trials=20, seed=None)`
- `EMMREvaluator(deterministic_objective=False, delta=0.1, min_n_trials=2, seed=None)`

Behavior to preserve:

- `Terminator(min_n_trials=0)` raises `ValueError` because `min_n_trials` must be positive.
- `Terminator.should_terminate(study)` returns `False` until at least `min_n_trials` complete trials exist.
- Termination condition is strict: `improvement < error`. Equal values do not terminate.
- `TerminatorCallback.__call__(study, trial)` calls `study.stop()` when the terminator says to terminate.
- Default `Terminator()` uses `RegretBoundEvaluator()` and usually `CrossValidationErrorEvaluator()`.
- If the improvement evaluator is `BestValueStagnationEvaluator`, the default error evaluator becomes `StaticErrorEvaluator(constant=0)`.

### Safe callback with a custom terminator

Use a custom `BaseTerminator` when you need deterministic stopping logic or want to avoid optional evaluator internals.

```python
import optuna
from optuna.study import Study
from optuna.terminator import BaseTerminator, TerminatorCallback
from optuna.trial import TrialState


class StopAfterCompleteTrial(BaseTerminator):
    def __init__(self, last_trial_number: int) -> None:
        self.last_trial_number = last_trial_number

    def should_terminate(self, study: Study) -> bool:
        complete = study.get_trials(states=[TrialState.COMPLETE])
        return bool(complete) and max(t.number for t in complete) >= self.last_trial_number


def objective(trial: optuna.Trial) -> float:
    x = trial.suggest_float("x", -1.0, 1.0)
    return x * x


study = optuna.create_study(direction="minimize")
study.optimize(
    objective,
    n_trials=100,
    callbacks=[TerminatorCallback(StopAfterCompleteTrial(last_trial_number=3))],
)
```

### Cross-validation scores

`CrossValidationErrorEvaluator` expects the best complete trial to contain cross-validation scores set by `report_cross_validation_scores(trial, scores)`. Call it inside the objective before returning the aggregate score.

```python
from optuna.terminator import report_cross_validation_scores


def objective(trial):
    scores = [0.71, 0.75, 0.73]
    report_cross_validation_scores(trial, scores)
    return sum(scores) / len(scores)
```

Failure behavior:

- `report_cross_validation_scores(trial, [0.71])` raises `ValueError` because at least two scores are required.
- `CrossValidationErrorEvaluator().evaluate(...)` raises `ValueError` if the selected best trial does not have reported scores.

### Optional dependency notes

The terminator module itself imports with the base Optuna dependencies, but some advanced evaluators rely on heavier internals:

- `RegretBoundEvaluator` uses Optuna Gaussian-process internals and NumPy.
- `EMMREvaluator` lazily imports `scipy.stats` and `torch` through Optuna internals; if those packages are absent, construct a fallback such as `BestValueStagnationEvaluator` plus `StaticErrorEvaluator`.
- When writing portable examples, prefer the custom `BaseTerminator` or `BestValueStagnationEvaluator` smoke pattern unless the task explicitly requires GP/EMMR behavior.

## Search-Space Helpers

Public imports:

```python
from optuna.search_space import IntersectionSearchSpace
from optuna.search_space import intersection_search_space
```

Verified signatures:

- `IntersectionSearchSpace(include_pruned=False)`
- `IntersectionSearchSpace.calculate(study, use_cache=False)`
- `intersection_search_space(trials, include_pruned=False)`

Intersection search space contains parameter distributions that have been suggested in all considered finished trials with exactly matching distributions. The result is sorted by parameter name.

Rules and edge behavior:

- With no complete trials, the intersection is `{}`.
- Failed trials are ignored.
- Pruned trials are ignored unless `include_pruned=True`.
- Waiting and running trials do not add finished distributions.
- If a parameter name appears with different distributions, that parameter is removed from the intersection.
- `IntersectionSearchSpace` caches state and is intended for one study instance; with storage-backed distinct studies, reusing the instance raises `ValueError`.

Example with conditional parameters:

```python
import optuna
from optuna.search_space import IntersectionSearchSpace


def objective(trial: optuna.Trial) -> float:
    model = trial.suggest_categorical("model", ["linear", "tree"])
    if model == "linear":
        alpha = trial.suggest_float("alpha", 1e-4, 1.0, log=True)
        return alpha
    depth = trial.suggest_int("max_depth", 2, 8)
    return float(depth)


study = optuna.create_study(direction="minimize")
study.optimize(objective, n_trials=8)
space = IntersectionSearchSpace().calculate(study)
print(space)  # often only contains parameters shared by all completed branches
```

Private grouping helpers exist as `_GroupDecomposedSearchSpace` and `_SearchSpaceGroup`. They are imported from `optuna.search_space` but are underscore APIs. They are useful for understanding sampler behavior with conditional spaces, but public user code should prefer documented sampler options and `IntersectionSearchSpace`.

## Hypervolume Utilities

Optuna exposes internal hypervolume helpers from `optuna._hypervolume`:

```python
from optuna._hypervolume import compute_hypervolume
from optuna._hypervolume import get_non_dominated_box_bounds
```

Treat these as private APIs because the module path begins with an underscore. Prefer high-level multi-objective study APIs and visualization helpers when possible.

`compute_hypervolume(loss_vals, reference_point, assume_pareto=False)` expects a NumPy array of minimization-oriented loss vectors and a reference point. For maximize objectives, transform signs before calling. Source-backed behavior to preserve:

- Returns `0.0` for an empty point array.
- Raises `ValueError` if any point does not dominate or equal the reference point, i.e. if `loss_vals[i] <= reference_point[i]` is not true for all coordinates.
- Duplicate points do not change the result when `assume_pareto=False`.
- Infinite coordinates can yield infinite hypervolume; NaN in the reference point raises through the dominance check.
- `assume_pareto=True` is a speed hint and should be used only when the candidate points are already Pareto-filtered.

Minimal diagnostic example:

```python
import numpy as np
from optuna._hypervolume import compute_hypervolume

loss_vals = np.array([[1.0, 4.0], [2.0, 2.0], [4.0, 1.0]])
reference_point = np.array([5.0, 5.0])
print(compute_hypervolume(loss_vals, reference_point))
```

## Constraint Notes

Constraint handling is mostly owned by sampler implementations such as TPE and NSGA-II/III, so route algorithm selection and `constraints_func` configuration to `samplers-pruners`. For advanced debugging, know these source-backed rules:

- Constraint values are stored in trial system attributes under the key `"constraints"`.
- Constraint functions should return a sequence of floats, one value per constraint.
- Values `<= 0` are feasible; positive values indicate violations.
- NaN constraint values raise `ValueError` in constraint processing or validation.
- Trials with missing constraint values can be warned about and treated as dominated in constrained dominance comparisons.
- Trials with different numbers of constraints cannot be compared and raise `ValueError`.

## Logging APIs

Public functions:

```python
import optuna.logging

optuna.logging.get_verbosity()
optuna.logging.set_verbosity(optuna.logging.WARNING)
optuna.logging.disable_default_handler()
optuna.logging.enable_default_handler()
optuna.logging.disable_propagation()
optuna.logging.enable_propagation()
```

Available levels include `CRITICAL`/`FATAL`, `ERROR`, `WARNING`/`WARN`, `INFO`, and `DEBUG`. The default Optuna library logger writes to stderr at `INFO` and does not propagate to the Python root logger.

Use this pattern when an application already configures logging:

```python
import logging
import optuna.logging

logging.basicConfig(level=logging.INFO)
optuna.logging.disable_default_handler()
optuna.logging.enable_propagation()
```

Use this pattern to silence Optuna info logs without changing application logging:

```python
import optuna.logging

optuna.logging.set_verbosity(optuna.logging.WARNING)
```

## Exceptions and Warnings

Optuna-specific exceptions live in `optuna.exceptions`, with common aliases at `optuna.TrialPruned` for pruning.

Important classes:

- `OptunaError`: base class for Optuna-specific errors.
- `TrialPruned`: raise from an objective after `trial.should_prune()` returns true.
- `CLIUsageError`: invalid command-line configuration.
- `StorageInternalError`: backend database/storage operation failure.
- `DuplicatedStudyError`: duplicate study name in storage.
- `UpdateFinishedTrialError`: attempted mutation of a finished trial.
- `ExperimentalWarning`: warning category for experimental APIs.

Handling experimental warnings:

```python
import warnings
import optuna
from optuna.exceptions import ExperimentalWarning

with warnings.catch_warnings():
    warnings.simplefilter("ignore", ExperimentalWarning)
    # Call an experimental Optuna API intentionally.
```

Do not catch all `Exception` around Optuna optimization unless the task specifically requires converting failures to failed trials. Use `Study.optimize(..., catch=(SomeException,))` for expected objective exceptions, and keep Optuna configuration errors visible while debugging.
