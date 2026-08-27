# Inference, Sampling, and Simulation Workflows

These recipes are written for already-parameterized models. If CPDs, factors,
states, or graph structure still need to be created or fitted, first use the
modeling or learning sub-skills.

## 1. Exact posterior query with validation

```python
from pgmpy.global_vars import config
from pgmpy.inference import VariableElimination

config.set_show_progress(False)
assert model.check_model()

infer = VariableElimination(model)
posterior = infer.query(
    variables=["Wet_Grass"],
    evidence={"Rain": "yes"},
    joint=True,
    show_progress=False,
)
print(posterior)
print(posterior.get_value(Wet_Grass="yes"))
```

For multiple variables, use `joint=True` for one joint factor and `joint=False`
for a dictionary of marginal factors:

```python
marginals = infer.query(
    variables=["Rain", "Sprinkler"],
    evidence={"Wet_Grass": "yes"},
    joint=False,
    show_progress=False,
)
print(marginals["Rain"].values)
```

## 2. MAP query

```python
map_result = infer.map_query(
    variables=["Rain", "Sprinkler"],
    evidence={"Wet_Grass": "yes"},
    show_progress=False,
)
print(map_result)  # {'Rain': 'yes', 'Sprinkler': 'no'} for some models
```

Use MAP only for the variables whose most likely assignment is needed. If the
user asks for full uncertainty, use `query(...)` instead.

## 3. Belief propagation or junction-tree inference

```python
from pgmpy.inference import BeliefPropagation

bp = BeliefPropagation(model)
result = bp.query(
    variables=["Admission"],
    evidence={"Difficulty": "hard"},
    show_progress=False,
)
```

Belief propagation is exact on calibrated junction trees and can be convenient
for repeated exact queries. If the input is a `JunctionTree`, attach clique
potentials/factors before querying.

## 4. Diagnose exact-inference tractability

Exact inference cost depends on graph structure and variable cardinalities. If a
query is slow:

```python
order = [var for var in model.nodes() if var not in {"Wet_Grass", "Rain"}]
width = VariableElimination(model).induced_width(order)
print(width)
```

Then try a smaller query, more evidence, a different elimination-order heuristic,
or `ApproxInference`. Do not use approximate inference unless a sampling error is
acceptable for the task.

## 5. Approximate inference from generated samples

```python
from pgmpy.inference import ApproxInference

approx = ApproxInference(model)
posterior = approx.query(
    variables=["Disease"],
    evidence={"Test": "positive"},
    n_samples=20_000,
    seed=42,
    show_progress=False,
)
map_result = approx.map_query(
    variables=["Disease"],
    evidence={"Test": "positive"},
    n_samples=20_000,
    seed=42,
    show_progress=False,
)
```

If using a supplied DataFrame instead of generating samples, make sure it is
already filtered consistently with the evidence:

```python
filtered = samples[samples["Test"] == "positive"]
posterior = approx.query(
    variables=["Disease"],
    evidence={"Test": "positive"},
    samples=filtered,
    state_names={"Disease": ["absent", "present"]},
    show_progress=False,
)
```

Pass `state_names` for small or imbalanced samples so rare but valid states do
not disappear from the empirical factor.

## 6. Direct sampler classes

Forward samples from a discrete BN:

```python
from pgmpy.sampling import BayesianModelSampling

sampler = BayesianModelSampling(model)
samples = sampler.forward_sample(size=100, seed=42, show_progress=False)
```

Rejection and likelihood-weighted sampling use evidence as state tuples:

```python
from pgmpy.factors.discrete import State

hard = [State("Disease", "present")]
conditional = sampler.rejection_sample(
    evidence=hard,
    size=100,
    seed=42,
    show_progress=False,
)
weighted = sampler.likelihood_weighted_sample(
    evidence=hard,
    size=100,
    seed=42,
    show_progress=False,
)
print(weighted["_weight"].head())
```

Use likelihood weighting instead of rejection sampling for unlikely evidence, and
keep the `_weight` column when estimating probabilities from the weighted sample.

Gibbs sampling from a Markov network or BN:

```python
from pgmpy.factors.discrete import State
from pgmpy.sampling import GibbsSampling

gibbs = GibbsSampling(model)
start = [State(var, 0) for var in model.nodes()]
chain = gibbs.sample(start_state=start, size=100, seed=42)
```

`GibbsSampling` start states use integer state ids. For named-state BNs, inspect
CPDs if you need to map names to ids.

## 7. Observational simulation

```python
samples = model.simulate(
    n_samples=100,
    evidence={"Test": "positive"},
    seed=42,
    show_progress=False,
)
```

This conditions generated samples on observed evidence. It is not an
intervention and should not be described as a causal effect.

## 8. Interventional simulation and causal routing

```python
interventional = model.simulate(
    n_samples=100,
    do={"Treatment": "treated"},
    seed=42,
    show_progress=False,
)
```

`do` fixes the intervened variable while generating data from the modified model.
Use this for synthetic-data generation from a fully specified causal BN. If the
user wants to identify `P(Y | do(X=x))` from a graph, choose an adjustment set,
or estimate an ATE from observed data, route to `causal-identification-and-effects`.
Do not replace `do` with `evidence`.

## 9. Virtual evidence and virtual intervention

Virtual evidence is encoded as a single-variable `TabularCPD` whose cardinality
and state names match the model variable:

```python
from pgmpy.factors.discrete import TabularCPD

soft_test = TabularCPD(
    variable="Test",
    variable_card=2,
    values=[[0.1], [0.9]],
    state_names={"Test": ["negative", "positive"]},
)
posterior = infer.query(
    variables=["Disease"],
    virtual_evidence=[soft_test],
    show_progress=False,
)
samples = model.simulate(
    n_samples=100,
    virtual_evidence=[soft_test],
    seed=42,
    show_progress=False,
)
```

Virtual interventions use the same CPD form but pass it as
`virtual_intervention=[...]` to `simulate(...)`.

## 10. Missingness simulation

```python
missing_test = TabularCPD(
    variable="Test*",
    variable_card=2,
    values=[[0.8, 0.6], [0.2, 0.4]],
    evidence=["Test"],
    evidence_card=[2],
    state_names={
        "Test*": [0, 1],
        "Test": ["negative", "positive"],
    },
)
with_missing = model.simulate(
    n_samples=100,
    missing_prob=missing_test,
    return_full=True,
    seed=42,
    show_progress=False,
)
```

The missingness CPD's variable must end with `*`; state `1` marks rows where the
base variable is masked to missing. `return_full=True` keeps the original values
in `<variable>_full` columns for debugging or evaluation.

## 11. Dynamic Bayesian Network exact inference

```python
from pgmpy.inference import DBNInference

assert dbn.check_model()
dbn.initialize_initial_state()
infer = DBNInference(dbn)
result = infer.query(
    variables=[("Y", 2)],
    evidence={("X", 0): 1, ("X", 1): 0},
)
print(result[("Y", 2)].values)
```

DBN variables, CPDs, evidence, and interventions use tuple nodes. Mixing string
nodes like `"Y_2"` with tuple nodes like `("Y", 2)` causes lookup errors.

## 12. DBN simulation formats

```python
wide = dbn.simulate(
    n_samples=5,
    n_time_slices=3,
    seed=42,
    show_progress=False,
    return_format="wide",
)
indexed = dbn.simulate(
    n_samples=5,
    n_time_slices=3,
    seed=42,
    show_progress=False,
    return_format="pd-multiindex",
)
```

Use `return_format="sorted"` when stable column ordering matters. Use
`"numpy3d"` only when downstream code expects an array with dimensions
`sample x variable x timestep`.
