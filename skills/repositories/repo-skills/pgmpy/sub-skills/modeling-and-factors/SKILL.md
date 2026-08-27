---
name: modeling-and-factors
description: "Builds and validates pgmpy graph, model, CPD, factor, and backend
  objects for causal and probabilistic graphical models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Modeling and Factors

Use this sub-skill when the task is to construct, validate, inspect, or debug pgmpy graph/model/factor objects before learning, inference, simulation, causal effects, or file I/O.

## Route here

- Build graph-only objects: `DAG`, `PDAG`, `MAG`, `ADMG`, `SimpleCausalModel`, and `UndirectedGraph`, including causal roles such as exposures, outcomes, latents, confounders, mediators, and instruments.
- Build probabilistic model containers: `DiscreteBayesianNetwork`, `LinearGaussianBayesianNetwork`, `FunctionalBayesianNetwork`, `DynamicBayesianNetwork`, `DiscreteMarkovNetwork`, `FactorGraph`, `JunctionTree`, `ClusterGraph`, and `MarkovChain`.
- Define and validate CPDs/factors: `TabularCPD`, `LinearGaussianCPD`, `FunctionalCPD`, `DiscreteFactor`, `JointProbabilityDistribution`, and `NoisyORCPD`.
- Diagnose `add_cpds`, `get_cpds`, `get_factors`, `check_model`, cardinality, state-name, evidence-order, graph-role, factor-scope, and backend-configuration errors.

## Reroute elsewhere

- Parameter fitting, structure learning, CI tests, and scores: route to `learning-structure-and-parameters`.
- Posterior queries, MAP, simulation, and sampling beyond a tiny validation smoke: route to `inference-sampling-and-simulation`.
- Adjustment/frontdoor identification, do-calculus, ATE, IV, and effect-regressor workflows: route to `causal-identification-and-effects`.
- Model serialization formats, datasets/example models, graph metrics, and evaluation: route to `data-io-and-evaluation`.
- Adding or modifying pgmpy source APIs/templates: route to `extending-pgmpy`.

## Read next

- [Model and factor API reference](references/model-and-factor-api.md) for class-selection tables, CPD/factor shape rules, role methods, backend config, and validation semantics.
- [Modeling workflows](references/modeling-workflows.md) for self-contained recipes adapted from pgmpy's discrete BN, linear Gaussian BN, CPD, dynamic BN, functional BN, and factor-graph examples.
- [Troubleshooting](references/troubleshooting.md) for `check_model()` failures, CPD evidence/cardinality mismatches, state-name confusion, optional torch/Pyro errors, and graph-only-vs-model decisions.
- [Smoke script](scripts/check_modeling_smoke.py) to verify that an installed pgmpy package can build and validate a tiny discrete BN from any working directory.

## Minimal operating checklist

1. Choose the lightest object that matches the task: graph-only roles if no CPDs are needed; a BN/Markov/factor container if parameters are needed; a dynamic or functional model only when its extra structure is essential.
2. Add all nodes/edges before adding CPDs or factors. CPD/factor variables must already exist in the graph/model.
3. For `TabularCPD`, make `values` a 2-D array with shape `(variable_card, product(evidence_card))`; every column is a conditional distribution and must sum to 1 before `check_model()` passes.
4. Keep parent/evidence names, cardinalities, and `state_names` consistent across parent CPDs and child CPDs. Use the same labels in inference/evidence later.
5. Call `model.check_model()` before handing the model to learning, inference, simulation, causal, or I/O workflows.
6. Treat `FunctionalBayesianNetwork` and `FunctionalCPD` as optional: they require the torch backend plus `pyro-ppl`; they were not installed in the minimum CPU environment used for the core skill.

## Safe validation command

From any directory with pgmpy installed, run:

```bash
python path/to/check_modeling_smoke.py
```

The script builds a tiny discrete Bayesian network, validates CPDs, runs one small exact query as a smoke check, and reports whether optional torch/Pyro packages are importable without requiring them.
