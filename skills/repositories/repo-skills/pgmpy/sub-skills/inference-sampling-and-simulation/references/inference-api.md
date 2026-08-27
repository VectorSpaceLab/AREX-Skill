# Inference and Sampling API Map

This reference summarizes the pgmpy public APIs most often needed after a model
has already been created and parameterized. Examples assume a valid, installed
`pgmpy` package and do not require access to a source checkout.

## Imports

```python
from pgmpy.global_vars import config
from pgmpy.inference import (
    ApproxInference,
    BeliefPropagation,
    DBNInference,
    VariableElimination,
)
from pgmpy.sampling import BayesianModelSampling, GibbsSampling
```

Set `config.set_show_progress(False)` in non-interactive automation. Most calls
also accept a per-call `show_progress=False` argument.

## Exact inference

| Class | Model families | Main methods | Returns | Use when |
|---|---|---|---|---|
| `VariableElimination(model)` | `DiscreteBayesianNetwork`, `DiscreteMarkovNetwork`, `FactorGraph`, `JunctionTree`, compatible discrete factors | `query(variables, evidence=None, virtual_evidence=None, elimination_order="greedy", joint=True, show_progress=True)`; `map_query(variables=None, evidence=None, virtual_evidence=None, elimination_order="MinFill", show_progress=True)` | `DiscreteFactor` for joint queries, `dict[var, DiscreteFactor]` for `joint=False`, and `dict[var, state]` for MAP | Default exact posterior/MAP engine for small-to-medium discrete models. |
| `BeliefPropagation(model)` | Discrete BN, Markov network, factor graph, or junction tree | `query(variables, evidence=None, virtual_evidence=None, joint=True, show_progress=True)`; `map_query(variables=None, evidence=None, virtual_evidence=None, show_progress=True)` | Same broad result shape as exact inference | Repeated exact queries or junction-tree workflows. |

Rules that matter in practice:

- `variables` must be non-empty for `query(...)`.
- No query variable may also appear in `evidence`.
- Evidence keys must be model variables; evidence values must be CPD state names
  or valid state numbers for models without named states.
- `virtual_evidence` is a list of `TabularCPD` objects on individual variables;
  its cardinality and state names must match the target model variable.
- For `VariableElimination`, automatic elimination-order options include
  `"greedy"`, `"WeightedMinFill"`, `"MinNeighbors"`, `"MinWeight"`, and
  `"MinFill"`. A custom list should contain all eliminable variables after query
  variables and evidence are excluded/pruned.
- Use `induced_width(order)` or smaller query/evidence sets to diagnose exact
  inference that is too large.

## Approximate inference

| Class | Models | Main methods | Returns | Use when |
|---|---|---|---|---|
| `ApproxInference(model)` | `DiscreteBayesianNetwork`, `DynamicBayesianNetwork` | `query(variables, n_samples=10000, samples=None, evidence=None, virtual_evidence=None, joint=True, state_names=None, show_progress=True, seed=None)`; `map_query(...)` | Empirical `DiscreteFactor` or `dict[var, DiscreteFactor]`; MAP returns `dict[var, state]` | Exact inference is slow or a sampling approximation is acceptable. |

Notes:

- `samples=` can reuse a prefiltered DataFrame, but it must already conform to
  the evidence and virtual evidence supplied to the query.
- For named-state variables, pass `state_names=` when a small sample might miss
  rare states; otherwise inferred factors can omit states that did not appear in
  the sample.
- For DBNs, variables and evidence are tuple nodes such as `("Y", 4)`.
  `ApproxInference` automatically simulates enough time slices to cover the
  highest time index in variables, evidence, and virtual evidence.

## Direct Bayesian-network samplers

| Class/method | Inputs | Output | Notes |
|---|---|---|---|
| `BayesianModelSampling(model).forward_sample(size=1, include_latents=False, seed=None, show_progress=True, partial_samples=None, n_jobs=-1)` | A valid discrete BN | pandas DataFrame | Draws from the joint distribution. `partial_samples` fixes supplied columns; row count should match the desired sample size. |
| `BayesianModelSampling(model).rejection_sample(evidence=[], size=1, include_latents=False, seed=None, show_progress=True, partial_samples=None)` | Evidence as `State(var, state)` namedtuples or `(var, state)` pairs | pandas DataFrame | Rejection sampling can be very slow for low-probability evidence. |
| `BayesianModelSampling(model).likelihood_weighted_sample(evidence=[], size=1, include_latents=False, seed=None, show_progress=True, n_jobs=-1)` | Evidence as `State(var, state)` namedtuples or pairs | pandas DataFrame with `_weight` column | Better than rejection sampling for unlikely evidence; downstream code must respect `_weight`. |
| `GibbsSampling(model).sample(start_state=None, size=1, seed=None, include_latents=False)` | Discrete BN or Markov network | pandas DataFrame | Useful for approximate sampling from Markov networks or BNs. Provide `start_state` with valid integer state ids when controlling initialization. |
| `GibbsSampling(model).generate_sample(start_state=None, size=1, include_latents=False, seed=None)` | Same | generator of lists of `State(var, state)` | Streaming/generator version. |

## Model-level simulation

`DiscreteBayesianNetwork.simulate(...)` wraps the BN sampler and handles common
simulation conditions:

```python
samples = model.simulate(
    n_samples=100,
    do=None,
    evidence=None,
    virtual_evidence=None,
    virtual_intervention=None,
    missing_prob=None,
    include_latents=False,
    partial_samples=None,
    seed=42,
    show_progress=False,
    return_full=False,
)
```

Key distinctions:

- `evidence={"X": state}` conditions on observed variables.
- `do={"X": state}` applies a hard intervention for generating samples; it is
  not a full causal-effect identification workflow.
- `virtual_evidence=[TabularCPD(...)]` applies soft evidence and adds temporary
  helper variables internally.
- `virtual_intervention=[TabularCPD(...)]` is a soft intervention; it is handled
  by modifying the network then applying virtual evidence.
- `missing_prob=` takes one or more `TabularCPD` objects whose variable names end
  in `*`, such as `"CVP*"`, and whose first cardinality is 2 for not-missing vs
  missing indicators.
- `return_full=True` preserves original values in `*_full` columns before
  missingness masking.

`DynamicBayesianNetwork.simulate(...)` accepts analogous `do`, `evidence`,
`virtual_evidence`, and `virtual_intervention` dictionaries/lists keyed by tuple
nodes. It adds `n_time_slices` and `return_format` with choices including
`"wide"`, `"sorted"`, `"numpy3d"`, `"pd-multiindex"`, and `"pd-list"`.

## Dynamic Bayesian Network inference

`DBNInference(model)` performs exact interface-algorithm inference on a valid
`DynamicBayesianNetwork`.

```python
from pgmpy.inference import DBNInference

infer = DBNInference(dbn)
result = infer.query(
    variables=[("X", 2)],
    evidence={("Y", 0): 1, ("Y", 1): 0},
)
posterior_x2 = result[("X", 2)]
```

DBN requirements:

- Use tuple nodes `(variable_name, time_slice)` consistently in edges, CPDs,
  query variables, evidence, and interventions.
- Add CPDs for the initial slice and transition slice, then call
  `initialize_initial_state()` before inference or simulation.
- `DBNInference.query(..., args="exact")` dispatches to exact backward inference;
  lower-level `forward_inference` and `backward_inference` return dictionaries of
  factors keyed by tuple variables.

## Optional dependency surfaces

The minimum verified environment covers core NumPy/CPU inference and sampling.
Functional Bayesian networks require the optional `torch`/`pyro-ppl` extra; LLM
provider credentials, plotting extras, and remote downloads are separate optional
surfaces. Do not claim those optional workflows are available unless the user's
environment imports and verifies them.
