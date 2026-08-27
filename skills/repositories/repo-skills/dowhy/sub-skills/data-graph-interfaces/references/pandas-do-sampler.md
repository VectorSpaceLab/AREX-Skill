# Pandas `.causal.do` And Do-Samplers

This reference explains the pandas causal accessor and DoWhy's do-sampler support.
Use it when the user wants sampled interventional DataFrames, not when the final
request is a fitted treatment-effect estimate.

## Registration

The accessor is registered by importing `dowhy.api`:

```python
import dowhy.api  # registers pandas DataFrame accessor: df.causal
```

After registration, every pandas DataFrame can call:

```python
sampled = df.causal.do(...)
df.causal.reset()
```

## Verified Signature

The inspected runtime signature is:

```python
CausalAccessor.do(
    self,
    x,
    method="weighting",
    num_cores=1,
    variable_types={},
    outcome=None,
    params=None,
    graph=None,
    common_causes=None,
    estimand_type="nonparametric-ate",
    stateful=False,
)
```

The runtime type annotation for `graph` is `networkx.DiGraph`. The default
estimand type is DoWhy's nonparametric ATE enum value.

## What `.causal.do` Returns

`df.causal.do` returns a pandas DataFrame sampled from an interventional outcome
distribution. It replaces or resamples outcome columns according to the sampler
and intervention. It is not the same as `CausalModel.estimate_effect`, and it
does not return a `CausalEstimate` object.

Use cases:

- simulate sampled outcomes under `do(X=x)`;
- compare summary statistics over multiple do-sampled DataFrames;
- generate finite-sample interventional data for exploratory workflows;
- provide a sampling-oriented alternative to an explicit effect estimator.

For final ATE/CATE estimates, estimator method names, refuters, or sensitivity
analysis, route to `../effect-estimation/SKILL.md`.

## Intervention Argument `x`

`x` controls both the intervention variables and whether the original treatment
values are retained.

| Shape | Meaning | Treatment values in output |
|---|---|---|
| `"X"` | Intervene on one variable but do not set a value. | Original observed values are kept. |
| `["X1", "X2"]` | Intervene on multiple variables without fixed values. | Original observed values are kept. |
| `{"X": 1}` | Set one variable to a value. | Output treatment column is fixed after sampling/filtering. |
| `{"X1": 1, "X2": 0}` | Set multiple variables. | Output treatment columns are fixed after sampling/filtering. |

The default `weighting` sampler selects rows that exactly match requested
intervention values before resampling. For continuous treatments or values not
observed in the data, this can fail with an exact-match error. For continuous
what-if values, consider whether a different sampler or a fitted effect/GCM
workflow is more appropriate.

## Required Identification Inputs

The sampler needs treatment/action nodes, outcome nodes, observed nodes, data,
and an identified adjustment set.

Provide one of:

- `graph=nx.DiGraph(...)` with treatment, outcome, and adjustment nodes; or
- `common_causes=[...]`, which lets DoWhy build a simple graph internally.

Also provide:

- `outcome="Y"` or a list-like outcome specification;
- `variable_types` when inference is not safely inferable from pandas dtypes;
- `method` if not using the default weighting sampler;
- `params` only for method-specific sampler attributes.

## Variable Type Codes

DoWhy's do-samplers use short type codes rather than pandas dtype names.

| Code | Meaning | Common use |
|---|---|---|
| `c` | continuous | numeric continuous columns; DoWhy also maps pandas ints/floats to `c` when auto-infering. |
| `b` | binary | boolean treatment/outcome/covariate columns. |
| `d` | discrete | unordered discrete or categorical columns when order is not modeled. |
| `o` | ordered discrete | ordered categorical or ordinal variables. |
| `u` | unordered discrete | unordered categorical variables; internal density helpers also treat `d` as unordered. |

The `variable_types` dictionary should contain every treatment, outcome, and
adjustment variable. It can include extra columns; however, if it contains more
variables than the DataFrame has columns, the accessor raises an exception about
the DataFrame having fewer variables than `variable_types`.

## Auto-Inference And Unsupported Dtypes

When `variable_types` is empty, the pandas accessor converts DataFrame dtypes:

- any dtype name containing `int` -> `c`;
- any dtype name containing `float` -> `c`;
- any dtype name containing `bool` -> `b`;
- any dtype name containing `category` -> `d`;
- all other dtype names raise an unsupported-format exception.

This means plain Python/string/object columns are not automatically supported.
For string categories, either convert to pandas `category` or pass an explicit
`variable_types` mapping and ensure downstream sampler operations can encode the
values.

If `variable_types` is partially specified and the DataFrame has additional
columns, the accessor fills missing column types using the same dtype conversion.
Therefore, a single untyped object column can still fail even if the causal
variables were specified. The safest recipe is to give all DataFrame columns a
valid dtype or pass a complete `variable_types` dictionary.

## Sampler Methods

The factory loads sampler classes by method name plus `_sampler`. Public method
names used through `.causal.do` include:

| Method | Class | Notes |
|---|---|---|
| `weighting` | `WeightingSampler` | Default. Uses inverse propensity weighting and exact treatment-value matching when `x` is a dict. Assumes iid data. |
| `multivariate_weighting` | `MultivariateWeightingSampler` | Similar weighting path for multivariate treatment states. Assumes iid data. |
| `kernel_density` | `KernelDensitySampler` | Uses statsmodels conditional KDE. Requires explicit `variable_types`; can be slower for larger data/high dimensions. |
| `mcmc` | `McmcSampler` | Uses PyMC3 Bayesian network sampling; requires `pymc3` and a DAG; supports `c` and `b` node types in its model path. |

Do-samplers implement the same conceptual stages:

1. disrupt causes of the intervention variable, often by accounting for
   selection into treatment;
2. make the intervention effective, either by setting treatment values or
   retaining original values;
3. propagate and sample outcomes into a returned DataFrame.

Do-sampler output varies from sample to sample. For statistics, generate
multiple samples and report variability rather than treating one draw as exact.

## Stateful Behavior

The pandas accessor is stateless by default. Each default call resets cached
sampler state before returning.

`stateful=True` keeps the sampler on `df.causal` so later calls with the same
method can reuse expensive setup. This can be useful for repeated calls with MCMC,
kernel-density, or weighting samplers, but it is easy to misuse.

Rules:

- `df.causal.reset()` clears cached graph, identified estimand, sampler, and
  method.
- If `stateful=False`, the accessor resets before/after a call.
- If `stateful=True` but `method` changes, the accessor resets.
- State belongs to the DataFrame accessor namespace, not just one method call.
- Reset before changing graph, outcome, common causes, variable types, params, or
  the underlying DataFrame content.

## Common Recipes

### Minimal Weighting Sample With Explicit Types

```python
import numpy as np
import pandas as pd
import dowhy.api

rng = np.random.default_rng(7)
n = 200
w = rng.normal(size=n)
x = (w + rng.normal(size=n) > 0).astype(int)
y = 2.0 * x + w + rng.normal(scale=0.2, size=n)
df = pd.DataFrame({"W": w, "X": x, "Y": y})

sampled = df.causal.do(
    x={"X": 1},
    outcome="Y",
    common_causes=["W"],
    variable_types={"W": "c", "X": "d", "Y": "c"},
    method="weighting",
)
assert set(sampled["X"].unique()) == {1}
```

### Use An Explicit Graph

```python
import networkx as nx
import dowhy.api

graph = nx.DiGraph([("W", "X"), ("W", "Y"), ("X", "Y")])
sampled = df.causal.do(
    x={"X": 0},
    outcome="Y",
    graph=graph,
    variable_types={"W": "c", "X": "d", "Y": "c"},
)
```

### Categorical/String Columns

```python
import pandas as pd
import dowhy.api

df = pd.DataFrame({
    "segment": pd.Series(["a", "b", "a", "b"], dtype="category"),
    "X": [0, 1, 0, 1],
    "Y": [1.0, 2.0, 1.1, 1.9],
})
variable_types = {"segment": "d", "X": "d", "Y": "c"}
```

If `segment` remains an object/string dtype and `variable_types` is missing or
partial, auto-inference can raise an unsupported dtype exception. Convert to
`category` or supply a complete mapping.

### Repeated Stateful Calls

```python
for value in [0, 1]:
    sampled = df.causal.do(
        x={"X": value},
        outcome="Y",
        common_causes=["W"],
        variable_types={"W": "c", "X": "d", "Y": "c"},
        stateful=True,
    )

df.causal.reset()
```

Reset immediately after the repeated block, especially before using a different
graph or variable schema.

## Validation Checklist

Before calling `.causal.do`:

1. `import dowhy.api` has run.
2. `x` is a string/list/dict in the intended mode.
3. `outcome` is present in the DataFrame.
4. Every treatment, outcome, and common-cause/adjustment variable is present in
   the DataFrame.
5. The graph, if supplied, includes treatment and outcome nodes.
6. Graph nodes that must be observed have matching DataFrame columns.
7. `variable_types` covers any object/string/categorical/non-obvious columns.
8. The chosen method has its optional dependencies available.
9. The sample size and treatment support are enough for exact matching or density
   estimation.
10. Any stateful run is reset before changing schema or method.

## When To Choose Another Workflow

Route away from `.causal.do` when:

- the user asks for an ATE/CATE estimate, confidence intervals, or refutation;
- treatment values are continuous and exact matching through `weighting` is not
  meaningful;
- the user wants structural interventions on a fitted GCM;
- the user needs counterfactual samples conditioned on observed units;
- the graph/data schema is not yet validated.
