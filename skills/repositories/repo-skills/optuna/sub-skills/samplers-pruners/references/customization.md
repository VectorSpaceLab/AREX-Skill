# Custom Samplers and Pruners

Use built-in samplers and pruners first. Create custom implementations only when the search policy or pruning rule needs behavior Optuna does not already expose through constructor arguments.

## Custom Sampler Contract

Subclass `optuna.samplers.BaseSampler` and implement three methods:

- `infer_relative_search_space(study, trial) -> dict[str, BaseDistribution]`
- `sample_relative(study, trial, search_space) -> dict[str, Any]`
- `sample_independent(study, trial, param_name, param_distribution) -> Any`

`infer_relative_search_space` runs near the beginning of a trial. Parameters in its returned search space are sampled together by `sample_relative`. Parameters not in that relative search space are sampled one by one by `sample_independent` when the objective calls a `trial.suggest_*` API.

## Minimal Relative Sampler Pattern

```python
import numpy as np
import optuna


class LocalNeighborhoodSampler(optuna.samplers.BaseSampler):
    def __init__(self, seed: int | None = None) -> None:
        self._rng = np.random.default_rng(seed)
        self._fallback = optuna.samplers.RandomSampler(seed=seed)

    def infer_relative_search_space(self, study, trial):
        return optuna.search_space.intersection_search_space(
            study.get_trials(deepcopy=False)
        )

    def sample_relative(self, study, trial, search_space):
        if not search_space or len(study.trials) < 2:
            return {}
        previous = study.trials[-2]
        params = {}
        for name, distribution in search_space.items():
            if not isinstance(distribution, optuna.distributions.FloatDistribution):
                continue
            center = previous.params[name]
            width = 0.1 * (distribution.high - distribution.low)
            low = max(distribution.low, center - width)
            high = min(distribution.high, center + width)
            params[name] = float(self._rng.uniform(low, high))
        return params

    def sample_independent(self, study, trial, param_name, param_distribution):
        return self._fallback.sample_independent(
            study, trial, param_name, param_distribution
        )
```

Key guardrails:

- Return `{}` from `sample_relative` when no complete trials or no compatible relative search space exist.
- Use `optuna.search_space.intersection_search_space(study.get_trials(deepcopy=False))` for a stable shared space across completed trials.
- Delegate unsupported distributions to `RandomSampler` or another fallback instead of returning invalid values.
- Validate `FloatDistribution`, `IntDistribution`, and `CategoricalDistribution` explicitly when the algorithm only supports some types.
- Consider `study.direction` or `study.directions` if comparing objective values directly; simple minimization-only examples need adaptation for maximization.

## Custom Pruner Contract

Subclass `optuna.pruners.BasePruner` and implement:

```python
prune(study: optuna.study.Study, trial: optuna.trial.FrozenTrial) -> bool
```

The method can inspect:

- `trial.last_step` for the latest reported step, or `None` when nothing was reported.
- `trial.intermediate_values`, a mapping from integer step to reported float.
- `study.get_trials(deepcopy=False, states=(optuna.trial.TrialState.COMPLETE,))` to compare with completed trials.

## Minimal Last-Place Pruner Pattern

```python
import optuna
from optuna.trial import TrialState


class LastPlacePruner(optuna.pruners.BasePruner):
    def __init__(self, warmup_steps: int, warmup_trials: int) -> None:
        self._warmup_steps = warmup_steps
        self._warmup_trials = warmup_trials

    def prune(self, study, trial) -> bool:
        step = trial.last_step
        if step is None or step < self._warmup_steps:
            return False

        current = trial.intermediate_values[step]
        completed = study.get_trials(deepcopy=False, states=(TrialState.COMPLETE,))
        peer_values = [
            other.intermediate_values[step]
            for other in completed
            if step in other.intermediate_values
        ]
        if len(peer_values) <= self._warmup_trials:
            return False

        if study.direction.name == "MAXIMIZE":
            return current < min(peer_values)
        return current > max(peer_values)
```

Key guardrails:

- Return `False` when the objective has not called `trial.report`.
- Wait for enough completed trials and enough steps before pruning.
- Compare in the correct direction: larger is worse for minimization, smaller is worse for maximization.
- Keep the pruner deterministic and side-effect-light; Optuna stores intermediate values, not arbitrary pruner state.

## Constraints and Feasibility

For built-in samplers that accept `constraints_func`, the callable receives a completed `FrozenTrial` and returns one or more constraint values. Feasible means every returned value is `<= 0`.

```python
def constraints(trial):
    params = trial.params
    return [params["units"] * params["layers"] - 512]

sampler = optuna.samplers.TPESampler(seed=3, constraints_func=constraints)
```

Avoid constraints that access conditional parameters without guards:

```python
def safe_constraints(trial):
    if trial.params.get("model") != "mlp":
        return [0.0]
    return [trial.params["units"] * trial.params["layers"] - 512]
```

## Customization Decision Tree

- Need only different startup/randomness/parallel behavior: configure a built-in sampler (`seed`, `n_startup_trials`, `constant_liar`, `independent_sampler`).
- Need finite manual combinations: prefer `GridSampler` or `BruteForceSampler` over a custom sampler.
- Need domain-specific trial rejection: use `constraints_func` where supported before writing a sampler.
- Need a custom early-stop metric: implement `BasePruner` and ensure objectives call `trial.report` and `trial.should_prune`.
- Need ML framework callback pruning: route to integration coverage rather than implementing a generic pruner here.

## Testing Custom Implementations

Use a tiny deterministic objective before applying a custom algorithm to expensive training:

```python
def objective(trial):
    x = trial.suggest_float("x", -2.0, 2.0)
    for step in range(3):
        trial.report(abs(x) + 0.1 * step, step)
        if trial.should_prune():
            raise optuna.TrialPruned()
    return x * x

study = optuna.create_study(
    direction="minimize",
    sampler=LocalNeighborhoodSampler(seed=0),
    pruner=LastPlacePruner(warmup_steps=1, warmup_trials=2),
)
study.optimize(objective, n_trials=8)
```

Check that trial states include a plausible mix of `COMPLETE` and `PRUNED`, all sampled parameters lie inside distributions, and repeated single-process runs with the same seed produce the same result.
