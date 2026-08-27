# Causal Troubleshooting

## Purpose

Use this matrix when pgmpy causal identification, interventional queries, ATE, or causal regressors fail or produce a result that is easy to misinterpret.

| Symptom or error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `must have at least one 'exposures' and one 'outcomes' role` | The graph has edges but no causal roles. | Rebuild with `roles={"exposures": ..., "outcomes": ...}` or add roles with `with_role`. Run `get_role_dict()` before calling `Adjustment`/`Frontdoor`. |
| `Exactly one exposure variable must be defined` or `only supports a single exposure` | A prediction regressor received zero or multiple exposure variables. | Split the task into one exposure-outcome estimand per fit, or choose an API that explicitly supports the intended multivariate query. |
| `Exactly one outcome variable must be defined` or `only supports a single outcome` | A prediction regressor received zero or multiple outcomes. | Fit one outcome at a time and pass the corresponding target series/dataframe column as `y`. |
| `Backdoor identification is only implemented for single exposure variable` | `Adjustment(variant="minimal")` received multiple exposures or outcomes. | Use a single exposure/outcome pair for minimal adjustment, or inspect `variant="all"` only if the graph/query semantics still match the task. |
| `minimal_variance` raises `NotImplementedError` | The variant is declared but not implemented. | Use `variant="minimal"` or `variant="all"`; document that minimal-variance adjustment is unavailable. |
| `success` is `False`, adjustment role is absent, or `get_minimal_adjustment_set` returns `None` | The graph is not identifiable by the attempted criterion, often because required blockers are latent. | Do not invent covariates. Try `Frontdoor` when a mediator exists and its criterion may hold; otherwise report non-identifiability for this graph. |
| `Frontdoor().identify(...)` returns `False` | Candidate mediators do not intercept all directed paths or fail frontdoor backdoor subconditions. | Check whether every directed path from exposure to outcome passes through the proposed mediator and whether the necessary backdoor paths are blocked. If not, stop or use another design. |
| `The causal_graph must be an instance of ...` | The identification method does not support the graph type. | Use a supported graph class. `Frontdoor` supports `DAG`; `Adjustment` supports DAG/PDAG/ADMG/MAG for implemented variants. |
| `Variable 'Z' not found in the graph` | A role assignment names a variable not present as a graph node. | Add the node/edge first, or correct spelling/case. Verify `set(graph.nodes())` against the role dictionary. |
| `Missing required columns in input data` | Regressor feature `X` does not include every role-derived required feature. | Build `X` from the role columns: exposure + adjustment + pretreatment for adjustment/DML, or exposure + instrument + pretreatment for IV fitting. Column names must exactly match graph variables. |
| Regressor accepts extra feature columns but ignores them in outputs | pgmpy filters to role-required columns after validation. | Do not assume unused columns are part of the effect model. Inspect `feature_columns_fit_` and `get_feature_names_out()` where available. |
| Numeric validation fails, or categorical strings cause sklearn errors | `pgmpy.prediction` regressors call sklearn numeric validation. | Encode categorical variables before fitting, or use a suitable numeric sklearn pipeline/transformer outside pgmpy's regressor. Keep graph role names aligned with transformed columns. |
| NumPy array input fails with missing columns | Arrays are converted to DataFrames with integer column names `0, 1, ...`. | Prefer pandas DataFrames for string-named variables. If using arrays, construct the DAG with integer node names and integer role variables. |
| `NaiveIVRegressor requires at least one instrument` | The graph lacks singular role `instrument`, or the user used `instruments` only. | Add `roles={"instrument": [...]}` for IV regressors. If using `SimpleCausalModel`, add a singular `instrument` role to the instrument nodes before fitting. |
| IV estimate is requested from a weak or invalid instrument | pgmpy reads role labels but does not prove IV validity. | Check domain assumptions: instrument affects exposure, affects outcome only through exposure, and is independent of unobserved outcome causes. If these are not defensible, do not report an IV causal estimate. |
| `variables much be a list` or query variable not in model | `CausalInference.query` received a string variable or unknown variable. | Pass `variables=["Y"]`, not `variables="Y"`, and verify query/do/evidence names are model nodes. |
| `do must be a dict` or `evidence must be a dict` | `CausalInference.query` received scalar/list arguments. | Use `do={"X": state}` and `evidence={"Z": state}`. Empty or omitted `do` means ordinary probabilistic inference. |
| `inference_algo must be one of: 've', 'bp'...` | Unsupported inference algorithm name or object. | Use `inference_algo="ve"`, `"bp"`, or pass a compatible pgmpy inference instance. |
| `Not all parents of do variables are observed. Please specify an adjustment set.` | Default adjustment uses parents of the intervention variable, and at least one parent is latent. | Supply a validated observed adjustment set or stop if no valid observed adjustment exists. |
| Unexpected difference between `evidence={"X": x}` and `do={"X": x}` | This is usually correct: conditioning and intervention answer different questions. | Clarify the estimand with the user. Use ordinary inference for `P(Y | X=x)`; use this sub-skill for `P(Y | do(X=x))`. |
| `Invalid causal query: There is a direct edge from the query variable ... to the intervention variable ...` | The requested counterfactual/interventional direction violates pgmpy's query guard. | Recheck cause/effect direction and formulate the query over descendants of the intervention when appropriate. |
| `estimate_ate` raises no-valid-adjustment errors | The graph path effect cannot be estimated with pgmpy's current backdoor strategy. | Re-run identification explicitly. If a frontdoor or IV strategy is intended, use the corresponding workflow and do not force `estimate_ate`. |
| Causal effect estimate looks plausible but graph roles were never validated | Predictive fit succeeded, but causal assumptions were not checked. | Record the graph, roles, identification method, validation result, data columns, and estimator class before reporting an effect. |

## Recovery Checklist for Hard Cases

1. Print `graph.get_role_dict()` and verify role spelling exactly: `exposures`, `outcomes`, `adjustment`, `frontdoor`, singular `instrument`, and optional `pretreatment`.
2. Print `set(graph.nodes())` and compare with every role variable and DataFrame column.
3. Run the relevant identification validator: `Adjustment().validate(graph)` or `Frontdoor().validate(graph)`.
4. For regressors, inspect fitted attributes such as `exposure_var_`, `outcome_var_`, `adjustment_vars_`, `instrument_vars_`, `pretreatment_vars_`, and `feature_columns_fit_`.
5. Use [../scripts/causal_effect_smoke.py](../scripts/causal_effect_smoke.py) to confirm the installed package can run a known-good fixture before debugging user-specific data.

## Stop Conditions

Stop and report uncertainty instead of estimating when:

- The requested estimand is not clear enough to distinguish `P(Y | X=x)` from `P(Y | do(X=x))`.
- The causal graph is absent and the task is not graph discovery.
- Identification returns `False` or validation fails for all candidate sets.
- The required adjustment/instrument/frontdoor variables are latent or missing from data.
- The user asks for a causal claim that the supplied graph and data do not justify.
