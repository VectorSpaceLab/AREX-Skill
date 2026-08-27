# Inference, Sampling, and Simulation Troubleshooting

Start with the model, not the algorithm. Most pgmpy inference and simulation
failures are invalid-model or state-name problems.

## Quick diagnostic checklist

```python
from pgmpy.global_vars import config

config.set_show_progress(False)
print(list(model.nodes()))
print(model.get_cpds())
print(model.check_model())
for cpd in model.get_cpds():
    print(cpd.variable, cpd.state_names)
```

For non-BN factor models, inspect attached factors and their scopes instead of
CPDs.

## Common failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `check_model()` raises before inference or simulation | Missing CPD, CPD cardinality mismatch, CPD evidence order/table shape mismatch, or CPD state names inconsistent with parent variables | Rebuild the CPDs in the modeling sub-skill; do not query a partially parameterized BN. For a child with parents, the CPD columns must enumerate parent-state combinations in the declared `evidence` order. |
| `ValueError` about the same variable appearing in `variables` and `evidence` | Query variable overlaps evidence | Remove that variable from `variables` if it is observed, or remove it from `evidence` if you need its posterior. `P(X | X=x)` is degenerate and not accepted by these query APIs. |
| `ValueError`, `KeyError`, or node lookup error for evidence | Evidence key is not a model variable, or DBN evidence used the wrong node convention | Compare `evidence.keys()` with `model.nodes()`. For DBNs, use tuple keys like `("Y", 2)`, not strings such as `"Y_2"`. |
| `KeyError` or `ValueError` for an evidence state | State value does not match CPD state names | Inspect `model.get_cpds(var).state_names`. Use exactly the stored labels, including case and type, e.g. `"positive"` instead of `1` when named states were declared. |
| Posterior shape is surprising | `joint=True` returns one joint factor; `joint=False` returns separate marginal factors | Decide whether downstream code expects a single factor over all query variables or a dictionary keyed by variable. Check `factor.variables`, `factor.cardinality`, `factor.values.shape`, and `factor.state_names`. |
| Exact inference is very slow or memory-heavy | Large induced width, high cardinality variables, broad joint query, or insufficient evidence | Try a smaller query, set more observed evidence, try another elimination order, inspect `induced_width(order)`, use `BeliefPropagation` for repeated junction-tree queries, or switch to `ApproxInference` if approximate answers are acceptable. |
| Approximate results vary across runs | Sampling randomness or too few samples | Pass `seed=...`, increase `n_samples`, pass explicit `state_names`, and compare only within a tolerance. Do not expect exact equality with `VariableElimination`. |
| Progress bars clutter logs or tests | Default progress display is enabled | Pass `show_progress=False` on query/simulation/sampling calls and call `config.set_show_progress(False)` at script startup. |
| `simulate(..., evidence=...)` and `simulate(..., do=...)` give different results | Evidence conditions; `do` intervenes by modifying incoming edges for the fixed variables | Preserve the distinction. Use `evidence` for observations and `do` for synthetic interventional data. Route causal-effect identification or ATE requests to the causal sub-skill. |
| Error that a variable cannot be in both `do` and `evidence` | Same variable supplied in both simulation dictionaries | Choose either observed conditioning or hard intervention for that variable. |
| Virtual evidence cardinality error | `TabularCPD` used for `virtual_evidence` does not match target variable cardinality or state names, or has extra evidence variables | Create a single-variable CPD with the same cardinality/state names as the model variable. Soft interventions go to `virtual_intervention`, not multi-parent virtual evidence. |
| Missingness simulation error requiring `*` | `missing_prob` CPD variable does not end with `*`, target base variable is absent, or first cardinality is not 2 | Name the missing indicator like `"X*"`, use state names compatible with `X`, and provide two missing-indicator states where state `1` marks missing. |
| `partial_samples` shape or column issues | Supplied partial DataFrame row count or columns do not match the simulation call | Ensure `partial_samples.shape[0] == n_samples` and columns are valid model variables with valid state values. |
| Rejection sampling appears stuck | Evidence has low probability, so many forward samples are rejected | Use likelihood-weighted sampling or model-level `simulate(..., evidence=...)` with a small fixture first; consider approximate or exact inference for probabilities instead of conditional sample generation. |
| Gibbs sampling start-state error or unexpected labels | `GibbsSampling` start states use variable names and integer state ids | Provide `State(var, state_id)` for every variable or let the sampler choose a random start state. Map named states to ids through CPDs when necessary. |
| DBN inference error after adding CPDs | Initial-state or transition CPDs are incomplete, or `initialize_initial_state()` was not called | Add CPDs for slice 0 and the transition slice, then call `initialize_initial_state()` before `DBNInference` or DBN simulation. |
| Optional functional-model inference/simulation import fails | `torch`/`pyro-ppl` extra is not installed | Treat functional Bayesian networks as optional. Install and verify the `torch` extra only when the user's task actually requires that model family. |

## Recovery pattern for invalid evidence/state names

```python
variables = set(model.nodes())
evidence = {"Test": "positive"}
unknown = set(evidence) - variables
if unknown:
    raise ValueError(f"Evidence variables not in model: {sorted(unknown)}")

for var, state in evidence.items():
    states = model.get_cpds(var).state_names.get(var)
    if states is not None and state not in states:
        raise ValueError(f"Invalid state {state!r} for {var}; valid states are {states}")
```

Use this preflight check in scripts that receive variable names or states from a
user interface.

## Result-shape checks

For `query(joint=True)`:

```python
factor = infer.query(["A", "B"], show_progress=False)
assert set(factor.variables) == {"A", "B"}
assert abs(float(factor.values.sum()) - 1.0) < 1e-8
```

For `query(joint=False)`:

```python
marginals = infer.query(["A", "B"], joint=False, show_progress=False)
assert set(marginals) == {"A", "B"}
for var, factor in marginals.items():
    assert factor.variables == [var]
```

For `simulate(...)`:

```python
samples = model.simulate(n_samples=5, seed=42, show_progress=False)
assert samples.shape[0] == 5
assert set(samples.columns).issuperset(set(model.nodes()) - set(model.latents))
```

For `DBNInference`:

```python
result = infer.query([("Y", 2)], evidence={("X", 0): 1})
assert ("Y", 2) in result
assert abs(float(result[("Y", 2)].values.sum()) - 1.0) < 1e-8
```
