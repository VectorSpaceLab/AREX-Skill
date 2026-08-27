# Effect Estimation API Reference

This reference covers DoWhy's classic `CausalModel` potential-outcomes workflow.
The signatures below were verified from the installed DoWhy package used to
build this skill. They are runtime API facts, not source-tree links.

## Scope boundary

Use these APIs for classic treatment-effect estimation. Route `dowhy.gcm`
mechanism, sampling, intervention, counterfactual, anomaly, and distribution-
change tasks to the graphical-causal-models sub-skill. Route pandas
`df.causal.do`, graph parsing, plotting, time-series helpers, and data/graph
schema preparation to the data-graph-interfaces sub-skill.

## `CausalModel`

| API | Verified signature | Returns |
|---|---|---|
| Constructor | `CausalModel(data, treatment, outcome, graph=None, common_causes=None, instruments=None, effect_modifiers=None, estimand_type='nonparametric-ate', proceed_when_unidentifiable=False, missing_nodes_as_confounders=False, identify_vars=False, **kwargs)` | A model object with data, treatment/outcome role names, a causal graph, and an estimator cache. |
| Identify | `model.identify_effect(estimand_type=None, method_name='default', proceed_when_unidentifiable=None, optimize_backdoor=False)` | Usually an `IdentifiedEstimand`; with `method_name='id-algorithm'`, an `IDExpression`. |
| Estimate | `model.estimate_effect(identified_estimand, method_name=None, control_value=0, treatment_value=1, test_significance=None, evaluate_effect_strength=False, confidence_intervals=False, target_units='ate', effect_modifiers=None, fit_estimator=True, method_params=None)` | A `CausalEstimate`. |
| Do operator | `model.do(x, identified_estimand, method_name=None, fit_estimator=True, method_params=None)` | A scalar-like expected outcome under `do(treatment=x)` for estimators that implement `do`. |
| Refute | `model.refute_estimate(estimand, estimate, method_name=None, show_progress_bar=False, **kwargs)` | Usually a `CausalRefutation`; some refuters can return a list. |
| Cached estimator | `model.get_estimator(method_name)` | The cached fitted estimator for a method name, or `None`. |

### Constructor inputs

| Input | Use | Notes |
|---|---|---|
| `data` | pandas DataFrame with treatment, outcome, and observed variables. | Treatment/outcome missing from columns trigger early warnings and usually downstream errors. |
| `treatment`, `outcome` | Column name or list of names. | Multi-treatment support depends on estimator; many matching/propensity/frontdoor estimators require one treatment. |
| `graph` | Explicit DAG assumption. | Can be a supported graph object/string/path. If graph formatting is the main issue, route to data-graph-interfaces. |
| `common_causes` | Observed confounders when no graph is supplied. | Used only when `graph is None`. |
| `instruments` | Instrumental variables when no graph is supplied. | Used only when `graph is None`; IV estimators require identified instruments. |
| `effect_modifiers` | Variables for heterogeneous/conditional effects. | Can be supplied in the constructor or in `estimate_effect`; they do not affect identification. |
| `estimand_type` | Target estimand family. | Common values: `'nonparametric-ate'`, `'nonparametric-nde'`, `'nonparametric-nie'`, `'nonparametric-cde'`. |
| `proceed_when_unidentifiable` | Whether to proceed despite possible unobserved confounding. | Use only when the user accepts the risk; record the assumption. |
| `missing_nodes_as_confounders` | Treat DataFrame variables absent from a supplied graph as confounders. | Helpful for partial graphs, but verify names and assumptions. |
| `identify_vars` | Populate common causes, instruments, and effect modifiers from graph during initialization. | Use when the user wants graph-derived role lists; avoid if explicit role lists should be preserved. |

## Identification APIs

| API | Verified signature | Return object |
|---|---|---|
| `identify_effect_auto` | `identify_effect_auto(graph, action_nodes, outcome_nodes, observed_nodes, estimand_type, conditional_node_names=None, backdoor_adjustment=BackdoorAdjustment.BACKDOOR_DEFAULT, optimize_backdoor=False, costs=None, generalized_adjustment=GeneralizedAdjustment.GENERALIZED_ADJUSTMENT_DEFAULT)` | `IdentifiedEstimand`. |
| `identify_effect_id` | `identify_effect_id(graph, action_nodes, outcome_nodes)` | `IDExpression`. |
| `identify_effect` | `identify_effect(graph, action_nodes, outcome_nodes, observed_nodes)` | `IdentifiedEstimand`. |

### `model.identify_effect` method names

| `method_name` | Meaning | Output caveat |
|---|---|---|
| `'default'` | Auto-identify ATE using backdoor, IV, frontdoor, and generalized adjustment where available. | Returns one `IdentifiedEstimand` containing multiple candidate estimands. |
| `'maximal-adjustment'` | Use a maximal valid backdoor set. | Fast, may include superfluous variables. |
| `'minimal-adjustment'` | Use a minimal valid backdoor set. | Can take longer on large graphs. |
| `'exhaustive-search'` | Enumerate valid backdoor sets. | Potentially expensive; bounded internally. |
| `'efficient-adjustment'` | Compute an asymptotically efficient adjustment set when graph conditions allow. | Requires graph conditions for efficient backdoor algorithms. |
| `'efficient-minimal-adjustment'` | Efficient minimal backdoor set. | Same graph-condition caveats. |
| `'efficient-mincost-adjustment'` | Efficient minimum-cost set. | Costs may be supplied through functional API; otherwise constant costs are assumed in the efficient algorithm. |
| `'id-algorithm'` | Run the Shpitser-Pearl ID algorithm. | Returns `IDExpression`, not the usual `IdentifiedEstimand`; do not pass it directly to `estimate_effect`. |

### `IdentifiedEstimand` fields and helpers

| Field or helper | Meaning |
|---|---|
| `treatment_variable`, `outcome_variable` | Parsed treatment and outcome variable lists. |
| `estimand_type` | ATE/NDE/NIE/CDE enum value. |
| `estimands` | Dictionary of symbolic estimands by identifier key, such as `backdoor`, `iv`, `frontdoor`, `general_adjustment`. |
| `backdoor_variables`, `general_adjustment_variables` | Candidate adjustment sets by key. |
| `instrumental_variables`, `frontdoor_variables`, `mediator_variables` | Variables found for IV, frontdoor, or mediation paths. |
| `mediation_first_stage_confounders`, `mediation_second_stage_confounders` | Stage-specific adjustment sets for two-stage mediation/frontdoor estimators. |
| `identifier_method` | Set by `estimate_effect` from the method-name prefix. |
| `no_directed_path` | True when no directed path from treatment to outcome is present; effect is treated as zero. |
| `get_adjustment_set()` | Returns the active backdoor or generalized adjustment set. |
| `get_backdoor_variables()`, `get_general_adjustment_variables()` | Return adjustment variables by active or requested key. |
| `get_instrumental_variables()`, `get_frontdoor_variables()`, `get_mediator_variables()` | Return corresponding strategy variables. |

## Estimation API

`model.estimate_effect(...)` always needs an explicit `method_name`. DoWhy now
raises a `ValueError` when `method_name=None` instead of attempting a default
estimator.

| Parameter | Meaning | Practical notes |
|---|---|---|
| `identified_estimand` | Result of `identify_effect`. | The method-name prefix must correspond to a non-null estimand inside this object. |
| `method_name` | Estimator selector in `<identifier>.<estimator>` form. | Examples: `backdoor.linear_regression`, `iv.instrumental_variable`, `frontdoor.two_stage_regression`. |
| `control_value`, `treatment_value` | Treatment contrast values. | Lists are allowed for multivariate treatments where the estimator supports them. |
| `test_significance` | Enable estimator significance testing. | Use `True` or `'bootstrap'`; set small simulation counts for quick checks. |
| `evaluate_effect_strength` | Experimental fraction-effect diagnostic. | Compares against a naive observational contrast. |
| `confidence_intervals` | Enable confidence intervals. | `True` uses estimator-specific intervals when available, otherwise bootstrap; `'bootstrap'` forces bootstrap. |
| `target_units` | Effect target population. | Common strings: `'ate'`, `'att'`, `'atc'`; some estimators accept a DataFrame or row-filter lambda. |
| `effect_modifiers` | Variables for conditional effects. | Overrides graph/model effect modifiers for estimation; must be present in data. |
| `fit_estimator` | Whether to fit before estimating. | `False` reuses the cached estimator for the exact method name; use after one successful fit. |
| `method_params` | Method-specific init and fit arguments. | Top-level keys go to estimator construction; nested `fit_params` go to estimator `fit`. |

### `CausalEstimate` return object

| Attribute or method | Meaning |
|---|---|
| `value` | Main scalar/array effect estimate. |
| `target_estimand` | Identified estimand used for the estimate. |
| `realized_estimand_expr` | Estimator-specific realized estimand expression or symbolic string. |
| `estimator` | Fitted estimator object used to compute the estimate. |
| `control_value`, `treatment_value` | Contrast values used. |
| `conditional_estimates` | Conditional effects as a pandas Series when available. |
| `cate_estimates` | Pointwise CATE estimates for supported external/ML estimators. |
| `effect_intervals` | Some external estimators store pointwise intervals here. |
| `effect_strength` | Optional effect-strength diagnostic. |
| `get_confidence_intervals(...)` | Compute or retrieve confidence intervals. |
| `get_standard_error(...)` | Compute or retrieve standard errors. |
| `test_stat_significance(...)` | Return a p-value dictionary. |
| `estimate_conditional_effects(effect_modifiers=None, num_quantiles=5)` | Compute effects over effect-modifier groups; numeric modifiers are quantile-binned. |
| `interpret(...)` | Run a DoWhy interpreter for the estimate if the interpreter is available. |

## `CausalModel.do`

Use `model.do(x, identified_estimand, method_name=...)` when the user asks for
`E[Y | do(T=x)]` from the classic model. The method name is required and uses the
same `<identifier>.<estimator>` grammar. Prefer regression-style estimators such
as `backdoor.linear_regression` for a safe first attempt, because many built-in
estimators do not implement the `do` operation and will raise
`NotImplementedError` or a method-specific error.

`fit_estimator=False` for `do` reuses `model.causal_estimator`, not the
`estimate_effect` cache. Use the default first, then reuse only if the same
model has already completed a compatible `do` call.

## Refutation API

`model.refute_estimate(estimand, estimate, method_name=..., show_progress_bar=False, **kwargs)`
requires both an `IdentifiedEstimand` and a valid `CausalEstimate` whose
`value` is not `None`.

| Refuter result | Meaning |
|---|---|
| `estimated_effect` | Original estimate value. |
| `new_effect` | Mean or sensitivity-adjusted effect from the refuter. |
| `refutation_type` | Human-readable refuter label. |
| `refutation_result` | Optional p-value/significance dictionary for simulation refuters. |
| `refuter` | Refuter instance, when added by the class wrapper. |

Common refuter kwargs include `num_simulations`, `random_state` or
`random_seed`, `n_jobs`, `verbose`, `subset_fraction`, `placebo_type`,
`required_variables`, `noise`, and sensitivity-analysis parameters. See the
estimators-and-refuters reference for method-specific choices.

## Graph validation helper

`model.refute_graph(k=1, independence_test=None, independence_constraints=None)`
checks conditional independence constraints implied by a supplied graph. Use it
as a graph-assumption diagnostic before trusting effect estimates. If the user
is mainly parsing or plotting graphs, route to data-graph-interfaces first.
