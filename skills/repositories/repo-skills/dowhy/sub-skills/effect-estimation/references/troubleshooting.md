# Effect-Estimation Troubleshooting

This reference maps common DoWhy `CausalModel` effect-estimation failures to
causes and fixes.

## `ValueError: method_name must be provided`

Where it appears:

- `model.estimate_effect(estimand, method_name=None)`
- `model.do(..., method_name=None)`
- `model.refute_estimate(..., method_name=None)`

Fix:

```python
estimate = model.estimate_effect(estimand, method_name="backdoor.linear_regression")
result = model.refute_estimate(estimand, estimate, method_name="random_common_cause")
do_y = model.do(1, estimand, method_name="backdoor.linear_regression")
```

Use estimator names in `<identifier>.<estimator>` form and refuter names without
an identifier prefix.

## `ImportError: ... is not an existing causal estimator`

Likely causes:

- typo in the estimator part of `method_name`;
- optional package such as EconML or CausalML is not installed;
- external estimator class is not importable;
- custom estimator does not subclass DoWhy's `CausalEstimator`.

Fix:

1. Check spelling against the estimator table.
2. For built-ins, use names such as `backdoor.linear_regression`, not class
   names such as `LinearRegressionEstimator`.
3. For EconML/CausalML, confirm the optional package imports and the fully
   qualified class path is correct.
4. For custom estimators, confirm the class is importable from the current
   Python environment and subclasses `CausalEstimator`.

## `No valid identified estimand for '<identifier>'`

Likely causes:

- estimator prefix does not match a non-null estimand key;
- IV estimator selected but no valid instruments were identified;
- frontdoor estimator selected but no frontdoor variable was identified;
- general adjustment selected but no general adjustment set is available;
- graph has no directed path from treatment to outcome.

Diagnostic:

```python
print(estimand)
print(estimand.estimands.keys())
print("backdoor", estimand.estimands.get("backdoor"))
print("iv", estimand.estimands.get("iv"))
print("frontdoor", estimand.estimands.get("frontdoor"))
print("general", estimand.estimands.get("general_adjustment"))
```

Fix by changing the causal graph/assumptions or selecting an estimator whose
identifier key is available. Do not switch identifiers just to make code run.

## No directed path from treatment to outcome

DoWhy can return an identified estimand marked as no directed path and an effect
of zero. Verify:

- treatment and outcome names are not swapped;
- graph edges are directed correctly;
- the graph includes all nodes on the hypothesized causal path;
- the user truly expects no causal effect.

If the graph format or parsing is the issue, route to `data-graph-interfaces`.

## Treatment or outcome variable not found in DataFrame

DoWhy emits a user warning when treatment or outcome names are not columns.
This usually indicates a typo or a mismatch between graph labels and DataFrame
columns.

Fix:

```python
print(df.columns.tolist())
# Rename data or update treatment/outcome strings so names match exactly.
```

Also inspect capitalization, whitespace, and list-vs-string mistakes.

## Graph variables missing from data

DoWhy warns when graph nodes are not observed in the DataFrame. Missing graph
variables are treated as unobserved. This may be correct for latent confounders,
but it is dangerous if caused by typos.

Fix:

- If variables should be observed, add/rename columns.
- If they are intentionally latent, state the unobserved-confounding assumption
  and consider sensitivity analysis.
- If data columns missing from the graph should be treated as confounders, use
  `missing_nodes_as_confounders=True` deliberately.

## NaNs in treatment or outcome

DoWhy warns when treatment or outcome columns contain NaNs because many
estimators otherwise propagate NaN estimates.

Fix:

- Decide on a causal missing-data strategy before imputation or dropping rows.
- Check whether missingness is affected by treatment/outcome.
- Re-run identification/estimation on the final analysis DataFrame.

## Propensity-score errors

Common messages:

```text
No common causes/confounders present. Propensity score based methods are not applicable
Propensity score methods are applicable only for binary treatments
```

Fix:

- Ensure a valid backdoor/general adjustment set with at least one observed
  confounder.
- Encode the treatment as 0/1 for propensity estimators.
- Use a regression estimator if the treatment is continuous or multivalued.
- Check overlap/support before trusting propensity estimates.

For stratification errors about too few strata or clipping thresholds, reduce
`num_strata`, reduce `clipping_threshold`, or increase sample size.

## Distance matching errors

Common causes:

- no confounders;
- treatment is not a single binary 0/1 variable;
- unsupported `target_units` string;
- exact-match columns remove all usable matches.

Fix by checking treatment encoding, adjustment variables, `exact_match_cols`,
and `target_units` (`"ate"`, `"att"`, or `"atc"`).

## GLM family missing

Error:

```text
Need to specify the family for the generalized linear model
```

Fix:

```python
import statsmodels.api as sm

estimate = model.estimate_effect(
    estimand,
    method_name="backdoor.generalized_linear_model",
    method_params={"glm_family": sm.families.Binomial()},
)
```

Choose a family consistent with the outcome and estimand interpretation.

## IV estimator has no instruments

Common messages:

```text
No valid instruments found. IV Method not applicable
Number of instruments fewer than number of treatments
```

Fix:

- Inspect `estimand.get_instrumental_variables()`.
- Verify graph directions: instrument → treatment and no direct instrument →
  outcome path outside treatment.
- Pass `iv_instrument_name` only for identified instruments.
- For multiple treatments, provide enough instruments or use another design.

## Frontdoor or mediation errors

Common messages:

```text
No front-door variable present. Two stage regression is not applicable
Only singleton frontdoor variables are supported
No mediator variable present. Two stage regression is not applicable
Only singleton mediator variables are supported
```

Fix:

- Inspect `estimand.get_frontdoor_variables()` or
  `estimand.get_mediator_variables()`.
- Use `EstimandType.NONPARAMETRIC_NIE` or `NONPARAMETRIC_NDE` for mediation.
- Use a graph with one clear frontdoor/mediator variable, or narrow the analysis.
- If there are multiple mediators, DoWhy's built-in two-stage estimator may not
  be sufficient.

## `CausalModel.do` raises `NotImplementedError`

Cause: the selected estimator does not implement a do-operator.

Fix:

- Try `backdoor.linear_regression` or another estimator known to support `_do`.
- If the user needs a sampled interventional DataFrame, route to pandas
  `.causal.do` in `data-graph-interfaces`.
- If the user needs interventions in a fitted structural model, route to
  `graphical-causal-models`.

## `fit_estimator=False` gives stale or unexpected results

Likely causes:

- no estimator was previously cached for the exact method-name string;
- target units or effect-modifier schema changed after fitting;
- categorical encodings differ between fit data and new data;
- confusing `estimate_effect` estimator cache with `CausalModel.do`'s separate
  estimator.

Fix:

```python
method = "backdoor.linear_regression"
first = model.estimate_effect(estimand, method_name=method)
assert model.get_estimator(method) is first.estimator
second = model.estimate_effect(estimand, method_name=method, fit_estimator=False)
```

Refit when the feature schema changes.

## Effect modifiers do not produce CATEs

Common causes:

- no `effect_modifiers` were supplied;
- the estimator does not support conditional estimates;
- new effect modifiers were passed only at prediction time after fitting;
- target_units DataFrame does not match expected effect-modifier columns.

Fix:

- Supply effect modifiers at model construction or estimation time.
- For linear regression, inspect `estimate.conditional_estimates`.
- For EconML, inspect `estimate.cate_estimates` and ensure `X` columns exist.
- Refit when changing effect modifiers.

## Optional dependency import failures

Examples:

- EconML method path fails to import.
- CausalML estimator class fails to import.
- TabPFN estimator raises that `tabpfn` or `torch` is missing.

Fix:

1. Confirm the optional package is required for the requested method.
2. Install only the needed optional package/extra in the user's environment.
3. Re-run a small import and smoke estimate.
4. If optional install is not allowed, use a built-in estimator and state the
   reduced scope.

Do not silently replace a requested CATE estimator with an ATE-only estimator.

## Refuter says no estimate is provided

Error:

```text
Aborting refutation! No valid estimate is provided.
```

Fix: return to estimation. Ensure `estimate` is a `CausalEstimate` with a
non-null `.value` and attached `.estimator`.

## Refuter runtime is too slow

Simulation refuters refit estimators many times. Slowdowns are expected with
large datasets, EconML/CausalML/TabPFN estimators, or high `num_simulations`.

Fix:

- Start with `num_simulations=5` or `10` for a smoke run.
- Use `n_jobs=1` for debugging; increase only after memory checks.
- Reduce dataset size or use `data_subset_refuter` with a smaller
  `subset_fraction` for exploratory robustness.
- Disable progress bars in scripts/logs.

## Refuter p-values are unstable

Likely causes:

- too few simulations;
- random seeds omitted;
- estimator itself is stochastic;
- parallelism changes random-state behavior in third-party estimators.

Fix:

- Set `random_state` on DoWhy refuters and underlying estimator/nuisance models.
- Increase `num_simulations` for final analysis.
- Report simulation count and random seeds with refutation results.

## Placebo refuter with IV errors

IV placebo refutation supports `placebo_type="permute"` only.

Fix:

```python
model.refute_estimate(
    estimand,
    estimate,
    method_name="placebo_treatment_refuter",
    placebo_type="permute",
    num_simulations=50,
    random_state=7,
)
```

## `assess_overlap` issues

`assess_overlap` uses backdoor variables and learns support/overlap rules. It is
not a general refuter for IV/frontdoor/mediation estimates.

Fix:

- Use it with a backdoor adjustment estimand.
- Provide `cat_feats` for categorical features.
- Tune `overlap_eps` and support/overlap configs when rules are too strict or
  too loose.

## Graph refutation confusion

Use `model.refute_graph(...)` to test conditional independence implications of
the classic `CausalModel` graph. Do not call `model.refute_estimate(...,
method_name="graph_refuter")`; graph refutation has a separate API.

For `dowhy.gcm` structure/model validation, route to `graphical-causal-models`.

## Boundary checklist

Route away when the user's main issue is:

- graph format parsing, DOT/GML/DAGitty, NetworkX conversion, plotting, pandas
  `.causal.do`, `do_sampler`, datasets, data transformers, or time-series setup:
  use `data-graph-interfaces`;
- `dowhy.gcm`, causal mechanisms, GCM interventions/counterfactuals, anomaly
  attribution, distribution change, arrow strength, or GCM validation: use
  `graphical-causal-models`.
