---
name: ml-from-scratch
description: "Route ML-From-Scratch educational supervised, unsupervised,
  deep-learning, and DQN workflows with install, utilities, and troubleshooting
  guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ML-From-Scratch

Use this repo skill when a task involves the `mlfromscratch` package: educational Python implementations of supervised models, unsupervised algorithms, a small neural-network framework, and a CartPole Deep Q-Network workflow.

The skill is self-contained. Do not send future agents to the original repository examples or docs at runtime. Use the bundled references and scripts here, plus the installed `mlfromscratch` package in the user's environment.

## Start here

1. Identify the workflow family from the user request, package import path, model name, error message, or data type.
2. If package health is uncertain, run `python scripts/check_install.py --help` or `python scripts/check_install.py --include-rl` from this skill directory.
3. Route to the nearest sub-skill for workflow depth; keep this root file for package-wide install, utility, and troubleshooting context.
4. Prefer bundled smoke scripts over long plotted demonstrations when validating behavior in a headless agent session.

## Route map

| Request signal | Read first |
| --- | --- |
| Regression, binary/multiclass classification, trees, ensembles, SVM, Naive Bayes, LDA, KNN, Adaboost, XGBoost, Perceptron, Neuroevolution, ParticleSwarmOptimizedNN | `sub-skills/supervised-learning/SKILL.md` |
| PCA, KMeans, DBSCAN, PAM, GaussianMixtureModel, Apriori, FPGrowth, GeneticAlgorithm, RBM reconstruction, transaction itemsets/rules, clustering diagnostics | `sub-skills/unsupervised-learning/SKILL.md` |
| `NeuralNetwork`, `Dense`, `Conv2D`, `RNN`, activations, losses, optimizers, MLP/CNN/RNN assembly, autoencoder/GAN/DCGAN model-building patterns | `sub-skills/deep-learning/SKILL.md` |
| `DeepQNetwork`, CartPole, Gym reset/step errors, replay memory, epsilon decay, DQN model-builder callback, render/play behavior | `sub-skills/reinforcement-learning/SKILL.md` |
| `normalize`, `standardize`, `train_test_split`, `to_categorical`, metrics, plotting helpers, data utility behavior | `references/shared-utilities.md` |
| Install/import failures, dependency pins, `sklearn` shim, `cvxopt`, Gym/NumPy drift, headless plotting | `references/troubleshooting.md` |
| Package layout, dependency map, sub-skill ownership, example coverage overview | `references/package-overview.md` and `references/workflow-map.md` |

## Install baseline

For a CPU-oriented public package environment, pin the legacy compatibility pair and install the real scikit-learn distribution before the package:

```bash
python -m pip install "numpy<2" "gym==0.25.2" scikit-learn cvxopt progressbar33 terminaltables matplotlib pandas scipy
python -m pip install mlfromscratch
```

If installing from a local package checkout, replace the final package argument with the checkout's editable install command. Then run `python scripts/check_install.py`; add `--include-rl` when CartPole/DQN is part of the task.

## Package-wide operating facts

- Distribution/import name: `mlfromscratch`, version `0.0.4` in the inspected source.
- There are no package CLI entry points; use Python imports and bundled smoke scripts.
- Most workflows are CPU-only and educational. Do not claim production-grade speed or benchmark performance.
- Several APIs intentionally differ from scikit-learn: for example `KNN` predicts with `predict(X_test, X_train, y_train)`, and many unsupervised classes expose `predict` or `transform` without a separate `fit`.
- Dependency quirks matter: install the real `scikit-learn` distribution even though legacy metadata names `sklearn`; use `gym==0.25.x` with NumPy `<2` for the DQN path unless a compatibility wrapper is applied.
- Plotting examples should run headless by setting `MPLBACKEND=Agg` before importing Matplotlib, or by using bundled non-plotting smokes.

## Bundled checks

From this root directory:

```bash
python scripts/check_install.py
python scripts/check_install.py --include-rl
```

Sub-skill smoke helpers include:

- `sub-skills/supervised-learning/scripts/run_regression_smoke.py`
- `sub-skills/supervised-learning/scripts/run_classification_smoke.py`
- `sub-skills/unsupervised-learning/scripts/run_clustering_smoke.py`
- `sub-skills/unsupervised-learning/scripts/run_association_smoke.py`
- `sub-skills/unsupervised-learning/scripts/run_optimization_smoke.py`
- `sub-skills/deep-learning/scripts/run_mlp_smoke.py`
- `sub-skills/deep-learning/scripts/run_cnn_smoke.py`
- `sub-skills/reinforcement-learning/scripts/run_dqn_smoke.py`

These helpers are small validation and adaptation patterns, not replacements for full experiments.

## Avoid using this skill when

- The user is asking for scikit-learn, PyTorch, TensorFlow, Gymnasium, Stable-Baselines3, or another package's own API rather than ML-From-Scratch.
- The task needs production training infrastructure, GPU acceleration, model serving, checkpointing, distributed execution, or benchmark-quality results.
- The user needs general ML theory without package-specific code, unless package names or error messages clearly point back to `mlfromscratch`.

## Provenance and refresh

Read `references/repo-provenance.md` when deciding whether this skill may be stale. If the source package version, public API, dependency pins, or example behavior changed, refresh the repo skill before relying on details that may have drifted.
