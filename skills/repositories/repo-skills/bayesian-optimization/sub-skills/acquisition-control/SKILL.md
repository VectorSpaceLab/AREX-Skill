---
name: acquisition-control
description: "Select, tune, debug, and extend BayesianOptimization acquisition
  functions including UCB, EI, PI, Constant Liar, GPHedge, custom acquisitions,
  and constraint compatibility."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Acquisition Control

Use this sub-skill when the task is to choose, configure, debug, serialize, or extend acquisition functions for `bayesian-optimization` v3.3.x.

## Route here for

- Choosing UCB, Expected Improvement, Probability of Improvement, Constant Liar, or GPHedge.
- Tuning exploration/exploitation knobs: `kappa`, `xi`, `exploration_decay`, and `exploration_decay_delay`.
- Using lower-level acquisition `suggest(...)` controls such as `n_random`, `n_smart`, `fit_gp`, and `random_state`.
- Running asynchronous ask-tell loops with `ConstantLiar` dummy suggestions.
- Building portfolio acquisition strategies with `GPHedge`.
- Writing custom `AcquisitionFunction` subclasses and making them compatible with optimizer `save_state` / `load_state`.
- Diagnosing constraint compatibility, empty target-space errors, duplicate suggestions, stale `UtilityFunction` snippets, and custom state-method failures.

## Do not use this sub-skill for

- Basic optimizer lifecycle, `maximize`, `probe`, registration, or state management beyond acquisition-specific state. Use [optimizer workflows](../optimizer-workflows/SKILL.md).
- Detailed constraints, typed parameters, domain reduction, or parameter-bound transformations beyond acquisition compatibility notes. Use [advanced domain features](../advanced-domain-features/SKILL.md).
- Repository maintenance, tests, releases, or contribution workflows. Use [repo maintenance](../repo-maintenance/SKILL.md).

## Read first

1. [API reference](references/api-reference.md) for class signatures, parameter constraints, state parameters, constraint support, and common errors.
2. [Workflows](references/workflows.md) for strategy selection, exploration tuning, Constant Liar ask-tell, GPHedge portfolios, custom acquisitions, and save/load patterns.
3. [Troubleshooting](references/troubleshooting.md) when suggestions fail, constraints are rejected, parameters validate incorrectly, duplicates appear, old `UtilityFunction` code is encountered, or custom acquisitions fail persistence.
4. [Acquisition probe script](scripts/acquisition_probe.py) for a deterministic tiny check that compares built-in acquisition suggestions and optionally exercises Constant Liar and GPHedge.

## Minimal setup snippets

```python
from bayes_opt import BayesianOptimization, acquisition

optimizer = BayesianOptimization(
    f=None,
    pbounds={"x": (-2.0, 4.0)},
    acquisition_function=acquisition.UpperConfidenceBound(kappa=2.576),
    random_state=7,
    verbose=0,
)

# Seed observations before acquisition-driven suggestions.
optimizer.register({"x": -1.0}, target=-4.29)
optimizer.register({"x": 0.0}, target=-0.69)
optimizer.register({"x": 2.5}, target=-0.44)
next_point = optimizer.suggest()
```

If no `acquisition_function` is passed, `BayesianOptimization` chooses UCB for unconstrained problems and Expected Improvement for constrained problems. The optimizer-level `suggest()` method returns a random point while the target space is empty; lower-level acquisition `suggest(...)` requires at least one registered observation.

## Quick validation

After installing `bayesian-optimization` with its normal dependencies, run:

```bash
python scripts/acquisition_probe.py --help
python scripts/acquisition_probe.py --include-constant-liar --include-gphedge
```

The script performs no network access, no plotting, and no writes. It prints concise `PASS` lines after validating that suggested points remain inside bounds.
