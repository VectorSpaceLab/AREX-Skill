# Optuna Sampler and Pruner Algorithm Reference

This reference is self-contained for Optuna `5.0.0.dev0` public APIs. Use it to pick algorithms and constructor arguments without opening source docs.

## Sampler Selection Matrix

| Need | Recommended sampler | Notes |
| --- | --- | --- |
| Strong default for single-objective studies | `optuna.samplers.TPESampler(seed=...)` | Default sampler. Good for mixed numerical/categorical spaces, log scales, and moderate budgets. |
| Conditional search spaces | `TPESampler(multivariate=True, group=True, seed=...)` | `group=True` decomposes conditional spaces for multivariate TPE. |
| Batch or distributed suggestions | `TPESampler(constant_liar=True, seed=None or unique seed)` | `constant_liar=True` reduces duplicated concurrent suggestions. Reproducibility is limited with parallel workers. |
| Baseline and high parallelism | `RandomSampler(seed=...)` | Robust for any standard distribution; often a good baseline with a pruner. |
| Fixed finite grid | `GridSampler(search_space, seed=...)` | Exhausts all provided combinations; does not use arbitrary continuous distributions. |
| Exhaustive dynamic finite search | `BruteForceSampler(seed=..., avoid_premature_stop=False)` | Explores finite choices discovered from the objective; suitable for small finite spaces. |
| Continuous, larger budget | `CmaEsSampler(seed=...)` | Requires optional `cmaes`; inefficient or unsupported for categorical/conditional-heavy spaces. |
| Low-dimensional continuous expensive objective | `GPSampler(seed=..., n_startup_trials=10)` | Requires optional `torch`; GP cost grows with completed trials. |
| Quasi-random coverage | `QMCSampler(qmc_type="sobol" or "halton", scramble=False, seed=...)` | Requires optional `scipy`; Sobol works best with trial counts that are powers of two. |
| Multi-objective evolutionary search | `NSGAIISampler(population_size=..., seed=...)` | Supports constraints and crossover customization. |
| Many-objective evolutionary search | `NSGAIIISampler(population_size=..., reference_points=..., seed=...)` | Experimental; designed for many-objective studies. |
| Fix known parameters and sample the rest | `PartialFixedSampler(fixed_params, base_sampler)` | Useful for ablations or staged optimization. |

## Pruner Selection Matrix

Optuna pruners are expected for single-objective optimization. Multi-objective studies should avoid built-in pruners unless the objective is deliberately reduced to a single monitored scalar outside Optuna's multi-objective pruner interface.

| Need | Recommended pruner | Notes |
| --- | --- | --- |
| Conservative baseline | `MedianPruner(n_startup_trials=5, n_warmup_steps=0, interval_steps=1, n_min_trials=1)` | Prunes if a trial is worse than the median of completed trials at the same step. |
| More aggressive percentile cutoff | `PercentilePruner(percentile=25.0, ...)` | For minimization, lower percentile is stricter; constructor validates `0 <= percentile <= 100`. |
| Bandit-style resource allocation | `SuccessiveHalvingPruner(min_resource="auto", reduction_factor=4, min_early_stopping_rate=0, bootstrap_count=0)` | Requires increasing integer steps/resources. |
| Hyperband brackets | `HyperbandPruner(min_resource=1, max_resource="auto", reduction_factor=3, bootstrap_count=0)` | Good default with TPE for iterative objectives; tries multiple SHA brackets. |
| Hard metric bounds | `ThresholdPruner(lower=..., upper=..., n_warmup_steps=0, interval_steps=1)` | Prunes when intermediate values cross explicit thresholds. At least one bound is required. |
| Add tolerance/patience | `PatientPruner(wrapped_pruner, patience=..., min_delta=0.0)` | Wraps another pruner or `None`; validates nonnegative `patience` and `min_delta`. |
| Never prune | `NopPruner()` | Use for debugging sampler behavior or when the objective cannot report meaningful intermediate values. |
| Independent repeated evaluations | `WilcoxonPruner(p_threshold=0.1, n_startup_steps=2)` | Requires optional `scipy`; compares current trial against the best trial by Wilcoxon signed-rank test. |

## Public Constructors to Reach For

```python
optuna.create_study(*, storage=None, sampler=None, pruner=None,
                    study_name=None, direction=None, load_if_exists=False,
                    directions=None)

optuna.samplers.TPESampler(seed=None, multivariate=False, group=False,
                           constant_liar=False, constraints_func=None)
optuna.samplers.RandomSampler(seed=None)
optuna.samplers.GridSampler(search_space, seed=None)
optuna.samplers.CmaEsSampler(x0=None, sigma0=None, n_startup_trials=1,
                             independent_sampler=None, seed=None,
                             consider_pruned_trials=False)
optuna.samplers.QMCSampler(qmc_type="sobol", scramble=False, seed=None)
optuna.samplers.GPSampler(seed=None, n_startup_trials=10,
                          deterministic_objective=False, constraints_func=None)
optuna.samplers.NSGAIISampler(population_size=50, crossover_prob=0.9,
                              swapping_prob=0.5, seed=None,
                              constraints_func=None)
optuna.samplers.NSGAIIISampler(population_size=50, seed=None,
                               reference_points=None, dividing_parameter=3,
                               constraints_func=None)
optuna.samplers.BruteForceSampler(seed=None, avoid_premature_stop=False)

optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=0,
                            interval_steps=1, n_min_trials=1)
optuna.pruners.PercentilePruner(percentile, n_startup_trials=5,
                                n_warmup_steps=0, interval_steps=1,
                                n_min_trials=1)
optuna.pruners.SuccessiveHalvingPruner(min_resource="auto",
                                       reduction_factor=4,
                                       min_early_stopping_rate=0,
                                       bootstrap_count=0)
optuna.pruners.HyperbandPruner(min_resource=1, max_resource="auto",
                               reduction_factor=3, bootstrap_count=0)
optuna.pruners.ThresholdPruner(lower=None, upper=None,
                               n_warmup_steps=0, interval_steps=1)
optuna.pruners.PatientPruner(wrapped_pruner, patience, min_delta=0.0)
optuna.pruners.WilcoxonPruner(p_threshold=0.1, n_startup_steps=2)
```

## Search-Space Compatibility Notes

- `TPESampler` handles float, int, and categorical parameters and is the safest choice for mixed spaces. Use `multivariate=True` for parameter correlations and `group=True` for conditional branches.
- `RandomSampler` is compatible with standard Optuna distributions and is often preferable when heavy parallelism makes model-based suggestions stale.
- `GridSampler` expects a mapping of parameter names to finite sequences, for example `{"optimizer": ["adam", "sgd"], "lr": [1e-3, 1e-2]}`. It samples only listed values.
- `CmaEsSampler` is meant for continuous numerical spaces. It may fall back to its independent sampler for unsupported parameters; categorical/conditional spaces are a poor fit.
- `GPSampler` is best for low-dimensional continuous spaces. Avoid using it as a drop-in for large categorical spaces.
- `QMCSampler` works on transformed search spaces and warns about asynchronous seeding in distributed use. Use the same seed across QMC samplers in distributed runs only when you intentionally coordinate them.
- `NSGAIISampler` and `NSGAIIISampler` are designed for multi-objective optimization and evolutionary populations; set `population_size` high enough for the number of objectives and constraints.
- `BruteForceSampler` is only practical for finite spaces with manageable combinations.

## Pruning Requirements

Pruners do nothing unless the objective reports intermediate values and checks pruning:

```python
for step in range(max_steps):
    value = evaluate_partial_model(step)
    trial.report(value, step)
    if trial.should_prune():
        raise optuna.TrialPruned()
return final_value
```

Use `n_startup_trials` to wait for completed evidence, `n_warmup_steps` to wait within each trial, `interval_steps` to reduce prune checks, and `n_min_trials` to require enough completed peers at a step.

## Constraints Functions

Some samplers accept `constraints_func`, including TPE, GP, NSGA-II, and NSGA-III. The callable receives a `FrozenTrial` and returns a sequence of constraint violations. Values `<= 0` are feasible and values `> 0` are infeasible.

```python
def constraints(trial):
    return [trial.params["width"] * trial.params["depth"] - 100.0]

sampler = optuna.samplers.TPESampler(seed=0, constraints_func=constraints)
```

Only use `constraints_func` after all referenced parameters are always present in completed trials. For conditional objectives, guard missing keys or keep constraints on unconditional parameters.

## Reproducibility

- Pass `seed=` to samplers for deterministic single-process runs.
- Do not promise exact reproducibility with `Study.optimize(..., n_jobs != 1)`; samplers reseed random generators to avoid duplicated parameters.
- In separate distributed processes, use `seed=None` or distinct seeds unless a sampler's documentation specifically calls for coordinated seeds.
- Keep objective-side randomness seeded separately from Optuna sampler randomness.
