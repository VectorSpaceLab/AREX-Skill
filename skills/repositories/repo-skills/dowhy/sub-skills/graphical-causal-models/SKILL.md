---
name: graphical-causal-models
description: "Operate DoWhy dowhy.gcm graphical causal model workflows for
  mechanisms, sampling, interventions, counterfactuals, attribution, influence,
  and validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Graphical Causal Models

Use this sub-skill when the user is working with DoWhy's `dowhy.gcm` package.
It is a router and task selector for graphical causal model operations, not a
long API manual. Read the bundled references before writing nontrivial code.

## Route here

Route here for requests mentioning any of these signals:

- `dowhy.gcm`, graphical causal model, GCM, PCM, SCM, or ISCM.
- `ProbabilisticCausalModel`, `StructuralCausalModel`, or
  `InvertibleStructuralCausalModel`.
- causal mechanisms, `assign_causal_mechanisms`, `set_causal_mechanism`, or
  automatic mechanism assignment.
- `gcm.fit`, `gcm.draw_samples`, synthetic samples from a fitted GCM, or model
  evaluation summaries returned during fit.
- GCM interventions, `interventional_samples`, `counterfactual_samples`, or
  `average_causal_effect`.
- direct arrow strength, intrinsic causal influence, parent relevance, feature
  relevance, or Shapley-based causal influence scoring.
- anomaly attribution, anomaly scores, root cause analysis, changed latency
  distributions, distribution-change attribution, robust distribution change,
  or unit-level change attribution.
- `evaluate_causal_model`, `refute_causal_structure`,
  `refute_invertible_model`, GCM independence tests, or GCM confidence
  intervals.

## Route away

- Classic four-step potential-outcomes workflows with `CausalModel`,
  `identify_effect`, `estimate_effect`, `refute_estimate`, propensity scores,
  IV, frontdoor, mediation, or EconML CATE estimators belong in
  [../effect-estimation/SKILL.md](../effect-estimation/SKILL.md).
- pandas `.causal.do`, graph string formats, graph parsing, plotting setup,
  datasets, data transformers, and temporal helpers belong in
  [../data-graph-interfaces/SKILL.md](../data-graph-interfaces/SKILL.md).
- Package installation, optional dependency checks, plotting backends, and
  cross-cutting import failures belong in the root troubleshooting and optional
  integration references.

## Read first

- [references/api-reference.md](references/api-reference.md) for verified GCM
  public signatures, model class selection, mechanism prerequisites, and
  runtime knobs.
- [references/workflows.md](references/workflows.md) for graph-to-mechanism,
  fit, draw, intervention, counterfactual, and GCM ACE workflows.
- [references/root-cause-and-attribution.md](references/root-cause-and-attribution.md)
  for choosing anomaly attribution, distribution change, feature relevance,
  influence scoring, and unit-change APIs.
- [references/model-evaluation-and-validation.md](references/model-evaluation-and-validation.md)
  for model evaluation, graph refutation, invertible-model refutation,
  independence tests, and confidence intervals.
- [references/troubleshooting.md](references/troubleshooting.md) for concrete
  errors and fixes around DAGs, columns, mechanisms, fitting, invertibility,
  categorical data, NaNs, and expensive Shapley/sample settings.
- [scripts/smoke_gcm.py](scripts/smoke_gcm.py) for a small self-contained smoke
  script that builds, assigns, fits, draws, and optionally intervenes on a
  synthetic GCM.

## Task selector

Use this checklist to choose the smallest GCM API family:

1. Need to represent a causal data-generating process?
   Read the model class and mechanism tables in the API reference.
2. Need observational synthetic samples after fitting?
   Use the graph → mechanisms → `gcm.fit` → `gcm.draw_samples` workflow.
3. Need a forward-looking what-if distribution?
   Use `gcm.interventional_samples` with either observed data or a requested
   generated sample size.
4. Need an alternative past for a particular observation?
   Use `gcm.counterfactual_samples`; require an invertible SCM when starting
   from observed data.
5. Need a GCM average causal effect between two interventions?
   Use `gcm.average_causal_effect`; do not switch to classic `CausalModel`
   unless the user asks for the potential-outcomes estimator workflow.
6. Need to rank direct parents of one node?
   Use `gcm.arrow_strength` for direct edge strength or `gcm.parent_relevance`
   for mechanism input relevance.
7. Need upstream influence that is not inherited through parents?
   Use `gcm.intrinsic_causal_influence` on a structural causal model.
8. Need to explain a single anomalous row or a small set of anomalous rows?
   Use `gcm.attribute_anomalies` on an invertible SCM.
9. Need to explain why a target distribution changed between old and new
   datasets?
   Use `gcm.distribution_change` or `gcm.distribution_change_robust`.
10. Need to test whether the graph or mechanisms are contradicted by data?
    Use the evaluation and refutation reference before trusting estimates.

## Operating protocol

- Confirm the graph is a DAG and that every graph node has a matching data
  column before assigning or fitting mechanisms.
- Choose the model class by the required causal rung:
  `ProbabilisticCausalModel` for association/interventions,
  `StructuralCausalModel` for functional mechanisms and influence tasks, and
  `InvertibleStructuralCausalModel` for point counterfactuals or anomaly
  attribution from observed rows.
- Assign a mechanism for every node before `gcm.fit`. Automatic assignment is
  the default for quick starts; manual assignment is preferred when the user has
  domain knowledge or known mechanism types.
- Fit before any sampling, intervention, influence, attribution, or validation
  that requires learned mechanisms.
- Keep generated examples self-contained. Do not require any external source
  tree, unbundled examples, or local environment details.
- For stochastic APIs, set a random seed in examples and state when output is
  approximate.
- For Shapley-based APIs, control runtime explicitly with sample sizes,
  `ShapleyConfig`, and `n_jobs`; defaults can be expensive on large graphs.
- For confidence intervals, decide whether to bootstrap only query randomness
  or refit the causal model on bootstrap training subsets.
- Treat non-rejection from graph or model refutation as absence of detected
  contradiction, not proof that the graph or mechanisms are correct.

## Minimal smoke check

Run the bundled smoke script when you need a quick package-level GCM sanity
check:

```bash
python scripts/smoke_gcm.py --samples 300 --draws 5 --seed 7 --intervene
```

The script is intentionally tiny, performs no downloads, and can be copied into
user projects as a starting point. It prints the fitted graph nodes, a few drawn
samples, and optional interventional/ACE summaries.

## Common decisions to make explicit

- Are graph nodes and data columns named exactly the same?
- Is the target continuous, ordered discrete, binary categorical, or
  multi-class categorical?
- Are missing values present, and if so is the user willing to rely on
  experimental missing-data support for numerical variables only?
- Is the user asking about a changed distribution across two datasets or an
  anomalous individual observation?
- Does the task require point counterfactuals from observed rows, and therefore
  invertible mechanisms?
- What sample-size, Shapley approximation, and parallelism budget is acceptable?
- Should validation prioritize mechanism quality, generated-distribution fit,
  graph refutation, or invertibility assumptions?

## Response style

When answering a GCM task, name the chosen API, list its required inputs, state
whether the model must already be fitted, and include one validation or
troubleshooting check. If routing away, state the target sibling skill and why.
