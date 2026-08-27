# Package overview

## What this package provides

ML-From-Scratch is an educational Python package named `mlfromscratch`. It implements many classical machine-learning algorithms, neural-network building blocks, and a compact DQN loop with NumPy-first code intended for transparency rather than production speed.

Use this skill when a future task needs package-specific constructors, label conventions, input shapes, dependency fixes, or small smoke checks for `mlfromscratch` workflows.

## Runtime import families

| Family | Import path | Owned by |
| --- | --- | --- |
| Supervised estimators | `mlfromscratch.supervised_learning` | `sub-skills/supervised-learning/` |
| Unsupervised algorithms | `mlfromscratch.unsupervised_learning` | `sub-skills/unsupervised-learning/` |
| Neural-network framework | `mlfromscratch.deep_learning` | `sub-skills/deep-learning/` |
| DQN loop | `mlfromscratch.reinforcement_learning` | `sub-skills/reinforcement-learning/` |
| Preprocessing, metrics, kernels, plotting helpers | `mlfromscratch.utils` | `references/shared-utilities.md` and relevant sub-skills |

There are no console-script entry points. Operate the package through Python imports and bundled helper scripts.

## Dependency baseline

The inspected package metadata reports `mlfromscratch==0.0.4` and a legacy runtime dependency list: Matplotlib, NumPy, `sklearn`, pandas, cvxopt, SciPy, progressbar33, terminaltables, and gym.

Practical install notes:

- Install the real `scikit-learn` distribution even if legacy metadata names the deprecated `sklearn` shim.
- Install `cvxopt` if importing `mlfromscratch.supervised_learning` at package level or using `SupportVectorMachine`.
- Use `gym==0.25.x` with NumPy `<2` for the package's DQN path, or adapt newer Gym reset/step APIs and NumPy bool aliases in a local wrapper.
- Use a headless Matplotlib backend for automated work: set `MPLBACKEND=Agg` before importing plotting code.
- CPU is sufficient for every selected workflow in this skill. No CUDA/ROCm/MPS backend is required or claimed.

## High-level capabilities

### Supervised learning

Use `sub-skills/supervised-learning/` for:

- Regression: linear, polynomial, ridge, lasso, elastic-net, regression trees, gradient boosting.
- Classification: logistic regression, KNN, Naive Bayes, LDA, trees, random forests, SVM, Adaboost, gradient boosting, XGBoost.
- Optimization-driven neural classifiers: Perceptron, Neuroevolution, particle-swarm optimized neural networks.
- Label encoding choices and estimator-specific `fit`/`predict` signatures.

### Unsupervised learning

Use `sub-skills/unsupervised-learning/` for:

- Dimensionality reduction with PCA.
- Clustering with KMeans, DBSCAN, PAM, and Gaussian mixtures.
- Association mining with Apriori and FPGrowth.
- Toy genetic search and RBM reconstruction.

### Deep learning

Use `sub-skills/deep-learning/` for:

- `NeuralNetwork` construction.
- Layers such as `Dense`, `Conv2D`, `RNN`, pooling, flattening, dropout, activation, batch normalization, reshape, and upsampling.
- Optimizers, losses, activations, target encoding, and shape debugging.
- MLP/CNN/RNN and advanced model-builder patterns.

### Reinforcement learning

Use `sub-skills/reinforcement-learning/` for:

- `DeepQNetwork` with CartPole-style Gym environments.
- Model-builder callbacks using the deep-learning framework.
- Replay memory, epsilon decay, one-epoch smoke checks, render/play caveats, and Gym API compatibility.

## Safe validation pattern

1. Run `scripts/check_install.py` from the root skill directory to verify imports and dependency versions.
2. Run the focused sub-skill smoke that matches the workflow family.
3. If the smoke passes but the user workflow fails, use the nearest troubleshooting reference before changing algorithm families.
4. Keep smoke settings small: one epoch, tiny arrays, no plotting, no network access, and no display/render calls.

## Known package caveats

- The package is educational and old-style. It does not follow all scikit-learn conventions.
- Some algorithms are stochastic; set `numpy.random.seed(...)` before model construction when reproducibility matters.
- Some tree-family code can expose current NumPy compatibility issues around heterogeneous split partitions; see the supervised troubleshooting reference.
- Some examples are long-running or plotting-heavy. Prefer the bundled helpers for automated verification.
