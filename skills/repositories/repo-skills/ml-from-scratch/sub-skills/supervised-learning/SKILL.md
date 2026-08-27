---
name: supervised-learning
description: "Select, fit, predict, and debug ML-From-Scratch supervised
  learning estimators."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Supervised Learning

Use this sub-skill when a task involves `mlfromscratch.supervised_learning` estimators for classical supervised prediction: regression, binary or multiclass classification, trees, ensembles, SVMs, Naive Bayes, LDA, boosting, XGBoost, Perceptron, Neuroevolution, or `ParticleSwarmOptimizedNN`.

## Route here when

- Choosing a repo estimator for tabular regression or classification.
- Translating a small supervised workflow into `fit`, `predict`, or `transform` calls.
- Debugging feature shape, label encoding, convergence, `cvxopt`, or headless plotting issues in supervised workflows.
- Checking a quick plot-free regression or classification smoke script bundled with this sub-skill.

## Route elsewhere

- Clustering, PCA-only analysis, association rules, genetic algorithms, RBM, or other unsupervised/generative tasks: use `../unsupervised-learning/`.
- Neural-network layer stacks, losses, optimizers, CNN/RNN/MLP construction internals, autoencoders, or GANs: use `../deep-learning/`.
- Gym CartPole, DQN training/play, replay memory, or Gym API compatibility: use `../reinforcement-learning/`.
- Package-wide install/import checks and dependency provenance: use the root references such as `../../references/package-overview.md` and `../../references/troubleshooting.md` when they are present.

## Fast operating path

1. Identify the task family:
   - Regression: start with `LinearRegression`, `PolynomialRegression`, `RidgeRegression`, `LassoRegression`, `PolynomialRidgeRegression`, `ElasticNet`, `RegressionTree`, or `GradientBoostingRegressor`.
   - Binary classification: start with `LogisticRegression`, `SupportVectorMachine`, `Adaboost`, `LDA`, `NaiveBayes`, `KNN`, or a tree/ensemble.
   - Multiclass classification: start with `KNN`, `ClassificationTree`, `RandomForest`, `NaiveBayes`, `GradientBoostingClassifier`, `XGBoost`, `MultiClassLDA` for projection, or one-hot neural classifiers.
2. Read `references/model-catalog.md` for constructors, method signatures, and label conventions. Do not assume scikit-learn estimator APIs.
3. Read `references/workflows.md` for concise regression and classification recipes, including 2-D feature shaping and label conversions.
4. If the workflow fails, use `references/troubleshooting.md` before changing models. Most failures are shape, label, dependency, NumPy compatibility, or convergence issues.
5. For a quick runtime check, run one of the bundled helpers:
   - `python scripts/run_regression_smoke.py --help`
   - `python scripts/run_regression_smoke.py --model linear-gd`
   - `python scripts/run_classification_smoke.py --help`
   - `python scripts/run_classification_smoke.py --model all-fast`

## Key cautions

- `X` should be a 2-D numeric array of shape `(n_samples, n_features)`. Convert a 1-D feature vector with `np.asarray(x).reshape(-1, 1)`.
- Label conventions differ by estimator: SVM and Adaboost expect `{-1, 1}` for binary tasks; LogisticRegression expects `0/1`; tree/KNN/NaiveBayes/boosting models use nominal integer labels; Perceptron and neural optimization wrappers expect one-hot targets from `to_categorical`.
- `KNN` has no `fit` method; call `predict(X_test, X_train, y_train)`.
- `SupportVectorMachine` depends on `cvxopt`; because the supervised package exports SVM at import time, missing `cvxopt` can also break package-level supervised imports.
- Tree, random forest, gradient boosting, and XGBoost workflows rely on the package's `divide_on_feature` helper and may need the NumPy-compatibility troubleshooting path in current environments.
