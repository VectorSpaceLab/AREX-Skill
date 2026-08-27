---
name: synthetic-data
description: "Generate synthetic DAGs, tabular samples, dynamic time-series
  samples, and feature-mapping helpers for CausalNex experiments."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Synthetic Data

Use this sub-skill when you need toy DAGs, synthetic tabular data, dynamic time-series samples, or helpers that reshape categorical and lagged inputs for causal workflows.

## Route here when

- The task names `generate_structure`, `sem_generator`, `nonlinear_sem_generator`, `generate_continuous_dataframe`, `generate_binary_dataframe`, `generate_count_dataframe`, `generate_categorical_dataframe`, `generate_structure_dynamic`, `generate_dataframe_dynamic`, `gen_stationary_dyn_net_and_df`, `DynamicDataTransformer`, or `VariableFeatureMapper`.
- You need synthetic benchmarks or fixtures for another CausalNex workflow.
- You need dynamic lagged matrices or categorical feature expansion.

## Route elsewhere when

- You want to fit or query a Bayesian network -> `../bayesian-networks/SKILL.md`.
- You want to learn a graph from generated data -> `../structure-learning/SKILL.md`.
- You need to discretize a feature before using generated data -> `../discretization/SKILL.md`.

## Start fast

1. Read `references/api-reference.md` for the generator and transform signatures.
2. Read `references/workflows.md` for static DAGs, dynamic DAGs, lagged transforms, and schema helpers.
3. Run `../../scripts/smoke_synthetic_data.py` when you need a quick end-to-end fixture check.
4. Read `references/troubleshooting.md` when a generator rejects the graph or the transformer rejects the input layout.
