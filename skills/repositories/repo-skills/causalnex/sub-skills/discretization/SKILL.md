---
name: discretization
description: "Discretize continuous features with unsupervised, tree-based, or
  MDLP splitters before Bayesian-network fitting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Discretization

Use this sub-skill when you need to bucket numeric data, prepare features for a Bayesian network, or debug tree-based and MDLP splitters.

## Route here when

- The task names `Discretiser`, `DecisionTreeSupervisedDiscretiserMethod`, or `MDLPSupervisedDiscretiserMethod`.
- You need fixed, uniform, quantile, outlier, or percentile bucketization.
- You need supervised split thresholds from a decision tree or MDLP.
- You need to discretize features before fitting `BayesianNetworkClassifier` or another BN workflow.

## Route elsewhere when

- You need the fitted BN itself -> `../bayesian-networks/SKILL.md`.
- You need the causal DAG learner -> `../structure-learning/SKILL.md`.
- You need synthetic data or feature mapping helpers -> `../synthetic-data/SKILL.md`.

## Start fast

1. Read `references/api-reference.md` for the exact constructor and split-method behavior.
2. Read `references/workflows.md` for the quickest unsupervised, tree-based, MDLP, and BN-classifier examples.
3. Run `../../scripts/smoke_discretizer.py` when install issues or binning behavior look suspicious.
4. Read `references/troubleshooting.md` for method-selection, split-point, and optional-dependency failures.
