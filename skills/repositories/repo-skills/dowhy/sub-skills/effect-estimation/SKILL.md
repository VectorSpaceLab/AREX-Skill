---
name: effect-estimation
description: "Operate DoWhy CausalModel potential-outcomes workflows for
  identification, estimation, do-operations, refutation, and sensitivity
  analysis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Effect Estimation

Use this sub-skill when the user wants DoWhy's classic potential-outcomes
workflow around `CausalModel`: model assumptions, identify an estimand, estimate
ACE/CATE/frontdoor/IV/mediation effects, compute `do`, or refute an effect
estimate.

This file is a router. Read the bundled references for concrete APIs,
parameters, recipes, and failure recovery before writing nontrivial code.

## Route here

Route here for requests mentioning any of these signals:

- `CausalModel`, `identify_effect`, `estimate_effect`, `refute_estimate`, or
  `CausalModel.do`.
- estimate causal effect, average causal effect, ATE, ACE, ATT, ATC, CATE,
  conditional effect, heterogeneous effect, or effect modifiers.
- backdoor adjustment, maximal adjustment, minimal adjustment, efficient
  adjustment, ID algorithm, instrumental variable, frontdoor, mediation,
  natural direct effect, or natural indirect effect.
- method names such as `backdoor.linear_regression`,
  `backdoor.propensity_score_matching`, `iv.instrumental_variable`,
  `frontdoor.two_stage_regression`, or `mediation.two_stage_regression`.
- propensity score matching, stratification, weighting, distance matching,
  linear regression, generalized linear model, doubly robust estimator,
  regression discontinuity, or TabPFN estimator in DoWhy.
- EconML or CausalML estimator calls through DoWhy's `estimate_effect` API.
- robustness checks: random common cause, placebo treatment, data subset,
  bootstrap, dummy outcome, unobserved common cause, E-value, partial R2, or
  sensitivity analysis.
- errors about missing `method_name`, no valid identified estimand, no
  instruments, unidentifiable effects, estimate absent before refutation, NaNs,
  or graph/data variable mismatches in the classic workflow.

## Route away

- `dowhy.gcm` graphical causal models, structural mechanisms, GCM sampling,
  GCM interventions, point counterfactuals, anomaly/root-cause attribution,
  distribution change, and GCM graph/model validation belong in
  [../graphical-causal-models/SKILL.md](../graphical-causal-models/SKILL.md).
- pandas `df.causal.do`, do-samplers, graph string parsing, graph plotting,
  data/schema preparation, built-in datasets, data transformers, graph discovery
  handoff, and time-series helper questions belong in
  [../data-graph-interfaces/SKILL.md](../data-graph-interfaces/SKILL.md).
- Package installation, Python version compatibility, optional dependency
  overview, and import-environment checks belong in the root DoWhy references.

## Read first

- [references/api-reference.md](references/api-reference.md) records verified
  `CausalModel`, identification, estimation, `do`, refutation, and result-object
  signatures and return types.
- [references/workflows.md](references/workflows.md) gives model-identify-
  estimate-refute recipes, graph/common-causes/instrument inputs, conditional
  effects, estimator reuse, `do`, and validation steps.
- [references/estimators-and-refuters.md](references/estimators-and-refuters.md)
  maps estimator/refuter method-name grammar to built-in choices, important
  parameters, sensitivity options, and native behavior anchors.
- [references/econml-cate.md](references/econml-cate.md) explains optional
  EconML, CausalML, and TabPFN boundaries, `method_params` shapes, and dependency
  or access caveats.
- [references/troubleshooting.md](references/troubleshooting.md) lists common
  symptoms, likely causes, recovery steps, and stop conditions for classic
  effect-estimation failures.
- [scripts/smoke_causal_model.py](scripts/smoke_causal_model.py) is a tiny
  no-download ATE smoke script with `--samples`, `--seed`, and `--tolerance`.
- [scripts/parallel_refutation_template.py](scripts/parallel_refutation_template.py)
  is an importable helper and CLI template for small parallel refuter runs on
  synthetic or user-provided CSV data.

## First decision

1. Decide whether the user already has a causal graph, role lists
   (`common_causes`, `instruments`, `effect_modifiers`), or neither.
2. If graph formats, plotting, pandas accessor sampling, or temporal schemas are
   the main problem, route to `data-graph-interfaces` before estimating.
3. Decide the estimand: total ATE, ATT/ATC, conditional effect, IV effect,
   frontdoor effect, natural direct effect, natural indirect effect, or a
   `do(x)` outcome expectation.
4. Identify before estimating. Do not choose an estimator only by convenience;
   the estimator prefix must match an identified strategy.
5. Refute only after a valid `CausalEstimate` exists.

## Core protocol

- Construct `CausalModel(data=df, treatment=..., outcome=..., graph=...)` when
  the user has a DAG; otherwise use explicit `common_causes`, `instruments`, and
  `effect_modifiers` role lists.
- Ensure treatment, outcome, adjustment, instrument, mediator, and effect
  modifier names match DataFrame columns exactly unless a variable is intended
  to be unobserved in the graph.
- Call `identified_estimand = model.identify_effect(...)` and inspect the
  printed estimand or its variable lists before calling `estimate_effect`.
- Always provide `method_name` to `estimate_effect`, `do`, and
  `refute_estimate`; `None` is an error by design.
- Use method names in `<identifier>.<estimator>` form, for example
  `backdoor.linear_regression`, `iv.instrumental_variable`, or
  `frontdoor.two_stage_regression`.
- Use `target_units="ate"`, `"att"`, `"atc"`, a row-filter lambda, or an effect-
  modifier DataFrame only when the selected estimator supports that form.
- Use `fit_estimator=False` only after the same model has cached a fitted
  estimator for the exact same method name and compatible effect modifiers.
- For `CausalModel.do`, choose a regression-style estimator that implements the
  do-operator, such as `backdoor.linear_regression`; many estimators do not.
- Pass method-specific estimator settings in `method_params`; use nested
  `fit_params` only for options that belong to the estimator's `fit` call.
- Set explicit seeds and low simulation counts for smoke refuters; increase
  `num_simulations` only for final analysis.
- Treat refuters as robustness diagnostics, not proof. A refuter failure means
  revisit graph, data quality, estimand, estimator, or domain assumptions.

## Estimator choice shortcuts

- Start with `backdoor.linear_regression` for a small, transparent baseline when
  linear outcome assumptions are acceptable.
- Use propensity score matching, stratification, or weighting for binary
  treatment with observed backdoor variables and adequate overlap.
- Use `backdoor.generalized_linear_model` for GLM outcome models; provide a
  `statsmodels` family in `method_params`.
- Use `iv.instrumental_variable` only when valid instruments are identified and
  there are at least as many instruments as treatment variables.
- Use `iv.regression_discontinuity` when an instrument-like threshold variable,
  threshold value, and bandwidth are part of the design.
- Use `frontdoor.two_stage_regression` for a singleton frontdoor mediator, and
  `mediation.two_stage_regression` for NDE/NIE mediation estimands.
- Use optional EconML, CausalML, or TabPFN estimators only when the relevant
  package, model access, and compute constraints have been verified.

## Refutation shortcuts

- Use `random_common_cause` to test invariance to an independent added covariate.
- Use `placebo_treatment_refuter` to test that a randomized or permuted
  treatment gives an effect near zero.
- Use `data_subset_refuter` to test stability under random subsampling.
- Use `bootstrap_refuter` to test stability under bootstrap resampling and noise.
- Use `dummy_outcome_refuter` when the outcome should be replaced by a known
  synthetic target.
- Use `add_unobserved_common_cause` for sensitivity analysis; choose
  `direct-simulation`, `linear-partial-R2`, `non-parametric-partial-R2`, or
  `e-value` according to estimator assumptions and available domain bounds.
- Refuters that run repeated simulations accept `num_simulations`; several also
  accept `n_jobs` and `verbose` through `model.refute_estimate`.

## Minimal smoke checks

```bash
python scripts/smoke_causal_model.py --samples 1000 --seed 7 --tolerance 0.35
python scripts/parallel_refutation_template.py --num-simulations 3 --n-jobs 1
```

Both scripts are self-contained and perform no downloads. Use them to confirm a
current Python environment can import DoWhy and run the classic workflow before
adapting code to user data.

## Response style

When answering, state the chosen identification strategy, estimator method name,
required columns, important `method_params`, one validation check, and one
refuter or sensitivity check. If routing away, name the sibling skill and the
reason. Do not point future agents to external notebooks, tests, or a source
checkout; distill the needed recipe here.