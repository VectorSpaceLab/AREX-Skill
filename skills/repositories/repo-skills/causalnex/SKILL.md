---
name: causalnex
description: "Use CausalNex to learn causal structures, fit Bayesian networks,
  discretize features, generate synthetic graph data, and run inference,
  evaluation, and latent-variable workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# CausalNex

Use this skill when the task names CausalNex, NOTEARS, DYNOTEARS, `BayesianNetwork`, `InferenceEngine`, `Discretiser`, `DAGClassifier`, `DAGRegressor`, `BayesianNetworkClassifier`, causal DAG learning, or Bayesian-network workflows from this package.

## Route by task

- Structure learning from tabular or time-series data -> `sub-skills/structure-learning/SKILL.md`
- Bayesian-network fitting, inference, metrics, plots, and latent-variable EM -> `sub-skills/bayesian-networks/SKILL.md`
- Discretizing continuous features, including tree-based or MDLP splits -> `sub-skills/discretization/SKILL.md`
- Synthetic DAG/data generation, dynamic transforms, and categorical mapping -> `sub-skills/synthetic-data/SKILL.md`
- Contrib-area or contribution-layout questions -> `references/contribution-mirror.md`

## Fast start

1. Install the package with `pip install causalnex`.
2. If you need the optional discretizer extras, install `pip install "causalnex[all]"` or `pip install mdlp-discretization~=0.3.3`.
3. Run `scripts/check_install.py` to confirm the core imports and optional backend availability.
4. Read `references/installation.md` for supported Python and dependency notes.
5. Read `references/api-reference.md` when you need verified public constructors, signatures, and return-shape notes.
6. Read `references/workflows.md` for the shortest path into each workflow.
7. Read `references/contribution-mirror.md` only when the user asks about `causalnex.contrib` or contribution layout.
8. Read `references/troubleshooting.md` when imports, optional dependencies, or data-shape checks fail.
9. Read `references/repo-provenance.md` when you need to compare this skill with the current source revision.

## Shared scripts

- `scripts/check_install.py` verifies the public package imports, `torch` availability, and the optional MDLP dependency.
- `scripts/smoke_structure_learning.py` exercises `from_pandas`, `from_numpy`, `from_pandas_dynamic`, `DAGClassifier`, and `DAGRegressor` on tiny inputs.
- `scripts/smoke_bayesian_network.py` fits a tiny Bayesian network, queries marginals, evaluates metrics, and optionally exercises latent-variable EM.
- `scripts/smoke_discretizer.py` exercises the fixed, uniform, quantile, outlier, percentiles, tree, and MDLP discretizers.
- `scripts/smoke_synthetic_data.py` exercises the DAG/data generators, dynamic transforms, and categorical mapping helpers.

## References

- `references/installation.md`
- `references/api-reference.md`
- `references/workflows.md`
- `references/contribution-mirror.md`
- `references/troubleshooting.md`
- `references/repo-provenance.md`
- `references/repo-routing-metadata.json`

## Avoid

- Do not assume CUDA is required; `use_gpu=True` falls back to CPU when CUDA is unavailable.
- Do not assume `mdlp-discretization` is installed unless you asked for the optional discretizer path.
- Do not rely on the original repository checkout; this skill should stand on its bundled references and scripts.
