---
name: supervised-and-tabular-models
description: "Routes numpy-ml tabular estimator, tree, nonparametric, and
  matrix-factorization tasks with fit/predict guidance and compatibility
  checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Supervised and Tabular Models

Use this sub-skill when a task asks how to use, inspect, or troubleshoot
`numpy-ml` estimators for small NumPy tabular problems:

- linear and generalized linear models;
- logistic regression and Gaussian naive Bayes;
- decision trees, random forests, and gradient-boosted decision trees;
- KNN, kernel regression, and Gaussian process regression;
- alternating least-squares and non-negative matrix factorization.

This package is an educational NumPy/SciPy implementation library, not a
scikit-learn replacement. Prefer small, explicit arrays and inspect learned
attributes when validating behavior.

## First Checks

1. Confirm the runtime uses the root skill compatibility guidance: Python 3.8
   is the verified legacy path, with `numpy<1.24` and SciPy installed.
2. Run the local helper when a task needs a quick estimator sanity check:

   ```bash
   python sub-skills/supervised-and-tabular-models/scripts/tabular_smoke.py
   ```

3. Read [`references/api-reference.md`](references/api-reference.md) before
   writing code that depends on constructor defaults, `fit`/`predict` methods,
   model attributes, or estimator-family differences.
4. Read [`references/workflows.md`](references/workflows.md) for copyable tiny
   examples and model-selection routes.
5. Read [`references/troubleshooting.md`](references/troubleshooting.md) when
   results contain `nan`, shapes do not match, `fit` returns `None`, class
   labels behave unexpectedly, or legacy dependency errors appear.

## Route by Task

| User asks for | Use this route |
| --- | --- |
| ordinary least squares, weighted/incremental least squares, ridge, Bayesian regression | Linear-model guidance in `api-reference.md` and `workflows.md`. |
| binary logistic regression, Gaussian naive Bayes, GLM links | Classification/GLM rows in `api-reference.md`; validate target shape and probability outputs. |
| CART, random forest, GBDT | Tree-family guidance; keep tiny data deterministic and set seeds where available. |
| KNN, Nadaraya-Watson kernel regression, Gaussian process regression | Nonparametric route; check metric/kernel object strings and prediction return shapes. |
| matrix factorization, ALS/NMF | Factorization route; inspect `.W` and `.H` after in-place `fit`. |
| feature standardization, one-hot encoding, tokenization, kernels, distances, graph helpers | Route to `../preprocessing-and-utilities/SKILL.md`. |
| neural-network layers, losses, optimizers, schedulers | Route to `../neural-network-components/SKILL.md`. |
| GMM/HMM/LDA/n-gram language models | Route to `../probabilistic-and-sequence-models/SKILL.md`. |

## Operating Notes

- Most estimator `fit` methods mutate the model and return `None`; keep the
  estimator object and inspect attributes such as `.beta`, `.parameters`,
  `.W`, `.H`, tree nodes, or trained kernel state.
- Methods are implemented for small educational experiments; avoid promising
  production-scale training, automatic validation, scikit-learn estimator
  protocol completeness, or GPU acceleration.
- Original repository tests compare some outputs against scikit-learn or other
  libraries, but those comparison packages are optional and are not runtime
  dependencies for this skill.
- If a workflow begins with raw text, labels, or feature dictionaries, first
  route preprocessing to `../preprocessing-and-utilities/SKILL.md`, then return
  here for estimator fitting.
