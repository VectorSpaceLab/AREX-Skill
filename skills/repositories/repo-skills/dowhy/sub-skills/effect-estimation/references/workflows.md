# Effect Estimation Workflows

This reference gives self-contained recipes for DoWhy's classic
`CausalModel` workflow. It assumes DoWhy is importable in the current Python
environment and the user already has or can create a pandas DataFrame.

## Four-step workflow

```python
from dowhy import CausalModel

model = CausalModel(
    data=df,
    treatment="T",
    outcome="Y",
    graph=graph,  # or common_causes=[...], instruments=[...]
    effect_modifiers=["X"],  # optional
)
identified_estimand = model.identify_effect(proceed_when_unidentifiable=False)
estimate = model.estimate_effect(
    identified_estimand,
    method_name="backdoor.linear_regression",
    control_value=0,
    treatment_value=1,
    target_units="ate",
)
refutation = model.refute_estimate(
    identified_estimand,
    estimate,
    method_name="random_common_cause",
    num_simulations=20,
    random_state=7,
)
```

Checklist before finalizing an answer:

1. Are treatment and outcome columns present in `df`?
2. Does every observed graph node or role-list variable match a DataFrame
   column exactly?
3. Does the selected estimator prefix match a non-null identified estimand?
4. Is the target population (`ate`, `att`, `atc`, subset lambda, or effect-
   modifier DataFrame) supported by that estimator?
5. Does at least one refuter or sensitivity diagnostic address the main
   assumption risk?

## Model causal assumptions

### Use an explicit graph when possible

A graph is the best representation when the user has a causal DAG. It lets DoWhy
identify backdoor, IV, frontdoor, generalized adjustment, and mediation
candidates from a common assumption set.

```python
model = CausalModel(
    data=df,
    treatment="T",
    outcome="Y",
    graph="graph[directed 1 node[id \"W\" label \"W\"] node[id \"T\" label \"T\"] node[id \"Y\" label \"Y\"] edge[source \"W\" target \"T\"] edge[source \"W\" target \"Y\"] edge[source \"T\" target \"Y\"]]",
)
```

For DOT/GML/DAGitty parsing, plotting, NetworkX conversion, or graph/data
alignment problems, route to `data-graph-interfaces` and return here after the
schema is valid.

### Use role lists when graph is not available

When the user knows roles but not a full graph, supply lists directly.

```python
model = CausalModel(
    data=df,
    treatment="T",
    outcome="Y",
    common_causes=["W1", "W2"],
    instruments=["Z"],          # optional
    effect_modifiers=["X"],     # optional
)
```

`common_causes`, `instruments`, and `effect_modifiers` are only used to build a
simple graph when `graph is None`. If both graph and role lists are provided,
DoWhy primarily uses the graph; use `identify_vars=True` only when you want
common causes, instruments, and effect modifiers derived from the graph.

### Partial graph and missing nodes

Use `missing_nodes_as_confounders=True` when the user's graph is intentionally
partial and remaining DataFrame columns should be treated as confounders.
Warn that this is an assumption-expansion step, not evidence that the variables
are true confounders.

```python
model = CausalModel(
    data=df,
    treatment="T",
    outcome="Y",
    graph=partial_graph,
    missing_nodes_as_confounders=True,
)
```

Validation: compare graph nodes with DataFrame columns before estimation. If a
node is missing from data unintentionally, fix the typo or add the column rather
than proceeding.

## Identify effects

### Default auto-identification

```python
identified_estimand = model.identify_effect(
    method_name="default",
    proceed_when_unidentifiable=False,
)
print(identified_estimand)
```

The default auto identifier checks several strategies and stores all found
candidates in one `IdentifiedEstimand`: backdoor/generalized adjustment, IV,
frontdoor, and mediation-related pieces where relevant.

### Backdoor selection options

Use these when multiple adjustment sets exist or the default is too slow/noisy.

```python
identified_estimand = model.identify_effect(method_name="maximal-adjustment")
identified_estimand = model.identify_effect(method_name="minimal-adjustment")
identified_estimand = model.identify_effect(method_name="exhaustive-search")
```

- `maximal-adjustment`: fast; may include unnecessary variables.
- `minimal-adjustment`: smaller set; can take longer.
- `exhaustive-search`: useful for auditing options; can be expensive.
- `efficient-adjustment`, `efficient-minimal-adjustment`, and
  `efficient-mincost-adjustment`: use graph-based efficient backdoor algorithms;
  stop if graph conditions are not met or costs/observability assumptions are
  unclear.

### Generalized adjustment

DoWhy's auto identifier may populate `general_adjustment` on Python versions
where the required NetworkX separator functionality is available. Estimators
such as linear regression, generalized linear model, propensity score methods,
distance matching, and doubly robust can work with identifier method
`general_adjustment` when their estimator-specific assumptions also hold.

### ID algorithm

```python
id_expression = model.identify_effect(method_name="id-algorithm")
print(id_expression)
```

The ID algorithm returns an `IDExpression`, not a normal `IdentifiedEstimand`.
Use it to inspect identifiability or derive a formula. Do not pass it directly
to `model.estimate_effect`; DoWhy's built-in estimators expect an
`IdentifiedEstimand` with strategy keys such as `backdoor`, `iv`, or
`frontdoor`.

### Mediation and direct effects

Use `EstimandType` for natural indirect/direct effects.

```python
from dowhy import EstimandType

nie_estimand = model.identify_effect(
    estimand_type=EstimandType.NONPARAMETRIC_NIE,
    proceed_when_unidentifiable=True,
)
nie = model.estimate_effect(
    nie_estimand,
    method_name="mediation.two_stage_regression",
)

nde_estimand = model.identify_effect(
    estimand_type=EstimandType.NONPARAMETRIC_NDE,
    proceed_when_unidentifiable=True,
)
nde = model.estimate_effect(
    nde_estimand,
    method_name="mediation.two_stage_regression",
)
```

Two-stage mediation currently assumes singleton mediator patterns for the common
built-in path; stop and redesign or choose another tool if the requested
mediator structure is outside that support.

## Estimate effects

### Backdoor linear regression baseline

```python
estimate = model.estimate_effect(
    identified_estimand,
    method_name="backdoor.linear_regression",
    control_value=0,
    treatment_value=1,
    target_units="ate",
    test_significance=True,
    confidence_intervals=True,
    method_params={"num_simulations": 100, "num_null_simulations": 100},
)
print(estimate.value)
```

Use this as a transparent first pass when linear outcome assumptions are
reasonable. It supports effect modifiers and can compute conditional estimates.

### Propensity score workflows

Propensity score estimators require binary treatment and observed adjustment
variables. They are inappropriate when there are no common causes or treatment
is not binary.

```python
match = model.estimate_effect(
    identified_estimand,
    method_name="backdoor.propensity_score_matching",
    target_units="att",
)

strat = model.estimate_effect(
    identified_estimand,
    method_name="backdoor.propensity_score_stratification",
    target_units="ate",
    method_params={"num_strata": "auto", "clipping_threshold": 10},
)

weight = model.estimate_effect(
    identified_estimand,
    method_name="backdoor.propensity_score_weighting",
    target_units="ate",
    method_params={"weighting_scheme": "ips_weight"},
)
```

Validate overlap before trusting propensity methods. Extreme or clipped
propensity scores indicate design problems or the need for stronger positivity
checks.

### Distance matching

Use distance matching for binary treatment and observed common causes. It can
accept distance metric options and `fit_params` for exact matching columns.

```python
estimate = model.estimate_effect(
    identified_estimand,
    method_name="backdoor.distance_matching",
    target_units="att",
    method_params={
        "distance_metric": "minkowski",
        "p": 2,
        "fit_params": {"exact_match_cols": ["W_cat"]},
    },
)
```

Stop if treatment is not binary, there are no adjustment variables, or exact
matching leaves too few matched units.

### Generalized linear model

Use GLM when the outcome model should use a non-Gaussian likelihood. Supply a
`statsmodels` family.

```python
import statsmodels.api as sm

estimate = model.estimate_effect(
    identified_estimand,
    method_name="backdoor.generalized_linear_model",
    method_params={"glm_family": sm.families.Binomial(), "predict_score": True},
)
```

If `glm_family` is missing, DoWhy raises a clear `ValueError`. For binary
outcomes, decide whether `predict_score=True` should return predicted
probabilities instead of hard labels.

### Instrumental variables and regression discontinuity

```python
iv = model.estimate_effect(
    identified_estimand,
    method_name="iv.instrumental_variable",
    method_params={"iv_instrument_name": "Z"},
)

rd = model.estimate_effect(
    identified_estimand,
    method_name="iv.regression_discontinuity",
    method_params={
        "rd_variable_name": "Z",
        "rd_threshold_value": 0.5,
        "rd_bandwidth": 0.15,
    },
)
```

IV requires at least one valid instrument and at least as many instruments as
treatment variables for 2SLS-style paths. Regression discontinuity is wrapped as
an IV problem around a local threshold window; verify the threshold and
bandwidth are domain-meaningful.

### Frontdoor and mediation

```python
frontdoor = model.estimate_effect(
    identified_estimand,
    method_name="frontdoor.two_stage_regression",
)
```

Two-stage regression uses linear first- and second-stage models by default. You
can pass `first_stage_model` or `second_stage_model` through `method_params`,
but ensure they are compatible `CausalEstimator` classes or instances.

### Doubly robust

```python
estimate = model.estimate_effect(
    identified_estimand,
    method_name="backdoor.doubly_robust",
    target_units="ate",
    method_params={"min_ps_score": 0.01, "max_ps_score": 0.99},
)
```

Doubly robust currently supports single-treatment ATE with covariate adjustment
and does not support effect modifiers in the built-in implementation.

## Conditional effects and target units

### `target_units`

| Value | Use |
|---|---|
| `'ate'` | Average treatment effect over all units. |
| `'att'` | Effect on treated units; supported by matching/propensity methods and some others. |
| `'atc'` | Effect on control units; supported by matching/propensity methods and some others. |
| `lambda df: ...` | Row filter for a subpopulation; common with regression/EconML. |
| DataFrame | Effect-modifier values for pointwise CATE in supported estimators. |

Do not assume every estimator supports every form. If an estimator raises
`Target units ... not supported`, choose a supported estimator/target pair.

### Effect modifiers

```python
model = CausalModel(
    data=df,
    treatment="T",
    outcome="Y",
    graph=graph,
    effect_modifiers=["X"],
)
estimate = model.estimate_effect(
    identified_estimand,
    method_name="backdoor.linear_regression",
    effect_modifiers=["X"],
)
print(estimate.conditional_estimates)
```

Numeric effect modifiers are automatically binned into quantiles for conditional
estimates. If bins are not meaningful, create your own categorical modifier
column and use that as the effect modifier.

## Reuse a fitted estimator

A fitted estimator is cached by exact method name. Reuse is useful for applying
the same model to different target units or compatible data slices.

```python
method = "backdoor.linear_regression"
first = model.estimate_effect(identified_estimand, method_name=method)
assert model.get_estimator(method) is first.estimator

subset_effect = model.estimate_effect(
    identified_estimand,
    method_name=method,
    fit_estimator=False,
    target_units=lambda frame: frame["X"] > 0,
)
```

Recovery rules:

- If `fit_estimator=False` refits unexpectedly or returns incompatible results,
  check that a previous call with the same method succeeded.
- Refit if the training data, effect modifiers, categorical encoding, or
  adjustment set changed.
- For external ML estimators, ensure the new target DataFrame has the same
  feature/effect-modifier schema used during fit.

## `CausalModel.do`

```python
do_treated = model.do(
    x=1,
    identified_estimand=identified_estimand,
    method_name="backdoor.linear_regression",
)
do_control = model.do(
    x=0,
    identified_estimand=identified_estimand,
    method_name="backdoor.linear_regression",
)
print(float(do_treated) - float(do_control))
```

Use `CausalModel.do` for expected outcome under a forced treatment value from
the classic model. This differs from pandas `df.causal.do`, which returns an
interventional sampled DataFrame, and from GCM interventions, which use fitted
mechanisms.

Stop or switch estimator when a selected estimator does not implement `do`.

## Refute and sensitivity-test estimates

```python
refuters = [
    ("random_common_cause", {"num_simulations": 20, "random_state": 7}),
    ("placebo_treatment_refuter", {"num_simulations": 20, "placebo_type": "permute", "random_state": 7}),
    ("data_subset_refuter", {"num_simulations": 20, "subset_fraction": 0.8, "random_state": 7}),
]
for method_name, kwargs in refuters:
    result = model.refute_estimate(identified_estimand, estimate, method_name=method_name, **kwargs)
    print(method_name, result.new_effect, result.refutation_result)
```

For repeated simulations, use low `num_simulations` for smoke checks and larger
values for conclusions. Several refuters support `n_jobs` and `verbose` through
`model.refute_estimate`.

### Unobserved confounding sensitivity

```python
sensitivity = model.refute_estimate(
    identified_estimand,
    estimate,
    method_name="add_unobserved_common_cause",
    simulation_method="direct-simulation",
    confounders_effect_on_treatment="binary_flip",
    confounders_effect_on_outcome="linear",
    effect_strength_on_treatment=[0.001, 0.005, 0.01],
    effect_strength_on_outcome=0.01,
    n_jobs=1,
    verbose=0,
)
```

Prefer domain-bounded effect strengths. Auto-inferred bounds assume no
unobserved confounder is stronger than observed ones; state this assumption.

## Validation steps

- Print or inspect the identified estimand before estimating.
- For graph-based workflows, run a graph/data alignment check and consider
  `model.refute_graph` before effect refuters.
- Compare at least two plausible estimators when assumptions differ, for
  example linear regression and propensity weighting.
- For propensity methods, inspect overlap and whether strata/matches are
  retained.
- For IV, verify instrument relevance, exclusion, and number of instruments
  outside DoWhy; DoWhy cannot prove these design assumptions.
- For CATE, inspect `conditional_estimates` or `cate_estimates` shape and ensure
  target-unit filters select a nonempty subset.
- For refuters, interpret p-values and new effects in context; a non-rejection
  is not proof of correctness.
