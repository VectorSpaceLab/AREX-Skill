---
name: optimizer-workflows
description: "Use BayesianOptimization for ordinary black-box optimization,
  manual ask-tell loops, persistence, prediction, and small ML hyperparameter
  optimization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Optimizer Workflows

Use this sub-skill when a user wants to run the core `bayes_opt.BayesianOptimization`
lifecycle for a black-box objective or a small machine-learning hyperparameter
optimization job. This route is self-contained: future agents should not need to
open the original repository docs, notebooks, tests, or examples.

## Load This When

- The user has a Python function or external evaluation service and wants to
  optimize scalar parameters with Bayesian optimization.
- The task mentions `BayesianOptimization`, `pbounds`, `maximize`, `max`, `res`,
  `probe`, `register`, `suggest`, `random_sample`, `set_bounds`,
  `set_gp_params`, `save_state`, `load_state`, or `predict`.
- The user asks how to turn a loss into an optimization target, persist an
  optimizer, resume a run, validate results, or handle duplicate/noisy
  observations.
- The user wants a tiny scikit-learn HPO pattern using `bayesian-optimization`.

## Core Rules To Apply First

1. The package maximizes target values. Convert losses to scores, commonly by
   returning `-loss` or using a scikit-learn scorer whose larger value is better.
2. `pbounds` keys must match the objective function keyword arguments exactly.
   Dict inputs are safest. Array/list inputs use the `pbounds` insertion order.
3. Keep objective functions deterministic enough for the GP when possible. For
   noisy objectives, set `allow_duplicate_points=True` only when repeated
   evaluations at the same coordinates are intentional.
4. Use `f=None` only for manual ask-tell loops: call `suggest()`, evaluate
   outside the optimizer, then `register(params, target)`. Do not call eager
   `probe(..., lazy=False)` or `maximize()` with `f=None`.
5. After `maximize()`, call `predict(..., fit_gp=True)` before relying on GP
   predictions; the final registered point may not be included in the fitted GP
   until prediction refits it.
6. Save/load state as JSON with a newly constructed compatible optimizer: same
   objective-compatible kwargs, `pbounds`, acquisition strategy, constraints,
   duplicate policy, and any bounds transformer.

## Bundled References

- [API reference](references/api-reference.md): constructor and method
  signatures, lifecycle semantics, `TargetSpace` result behavior, `predict`
  return shapes, and state persistence details.
- [Workflow recipes](references/workflows.md): basic optimization, manual
  ask-tell evaluations, tiny HPO patterns, loss sign handling, persistence,
  duplicate/noisy recipes, bounds updates, and result validation.
- [Troubleshooting](references/troubleshooting.md): symptoms, causes, and fixes
  for key mismatches, duplicate points, unfitted GP errors, stale state loads,
  target-sign mistakes, bounds/type changes, slow objectives, and `f=None`
  misuse.

## Bundled Smoke Scripts

- [`scripts/bo_core_smoke.py`](scripts/bo_core_smoke.py): deterministic core API
  smoke test. It runs a tiny optimizer, validates `max`/`res`, exercises
  `probe`, `register`, `suggest`, `random_sample`, `set_bounds`, `set_gp_params`,
  `predict`, duplicate handling, and optional JSON save/load.
- [`scripts/sklearn_hpo_smoke.py`](scripts/sklearn_hpo_smoke.py): deterministic
  tiny scikit-learn HPO diagnostic with synthetic data. It demonstrates both
  maximizing a score and negating a loss, with safe integer casting for model
  hyperparameters.

Run scripts only in an environment where `bayesian-optimization` and its normal
Python dependencies are installed. Both scripts support `--help`, use bounded
synthetic data, do not download from the network, and avoid destructive writes.

## Routing Boundaries

Stay in this sub-skill for the optimizer lifecycle, public result validation,
manual ask-tell loops, persistence/resume patterns, `predict` semantics, noisy
or duplicate objectives, bounds updates, GP parameter tuning through
`set_gp_params`, and ordinary small HPO recipes.

Route elsewhere for features that have distinct APIs or deeper contracts:

- Acquisition choices, custom acquisition functions, `ConstantLiar`, `GPHedge`,
  and exploration/exploitation controls: `../acquisition-control/SKILL.md`.
- Constraints, typed/categorical parameters beyond simple wrapper casting,
  custom `BayesParameter`, and sequential domain reduction:
  `../advanced-domain-features/SKILL.md`.
- Repository editing, tests, docs, release, packaging, linting, and maintainer
  workflows: `../repo-maintenance/SKILL.md`.

## Minimal Decision Flow

1. Identify objective type:
   - In-process Python function: create `BayesianOptimization(f=objective, ...)`.
   - External/manual evaluation: create `BayesianOptimization(f=None, ...)` and
     use ask-tell with `suggest()`/`register()`.
2. Define `pbounds` with exact parameter names and realistic finite bounds.
   Prefer log-transformed parameters for scale-sensitive HPO (`log10_C`,
   `log_learning_rate`) and transform inside the objective wrapper.
3. Choose a budget. For smoke tests use tiny values such as `init_points=2`,
   `n_iter=2`; for expensive tasks, increase only after validating objective
   sign, result shape, and runtime.
4. Run `maximize(init_points=..., n_iter=...)` or the ask-tell loop.
5. Validate `optimizer.max` is not `None`, has keys `target` and `params`, all
   returned params are within intended bounds, `len(optimizer.res)` matches the
   number of registered observations, and the best target uses the intended
   metric sign.
6. Persist long or expensive runs with `save_state(path)`. To resume, recreate a
   compatible optimizer and call `load_state(path)` before more suggestions or
   `maximize(init_points=0, n_iter=...)`.
7. If predictions or uncertainty are needed, call `predict()` with explicit
   `fit_gp=True` after at least one observation; use `return_std=True` or
   `return_cov=True`, never both.

## Handoff Checklist For Future Agents

- Objective wrapper returns a finite scalar target and uses the correct sign.
- `pbounds` keys and objective kwargs match exactly.
- Random seeds are set where reproducibility matters.
- `allow_duplicate_points` is justified for noise; otherwise duplicate errors
  are treated as a signal to change the loop.
- State files are JSON and loaded into an optimizer with compatible settings.
- Any advanced acquisition, constraint, typed-parameter, or domain-reduction
  need has been routed to the sibling sub-skill instead of duplicated here.
