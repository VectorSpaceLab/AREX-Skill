# Modeling and Factor Troubleshooting

## Purpose

Use this matrix when pgmpy graph/model/factor construction fails or when a future task must decide whether to keep a causal graph as roles-only structure or upgrade it to a full probabilistic model.

## Quick diagnostic order

1. Confirm the object family: graph-only, discrete BN, linear Gaussian BN, functional BN, DBN, Markov/factor graph, or cluster/junction tree.
2. Print graph nodes/edges before adding CPDs/factors.
3. Print CPD/factor variables, cardinalities, and `state_names`.
4. Run the local smoke script to separate environment/import problems from task-specific model problems.
5. Call `check_model()` only after all required CPDs/factors are attached.

## Error and recovery matrix

| Symptom or error fragment | Likely cause | Recovery |
|---|---|---|
| `CPD defined on variable not in the model` | CPD child or one evidence variable is absent from the graph/model. | Add the missing node/edge before `add_cpds`, or correct spelling/case. For DBNs, use tuple nodes like `("X", 0)` consistently in edges and CPDs. |
| `Only TabularCPD can be added` | A discrete BN or DBN received a non-tabular CPD/factor. | Use `TabularCPD` or `NoisyORCPD` for `DiscreteBayesianNetwork`/`DynamicBayesianNetwork`. Use `LinearGaussianBayesianNetwork` for `LinearGaussianCPD`. |
| `Only LinearGaussianCPD can be added` | A linear Gaussian model received `TabularCPD` or another object. | Recreate the model as `DiscreteBayesianNetwork` for categorical variables, or use `LinearGaussianCPD` with `beta`/`std` for continuous variables. |
| `Only FunctionalCPD can be added to Functional Bayesian Network` | A functional BN received a tabular/linear factor. | Use `FunctionalCPD(variable, fn, parents=[...])` where `fn` returns a Pyro distribution, or choose a discrete/linear model instead. |
| `CPD associated with X doesn't have proper parents associated with it` | CPD evidence set differs from `model.get_parents("X")`. | Compare `set(cpd.variables[1:])` with `set(model.get_parents(node))`; recreate CPD with exactly the graph parents. If the graph is wrong, edit edges instead of hiding the mismatch in the CPD. |
| `values must be of shape ... Got shape ...` | `TabularCPD.values` does not have `(variable_card, product(evidence_card))`. | Compute the product of evidence cardinalities and reshape/rewrite the 2-D values table. Remember: root CPDs still need one column. |
| `Length of evidence_card doesn't match length of evidence` | The two parent lists differ in length. | Provide one cardinality per evidence variable in the same order, e.g. `evidence=["A", "B"]`, `evidence_card=[2, 3]`. |
| `Evidence card must be provided if Evidence is provided` | Evidence variables were provided without evidence cardinalities. | Add `evidence_card=[...]`, or remove `evidence` for a root CPD. |
| `Evidence must be list, tuple or array of strings` | A single string was passed as `evidence="A"`. | Use `evidence=["A"]`; for DBNs use `evidence=[("A", 0)]`. |
| `CPD values must be non-negative` | At least one CPD cell is negative. | Correct the probability table before adding to the model. |
| `Sum or integral of conditional probabilities for node X is not equal to 1` or `Sum of probabilities of states for node X is not equal to 1` | One or more CPD columns do not sum to 1 within tolerance. | Inspect `cpd.get_values().sum(axis=0)`. Normalize columns only if that matches the intended model; otherwise correct the source probabilities. |
| `No CPD associated with X` | The BN has a node with no CPD. | Add a root CPD for parentless nodes and child CPDs for all other nodes before `check_model()`. |
| `CPD for X doesn't have state names defined for all the variables` | `state_names` was provided but omits a child or evidence variable. | Include a key for every variable in `cpd.variables`, or omit `state_names` entirely to use numeric states. |
| `The cardinality of P doesn't match in it's child nodes` | Parent CPD cardinality differs from child `evidence_card`. | Recreate the child CPD with the parent's cardinality, or correct the parent CPD if it is wrong. |
| `The state names of P doesn't match in it's child nodes` | Parent and child CPDs use different state-name lists for the same variable. | Use the exact same list and order in every CPD that mentions the variable. |
| `state: 0 is an unknown for variable ...` after string state names | Evidence/query value uses numeric code but the CPD uses string labels. | Pass the state label (for example `"yes"`) or use numeric default states consistently across all CPDs. |
| `Cardinality is not defined for continuous variables` | `get_cardinality()` was called on a linear Gaussian model. | Use `LinearGaussianCPD.evidence`, `beta`, `std`, and continuous model methods instead of discrete cardinality. |
| `requires pytorch backend, currently it is set to numpy` | `FunctionalBayesianNetwork` was constructed before switching pgmpy's backend to torch. | Install torch/Pyro extras if needed, call `config.set_backend("torch", device="cpu" or "cuda")`, then construct the model. Reset to NumPy after optional work if mixing with core examples. |
| `requires package 'pyro-ppl' ... was not found` | `FunctionalCPD` or `FunctionalBayesianNetwork` optional dependency is missing. | Install `pgmpy[torch]` or `pyro-ppl` in an environment where optional functional models are explicitly required. Do not treat this as a core modeling failure. |
| `Current backend is numpy. Device can only be set for torch backend` | `config.set_device(...)` was called under NumPy backend. | Call `config.set_backend("torch", device=...)` first, or avoid device configuration for NumPy. |
| `Factors defined on variable not in the model` | Markov/factor graph factor mentions a variable node not present. | Add variable nodes before adding factors; for `FactorGraph`, also add the factor object as a graph node and connect it to variable nodes. |
| `Edges can only be between variables and factors` | Factor graph lost its bipartite structure. | Ensure edges connect variable nodes to `DiscreteFactor` nodes, never variable-variable or factor-factor. |
| `Factors for all the cliques or clusters not defined` | Cluster graph/junction tree has a clique node without an exact-scope factor. | Add one `DiscreteFactor` whose `scope()` equals the clique tuple/set for every clique. |
| `No sepset found between these two edges` | Cluster graph edge connects disjoint cliques. | Connect only clique nodes with a non-empty intersection. |
| Junction tree edge addition forms a cycle or tree not fully connected | Junction tree property violated. | Keep clique graph acyclic and connected; add/remove clique edges before factors if necessary. |

## CPD shape recovery recipe

```python
import math

cpd = model.get_cpds("Child")
parents = list(model.get_parents("Child"))
print("graph parents:", parents)
print("cpd variables:", cpd.variables)
print("cpd cardinality:", [int(c) for c in cpd.cardinality])
print("2-D values shape:", cpd.get_values().shape)

expected_width = math.prod(int(c) for c in cpd.cardinality[1:]) if len(cpd.cardinality) > 1 else 1
assert cpd.get_values().shape == (int(cpd.cardinality[0]), expected_width)
```

If the assertion fails, recreate the CPD from a 2-D table. If it passes but `check_model()` fails, inspect column sums and parent CPD consistency:

```python
values = cpd.get_values()
print("column sums:", values.sum(axis=0))
for parent in cpd.variables[1:]:
    parent_cpd = model.get_cpds(parent)
    print(parent, int(parent_cpd.cardinality[0]), parent_cpd.state_names.get(parent))
```

## Parent/evidence order mismatch recovery

`check_model()` compares parent/evidence sets, so it can pass even when the CPD values table is hard to audit because the evidence order is not the order you expected. Prefer recreating the CPD with a clear evidence order. For a quick inspection:

```python
# Inspect a non-mutating reordered table before deciding to recreate the CPD.
reordered_values = cpd.reorder_parents(new_order=["ParentB", "ParentA"], inplace=False)
print(reordered_values)
```

Use `cpd.variables[1:]` as the stored evidence order for table shape and code review. `cpd.get_evidence()` can expose pgmpy's internal reverse order.

## Choosing DAG roles vs a full model

Stay with a graph-only class when:

- The user asks for causal roles, allowed/forbidden directions, graph surgery, role validation, or causal diagrams.
- No probabilities, CPDs, posterior distributions, simulations, predictions, or learned parameters are required.
- You need `PDAG`, `ADMG`, or `MAG` edge semantics that are not a standard directed BN.

Upgrade to a full model when:

- The user needs `check_model()` over CPDs/factors.
- The task says Bayesian network, Markov network, CPD, factor, inference, simulation, prediction, fit, save/load, or model validation.
- The graph has to carry probabilities or continuous CPDs, not just roles and edges.

If the next step is causal identification/effect estimation, build a role-aware graph/model here and then route to `causal-identification-and-effects`.

## Optional functional-model limits

Functional BNs were not installed or native-tested in the minimum core environment. Treat these as optional requirements:

- Package extras: `pgmpy[torch]` or equivalent torch plus `pyro-ppl`.
- Backend: `from pgmpy.global_vars import config; config.set_backend("torch", device="cpu")` before constructing functional objects.
- CPD functions: return Pyro distributions and accept parent-value dictionaries (or vectorized parent data if `vectorized=True`).
- Device/dtype: when creating tensors in CPD functions, use `config.get_dtype()` and `config.get_device()` to avoid dtype/device mismatches.

If torch/Pyro are not available and the user did not explicitly require functional models, choose a discrete or linear Gaussian model instead and record the limitation.
