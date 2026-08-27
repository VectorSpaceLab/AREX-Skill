---
name: bayesian-optimization
description: "Route BayesianOptimization package tasks for black-box Bayesian
  optimization, HPO, acquisition functions, constraints, typed domains, domain
  reduction, and checkout maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# BayesianOptimization Repo Skill

Use this repo skill when a user asks about the `bayesian-optimization` package,
its `bayes_opt` import, Gaussian-process Bayesian optimization, black-box
function maximization, small hyperparameter optimization, acquisition functions,
constraints, typed/categorical parameters, sequential domain reduction, or
maintaining this package's source checkout.

This skill is self-contained. Do not send future agents to original repository
notebooks or examples for package usage; use the bundled references and scripts
below. Checkout-only test and docs commands are confined to the maintainer
sub-skill.

## Install and import baseline

Package users normally install one of:

```bash
pip install bayesian-optimization
conda install -c conda-forge bayesian-optimization
```

Minimal import check:

```python
from bayes_opt import BayesianOptimization


def objective(x, y):
    return -x**2 - (y - 1.0) ** 2 + 1.0

optimizer = BayesianOptimization(
    f=objective,
    pbounds={"x": (-2.0, 2.0), "y": (-3.0, 3.0)},
    random_state=1,
    verbose=0,
)
optimizer.maximize(init_points=1, n_iter=1)
assert optimizer.max is not None
```

For an environment-level diagnostic, run
[`scripts/check_env.py`](scripts/check_env.py). Add `--run-subskill-smokes` when
you want it to execute the bundled tiny smoke helpers as well.

## Route map

### Core optimizer and HPO workflows

Read [`sub-skills/optimizer-workflows/SKILL.md`](sub-skills/optimizer-workflows/SKILL.md)
when the task involves:

- creating `BayesianOptimization(f=..., pbounds=...)`;
- `maximize`, `max`, `res`, `probe`, `register`, `suggest`, or `random_sample`;
- manual ask-tell loops for external evaluations;
- saving/loading JSON state, changing bounds, tuning GP parameters, or using
  `predict`;
- converting a loss into a maximization target;
- small scikit-learn HPO recipes and validation.

### Acquisition control

Read [`sub-skills/acquisition-control/SKILL.md`](sub-skills/acquisition-control/SKILL.md)
when the task involves:

- UCB, Expected Improvement, Probability of Improvement, Constant Liar, or
  GPHedge;
- choosing exploration/exploitation settings such as `kappa`, `xi`,
  `exploration_decay`, and `exploration_decay_delay`;
- lower-level acquisition `suggest(gp, target_space, n_random, n_smart, ...)`;
- asynchronous/batch-like suggestions, acquisition portfolios, or custom
  `AcquisitionFunction` subclasses;
- acquisition errors such as empty target spaces, invalid `xi`/`kappa`, stale
  `UtilityFunction` snippets, and constraint incompatibility.

### Advanced domain features

Read [`sub-skills/advanced-domain-features/SKILL.md`](sub-skills/advanced-domain-features/SKILL.md)
when the task involves:

- SciPy `NonlinearConstraint` and `ConstraintModel`;
- known constrained observations with `constraint_value`;
- integer bounds `(low, high, int)`, categorical bounds, or custom
  `BayesParameter` subclasses;
- `TargetSpace` array/dict conversion, masks, and typed kernel transforms;
- `SequentialDomainReductionTransformer`, `minimum_window`, and all-float
  domain reduction limitations.

### Repository maintenance

Read [`sub-skills/repo-maintenance/SKILL.md`](sub-skills/repo-maintenance/SKILL.md)
only when the user is editing or validating a `bayesian-optimization` source
checkout. It covers focused pytest selection, Ruff/lint commands, notebook/docs
checks, CI Python/NumPy matrix behavior, dependency markers, build validation,
and release/publish boundaries. Do not use it for ordinary package usage.

## Cross-cutting references

- [`references/troubleshooting.md`](references/troubleshooting.md): install,
  import, dependency marker, no-CLI, old API, and route-selection failures that
  cut across sub-skills.
- [`references/repo-provenance.md`](references/repo-provenance.md): source
  commit, package version, evidence paths, and refresh baseline for this skill.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json):
  structured metadata consumed by DisCo's managed repo-skills router importer.

## Quick decisions

- The package maximizes. If the real metric is a loss, return `-loss`.
- `pbounds` names must match objective and constraint keyword arguments.
- No GPU backend is required for selected package workflows; this is a CPU
  scientific Python package built on NumPy, SciPy, and scikit-learn.
- There is no public package CLI. Use Python APIs and bundled diagnostic
  scripts.
- Avoid old code that calls `optimizer.suggest(UtilityFunction(...))`; current
  v3.3.x optimizer-level `suggest()` takes no acquisition argument. Pass an
  acquisition instance into the optimizer constructor instead.
- Use dict parameters for clarity, especially with typed or categorical
  domains. Raw arrays follow `pbounds` insertion order and expanded internal
  dimensions.

## Handoff checklist

Before answering a user or running a diagnostic, identify:

1. Is this package usage or source-checkout maintenance?
2. Is the objective unconstrained or constrained?
3. Are parameters ordinary floats, typed integers/categories, or custom domain
   objects?
4. Is acquisition selection part of the task, or can the optimizer default be
   used?
5. Does the requested check require only CPU runtime dependencies, or a broader
   development environment for notebooks/docs/lint?

Then load the smallest matching sub-skill and use its bundled references and
scripts.
