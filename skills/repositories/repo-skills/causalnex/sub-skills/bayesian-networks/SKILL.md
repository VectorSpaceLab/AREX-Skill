---
name: bayesian-networks
description: "Fit Bayesian networks, query marginals, intervene, evaluate
  predictions, plot structures, and run latent-variable EM."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Bayesian Networks

Use this sub-skill when the graph already exists and you want CPDs, inference, interventions, evaluation metrics, plotting, or latent-variable EM.

## Route here when

- The request names `BayesianNetwork`, `InferenceEngine`, `roc_auc`, `classification_report`, `plot_structure`, `display_plot_ipython`, `EMSingleLatentVariable`, or `BayesianNetworkClassifier`.
- You need to fit CPDs on a known DAG.
- You need causal queries or do-calculus interventions.
- You need a Bayesian-network classifier or latent-variable estimation.

## Route elsewhere when

- You still need to learn the DAG -> `../structure-learning/SKILL.md`.
- You need to discretize inputs before fitting a BN -> `../discretization/SKILL.md`.
- You need synthetic fixtures or dynamic toy data -> `../synthetic-data/SKILL.md`.

## Start fast

1. Read `references/api-reference.md` for the BN constructors and query methods.
2. Read `references/workflows.md` for fitting, inference, evaluation, plotting, and EM recipes.
3. Run `../../scripts/smoke_bayesian_network.py` after environment changes or when a query path breaks.
4. Read `references/troubleshooting.md` for CPD, node-name, and intervention failures.
