---
name: samplers-pruners
description: "Choose, configure, customize, and debug Optuna search and pruning
  algorithms, including TPE, random, grid, CMA-ES, QMC, NSGA-II/III, GP, brute
  force, median, percentile, successive halving, Hyperband, threshold, patient,
  and Wilcoxon."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Samplers and Pruners

Use this sub-skill when the task is about selecting or configuring Optuna's `sampler=` or `pruner=`, implementing a custom `BaseSampler` or `BasePruner`, or debugging algorithm-specific behavior.

## Route Boundaries

- Stay here for `optuna.samplers.*`, `optuna.pruners.*`, `optuna.search_space.*`, sampler/pruner constructor arguments, `constraints_func`, pruning reports, grid exhaustion, and optional algorithm dependencies.
- Route objective-loop structure, `Study.optimize`, `Study.ask`, `Study.tell`, callbacks, and trial state lifecycle to `optimization-workflows`.
- Route RDB storage, distributed workers, CLI orchestration, study persistence, and heartbeat behavior to `cli-and-storage`.
- Route plots, parameter importance, dashboard-style analysis, and visualization extras to `analysis-visualization`.
- Route ML framework pruning callbacks, artifact stores, and optional integration packages to `artifacts-integrations`.

## Quick Selection

- Default single-objective tuning: start with `optuna.samplers.TPESampler(seed=...)` and `optuna.pruners.MedianPruner(...)` or `HyperbandPruner(...)` when the objective reports reliable intermediate values.
- Mixed categorical, log-scale, or conditional spaces: prefer `TPESampler(multivariate=True, group=True, seed=...)`; it supports categorical parameters and conditional search spaces better than CMA-ES, QMC, or GP.
- Small exhaustive discrete grids: use `GridSampler(search_space, seed=...)`; use `sampler.is_exhausted(study)` or omit `n_trials` when the study should stop after all grid points are evaluated.
- Purely random baselines or many parallel workers: use `RandomSampler(seed=...)` for robustness, and avoid expecting bit-for-bit reproducibility with `Study.optimize(..., n_jobs != 1)`.
- Continuous low-dimensional expensive objectives: consider `GPSampler(seed=...)` if `torch` is installed; otherwise fall back to TPE or random.
- Continuous high-budget optimization without categorical/conditional parameters: consider `CmaEsSampler(seed=...)` if the `cmaes` package is installed; otherwise fall back to TPE/random.
- Multi-objective optimization: use `NSGAIISampler(...)`, `NSGAIIISampler(...)`, `RandomSampler`, `TPESampler`, `QMCSampler`, or `BruteForceSampler`; do not use pruners for multi-objective studies.
- Independent repeated evaluations with early stopping by statistical comparison: use `WilcoxonPruner(p_threshold=..., n_startup_steps=...)` only when `scipy` is installed.

## Canonical Patterns

```python
import optuna

sampler = optuna.samplers.TPESampler(
    seed=42,
    multivariate=True,
    group=True,
    constant_liar=True,
)
pruner = optuna.pruners.HyperbandPruner(
    min_resource=1,
    max_resource="auto",
    reduction_factor=3,
)
study = optuna.create_study(direction="minimize", sampler=sampler, pruner=pruner)
```

For pruning to have any effect, the objective must report intermediate values and raise `optuna.TrialPruned()` when `trial.should_prune()` returns true:

```python
for step in range(max_steps):
    score = train_one_step(...)
    trial.report(score, step)
    if trial.should_prune():
        raise optuna.TrialPruned()
```

For a deterministic executable check, run the bundled smoke script from the Optuna skill directory:

```bash
python sub-skills/samplers-pruners/scripts/sampler_pruner_smoke.py
```

## Local References

- `references/algorithm-reference.md` maps Optuna sampler/pruner families to supported search-space shapes, objectives, budgets, optional dependencies, and constructor snippets.
- `references/customization.md` shows custom `BaseSampler` and `BasePruner` patterns, `intersection_search_space`, constraints, and safe fallback design.
- `references/troubleshooting.md` covers optional dependency absence, invalid arguments, grid exhaustion, pruning no-ops, reproducibility, and workflow-specific edge cases.

## Hard Usability Cases

- Choose a sampler/pruner for a mixed categorical/log/conditional search space with early stopping, then explain why TPE with `group=True` plus a single-objective pruner is safer than CMA-ES/QMC/GP.
- Debug a study where `GridSampler` stops early after exhausting combinations and a separate `CmaEsSampler` attempt fails because the optional `cmaes` dependency is not installed.
