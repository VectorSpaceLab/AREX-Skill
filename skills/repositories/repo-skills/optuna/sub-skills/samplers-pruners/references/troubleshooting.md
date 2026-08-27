# Sampler and Pruner Troubleshooting

## Optional Dependency Failures

Some Optuna algorithms are importable even when their optional runtime dependencies are absent, but they fail when used.

| Symptom | Likely cause | Fix or fallback |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'cmaes'` or similar while using `CmaEsSampler` | `cmaes` optional package is not installed | Install `cmaes`, or use `TPESampler`/`RandomSampler` for mixed spaces and smoke tests. |
| `ModuleNotFoundError` involving `scipy.stats.qmc` | `QMCSampler` needs SciPy's QMC implementation | Install `scipy`, or use `RandomSampler`/`TPESampler`. |
| `WilcoxonPruner` fails on import/use with SciPy errors | Wilcoxon signed-rank test needs `scipy` | Install `scipy`, or use `MedianPruner`, `PercentilePruner`, or `HyperbandPruner`. |
| `GPSampler` fails with Torch errors | GP sampler needs `torch` | Install compatible `torch`, or use `TPESampler` for dependency-light operation. |

Do not hide these failures by broadly catching all exceptions in production objectives. Prefer explicit dependency checks around algorithm selection:

```python
try:
    import cmaes  # noqa: F401
except ModuleNotFoundError:
    sampler = optuna.samplers.TPESampler(seed=0)
else:
    sampler = optuna.samplers.CmaEsSampler(seed=0)
```

## Pruner Has No Effect

Common causes:

- The objective never calls `trial.report(intermediate_value, step)`.
- The objective never checks `trial.should_prune()`.
- The objective checks pruning but does not raise `optuna.TrialPruned()` or otherwise stop.
- `n_startup_trials`, `n_warmup_steps`, `interval_steps`, or `n_min_trials` postpone pruning longer than the trial budget.
- The study is multi-objective; built-in pruners are expected for single-objective optimization.

Minimal pruning loop:

```python
for step in range(steps):
    value = evaluate(step)
    trial.report(value, step)
    if trial.should_prune():
        raise optuna.TrialPruned()
```

## Invalid Pruner Arguments

- `PercentilePruner(percentile=...)` requires `0 <= percentile <= 100`.
- `MedianPruner(..., interval_steps=...)` and `PercentilePruner(..., interval_steps=...)` require `interval_steps >= 1`.
- `MedianPruner(..., n_min_trials=...)` and `PercentilePruner(..., n_min_trials=...)` require `n_min_trials >= 1`.
- `SuccessiveHalvingPruner(min_resource=...)` requires `'auto'` or an integer at least `1`.
- `SuccessiveHalvingPruner(reduction_factor=...)` requires at least `2`.
- `SuccessiveHalvingPruner(min_early_stopping_rate=...)` and `bootstrap_count` require nonnegative integers.
- `HyperbandPruner(max_resource=...)` requires `'auto'` or an integer, and `max_resource >= min_resource` when both are integers.
- `ThresholdPruner` requires at least one of `lower` or `upper`, `lower < upper` when both are set, nonnegative `n_warmup_steps`, and `interval_steps >= 1`.
- `PatientPruner(patience=..., min_delta=...)` requires nonnegative values.
- `WilcoxonPruner(p_threshold=...)` requires `0 <= p_threshold <= 1`; `n_startup_steps` must be nonnegative.

## GridSampler Exhaustion

`GridSampler` enumerates the Cartesian product of values in `search_space`. When all grid combinations have been evaluated, optimization can stop automatically if `n_trials` is omitted.

```python
search_space = {"optimizer": ["adam", "sgd"], "lr": [1e-3, 1e-2]}
sampler = optuna.samplers.GridSampler(search_space, seed=0)
study = optuna.create_study(sampler=sampler)
study.optimize(objective)  # stops after 4 combinations
assert sampler.is_exhausted(study)
```

If a user expects more trials, check:

- The grid size: multiply lengths of all sequences.
- Whether failed/pruned trials consumed grid points.
- Whether the objective suggests parameters not present in `search_space`; those are not controlled by the grid.
- Whether multiple workers share the same grid and race near exhaustion.

## Search-Space Mismatch

Symptoms include independent-sampling warnings, poor suggestions, or unsupported-parameter errors.

- `CmaEsSampler` is a poor fit for categorical-heavy or conditional spaces. Use TPE or random.
- `QMCSampler` and `GPSampler` are best for stable numerical spaces; conditional spaces can trigger independent fallback behavior.
- `TPESampler(multivariate=True, group=True)` is the preferred first choice for mixed categorical/log/conditional spaces.
- `NSGAIISampler` and `NSGAIIISampler` require a multi-objective study created with `directions=[...]`, not `direction=...`.
- Pruners are not a replacement for multi-objective ranking; do not expect `trial.should_prune()` to work as a native multi-objective pruning strategy.

## Reproducibility Surprises

- `seed=` controls sampler randomness in single-process runs.
- `Study.optimize(..., n_jobs != 1)` reseeds samplers to avoid duplicate suggestions, so exact reproducibility is not guaranteed.
- Objective code can contain its own randomness; seed NumPy, Python, model libraries, and data splits separately.
- Persistent storage can change results if previous trials remain in the study; create a new study name or delete old studies when testing determinism.

## Misusing Ask/Tell or CLI with Samplers

Sampler and pruner objects are passed to `optuna.create_study(...)`. The CLI and ask/tell flows still depend on study configuration and stored trials, but this sub-skill owns only algorithm selection/configuration. Route detailed `Study.ask`, `Study.tell`, storage, and CLI sequencing problems to `optimization-workflows` or `cli-and-storage`.

Sampler-specific checks still apply:

- Use the same study object/storage so the sampler can observe completed trials.
- Tell trials with correct final values and states; model-based samplers learn from completed/pruned/failed history according to their implementation.
- For pruning with ask/tell, a trial must still receive intermediate values through normal trial APIs inside an objective-like loop; otherwise a pruner has no signal.

## Warning Triage

- Experimental warnings are expected for newer algorithms such as some GP, CMA-ES options, NSGA-III, PatientPruner, PartialFixedSampler, or WilcoxonPruner. Pin Optuna versions and treat experimental APIs as change-prone.
- Independent sampling warnings usually mean the sampler cannot handle a parameter in its relative model. Either simplify the search space, use a better-matched sampler, or set the warning flag only after confirming fallback is acceptable.
- QMC asynchronous seeding warnings indicate potential duplicated or inconsistent low-discrepancy sequences in distributed settings.
