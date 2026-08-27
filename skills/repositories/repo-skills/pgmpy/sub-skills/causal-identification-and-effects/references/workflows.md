# Causal Identification and Effects Workflows

## Purpose

Use these recipes to move from a stated causal estimand to pgmpy code. Each workflow assumes the user supplies or accepts a causal graph; structure discovery belongs to another sub-skill.

## Workflow 1: Identify a Backdoor Adjustment Set

Use this before ATE/regression when confounding is possible.

```python
from pgmpy.base import DAG
from pgmpy.identification import Adjustment

# Z is a confounder of X -> Y.
dag = DAG(
    [("Z", "X"), ("Z", "Y"), ("X", "Y")],
    roles={"exposures": "X", "outcomes": "Y"},
)

identified_graph, success = Adjustment(variant="minimal").identify(dag)
if not success:
    raise RuntimeError("No graph-valid minimal adjustment set was found.")

adjustment = identified_graph.get_role("adjustment")
assert Adjustment(variant="minimal").validate(identified_graph)
print(adjustment)  # ['Z']
```

Decision points:

- If the user proposes a set, annotate it as `roles={"adjustment": [...]}` and run `Adjustment(...).validate(graph)` before using it.
- If `variant="all"`, `identify` returns a list of graphs and `success`; inspect each graph's `adjustment` role.
- If `success` is false, do not estimate the effect from observational data unless another valid identification strategy is available.
- `variant="minimal_variance"` is not implemented; do not route users to it.

## Workflow 2: Try Frontdoor When Backdoor Fails

Use frontdoor when an exposure-outcome path is mediated and a latent confounder blocks backdoor adjustment.

```python
from pgmpy.base import DAG
from pgmpy.identification import Frontdoor

frontdoor_graph = DAG(
    [("X", "M"), ("M", "Y"), ("U", "X"), ("U", "Y")],
    latents={"U"},
    roles={"exposures": "X", "outcomes": "Y"},
)

identified_graph, success = Frontdoor().identify(frontdoor_graph)
if not success:
    raise RuntimeError("The graph does not satisfy pgmpy's frontdoor criterion.")

frontdoor_vars = identified_graph.get_role("frontdoor")
assert Frontdoor().validate(identified_graph)
print(frontdoor_vars)  # ['M']
```

Notes:

- `Frontdoor` currently supports `DAG` graphs.
- With `Frontdoor(variant="all")`, inspect every returned graph; with the default variant, pgmpy returns one valid frontdoor assignment.
- Frontdoor identification is not the same thing as fitting a mediator regression. It is a graphical criterion that must hold before estimation.

## Workflow 3: Run an Interventional Query with `do`

Use this for discrete fitted models with CPDs when the user asks for `P(Y | do(X=x))` or `P(Y | do(X=x), Z=z)`.

```python
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import CausalInference
from pgmpy.models import DiscreteBayesianNetwork

model = DiscreteBayesianNetwork([("S", "T"), ("S", "C"), ("T", "C")])
model.add_cpds(
    TabularCPD("S", 2, [[0.5], [0.5]], state_names={"S": ["m", "f"]}),
    TabularCPD(
        "T",
        2,
        [[0.25, 0.75], [0.75, 0.25]],
        evidence=["S"],
        evidence_card=[2],
        state_names={"S": ["m", "f"], "T": [0, 1]},
    ),
    TabularCPD(
        "C",
        2,
        [[0.3, 0.4, 0.7, 0.8], [0.7, 0.6, 0.3, 0.2]],
        evidence=["S", "T"],
        evidence_card=[2, 2],
        state_names={"S": ["m", "f"], "T": [0, 1], "C": [0, 1]},
    ),
)

ci = CausalInference(model)
observed = ci.query(variables=["C"], evidence={"T": 1}, show_progress=False)
intervened = ci.query(variables=["C"], do={"T": 1}, show_progress=False)
print(observed.values, intervened.values)
```

Rules:

- `evidence={"T": 1}` means condition on observed treatment; `do={"T": 1}` means intervene and sever incoming causes of `T`.
- If `do` is omitted, `CausalInference.query` delegates to ordinary probabilistic inference. Route ordinary posterior questions elsewhere.
- If `adjustment_set` is omitted, pgmpy uses parents of the do variables. If any parent is latent, pass a validated observed adjustment set or stop.
- Use state names that exist in the CPDs; strings like `"LOW"` work only when the model defines those states.

## Workflow 4: Estimate ATE from a Graph and Data

Use when the user asks for an average treatment effect and has observational data plus a causal graph.

```python
import numpy as np
import pandas as pd
from pgmpy.base import DAG
from pgmpy.identification import Adjustment
from pgmpy.inference import CausalInference

rng = np.random.default_rng(7)
Z = rng.normal(size=200)
X = 0.6 * Z + rng.normal(size=200)
Y = 2.0 * X + 0.3 * Z

data = pd.DataFrame({"X": X, "Z": Z, "Y": Y})
graph = DAG(
    [("Z", "X"), ("Z", "Y"), ("X", "Y")],
    roles={"exposures": "X", "outcomes": "Y"},
)

identified_graph, success = Adjustment(variant="minimal").identify(graph)
if not success:
    raise RuntimeError("ATE is not identified by a minimal adjustment set.")

ate = CausalInference(graph).estimate_ate(
    "X",
    "Y",
    data=data,
    estimand_strategy="smallest",
    estimator_type="linear",
)
print(float(ate))
```

Guidance:

- `estimate_ate` currently exposes `estimator_type="linear"` for public use.
- `estimand_strategy="smallest"` selects one graph-derived set; `"all"` estimates over all identified sets; a supplied frozenset is a manual choice that should be validated.
- Data must include all observed variables used along the causal paths and any adjustment sets.
- If pgmpy raises that no valid adjustment set was found, do not backfill with an arbitrary set.

## Workflow 5: Fit an Adjustment Regressor

Use `NaiveAdjustmentRegressor` as a lightweight sklearn-style estimator after identifying an adjustment set.

```python
import numpy as np
import pandas as pd
from pgmpy.base import DAG
from pgmpy.identification import Adjustment
from pgmpy.prediction import NaiveAdjustmentRegressor

rng = np.random.default_rng(7)
Z = rng.normal(size=100)
X = 0.6 * Z + rng.normal(size=100)
Y = 2.0 * X + 0.3 * Z

data = pd.DataFrame({"X": X, "Z": Z, "Y": Y})
graph = DAG(
    [("Z", "X"), ("Z", "Y"), ("X", "Y")],
    roles={"exposures": "X", "outcomes": "Y"},
)
identified_graph, success = Adjustment().identify(graph)
if not success:
    raise RuntimeError("No adjustment role identified.")

reg = NaiveAdjustmentRegressor(causal_graph=identified_graph)
reg.fit(data[["X", "Z"]], data["Y"])
print(reg.explanation_)
print(reg.predict(data[["X", "Z"]].head()))
```

Checklist:

- Feature data must include exposure + adjustment + pretreatment columns by exact name.
- Missing and empty `adjustment` both run, but an empty adjustment set is a causal claim; validate it.
- Custom sklearn regressors are allowed through `estimator=...`, but causal validity still comes from the graph/roles.

## Workflow 6: Fit a Double ML Regressor

Use `DoubleMLRegressor` for a cross-fitted partial-linear workflow when treatment and outcome nuisance functions should be estimated separately.

```python
from pgmpy.base import DAG
from pgmpy.prediction import DoubleMLRegressor
from sklearn.linear_model import LinearRegression

# data has columns D, Z1, Z2, Y.
graph = DAG(
    [("Z1", "D"), ("Z2", "D"), ("D", "Y"), ("Z1", "Y"), ("Z2", "Y")],
    roles={"exposures": "D", "outcomes": "Y", "adjustment": ["Z1", "Z2"]},
)

model = DoubleMLRegressor(
    causal_graph=graph,
    nuisance_estimators=LinearRegression(),
    effect_estimator=LinearRegression(),
    n_folds=3,
    seed=0,
)
model.fit(data[["D", "Z1", "Z2"]], data["Y"])
theta = model.effect_est_.coef_
```

Notes:

- `n_folds=1` disables cross-fitting and uses in-sample nuisance predictions.
- A tuple `(treatment_estimator, outcome_estimator)` can be supplied for different nuisance models.
- The final effect estimator should usually be linear for the usual Double ML interpretation.

## Workflow 7: Fit a Naive IV Regressor

Use `NaiveIVRegressor` only when the graph and domain assumptions justify the supplied instruments.

```python
from pgmpy.base import DAG
from pgmpy.prediction import NaiveIVRegressor
from sklearn.linear_model import LinearRegression

# data has columns X, Z1, Z2, Y.
graph = DAG(
    [("Z1", "X"), ("Z2", "X"), ("X", "Y")],
    roles={"exposures": "X", "outcomes": "Y", "instrument": ["Z1", "Z2"]},
)

iv = NaiveIVRegressor(
    causal_graph=graph,
    stage1_estimator=LinearRegression(),
    stage2_estimator=LinearRegression(),
)
iv.fit(data[["X", "Z1", "Z2"]], data["Y"])
print(iv.coef_)
print(iv.predict(data[["X"]].head()))
```

IV reminders:

- The role name is singular `instrument`.
- The first stage predicts exposure from instruments; the second stage predicts outcome from predicted exposure plus optional pretreatment covariates.
- pgmpy does not prove that a user-labeled instrument is valid. Check graph/domain assumptions before making an IV claim.

## Quick Environment Smoke

Run the bundled helper when you need a deterministic sanity check of installed pgmpy causal APIs:

```bash
python sub-skills/causal-identification-and-effects/scripts/causal_effect_smoke.py
```

It builds tiny fixtures and checks adjustment identification, frontdoor identification, `CausalInference.estimate_ate`, and `NaiveAdjustmentRegressor` without reading local repository files or downloading data.
