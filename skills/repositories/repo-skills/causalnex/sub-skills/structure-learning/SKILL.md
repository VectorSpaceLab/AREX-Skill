---
name: structure-learning
description: "Learn causal graph structure with NOTEARS, DYNOTEARS, and the
  sklearn DAG wrappers, and debug numeric-data and convergence failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Structure Learning

Use this sub-skill when you want to learn a causal graph from data, tune NOTEARS/DYNOTEARS, or use the sklearn-style `DAGClassifier` and `DAGRegressor` wrappers.

## Route here when

- The request names `from_pandas`, `from_numpy`, `from_pandas_dynamic`, `NOTEARS`, `DYNOTEARS`, `DAGClassifier`, `DAGRegressor`, or `NotearsMLP`.
- You need to convert numeric tabular data into a `StructureModel`.
- You need to learn a dynamic causal graph from lagged time-series data.
- You need a sklearn-style wrapper that returns feature importances or graph plots.

## Route elsewhere when

- You already have the DAG and need CPDs, inference, intervention, metrics, or EM -> `../bayesian-networks/SKILL.md`.
- You need feature discretization before BN fitting -> `../discretization/SKILL.md`.
- You need synthetic DAGs or toy time-series data -> `../synthetic-data/SKILL.md`.

## Start fast

1. Read `references/api-reference.md` for the verified constructors and key parameters.
2. Read `references/workflows.md` for the shortest tabular, dynamic, and sklearn wrapper recipes.
3. Run `../../scripts/smoke_structure_learning.py` after install changes or API edits.
4. Read `references/troubleshooting.md` if the learner rejects your data or fails to converge.

## Notes

- `use_gpu=True` is only a preference for PyTorch NOTEARS; the implementation falls back to CPU when CUDA is unavailable.
- The legacy `causalnex.structure.notears` functions do not take `use_gpu`; use the PyTorch module or wrapper `notears_mlp_kwargs` for device controls.
- `from_pandas` and `from_numpy` expect numeric input and reject NaN or infinity.
- `StructureModel` allows cycles, but the learned Bayesian-network path does not.
