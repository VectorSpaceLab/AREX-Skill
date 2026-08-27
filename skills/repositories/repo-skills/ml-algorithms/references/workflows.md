# MLAlgorithms route-level workflows

## Purpose

Use this reference when a user request spans multiple algorithm families or when you need to decide which sub-skill and helper script to read first.

## Workflow router

| User request | Read first | Then use |
| --- | --- | --- |
| Fit/predict a tabular classifier or regressor | `sub-skills/classical-estimators/SKILL.md` | `references/workflows.md` in that sub-skill and `run_classical_smoke.py` |
| Compare SVM, random forest, gradient boosting, KNN, or logistic regression | `sub-skills/classical-estimators/SKILL.md` | Classical API reference and troubleshooting |
| Cluster samples or compare KMeans/GMM | `sub-skills/unsupervised-and-reduction/SKILL.md` | Unsupervised smoke helper |
| Reduce dimensions or visualize embeddings | `sub-skills/unsupervised-and-reduction/SKILL.md` | PCA/t-SNE workflow notes |
| Build a small MLP/CNN/RNN/LSTM with the custom stack | `sub-skills/neural-network-building-blocks/SKILL.md` | Neural API/workflow references |
| Use CartPole DQN | `sub-skills/neural-network-building-blocks/references/rl-dqn.md` | DQN-init smoke before training |
| Diagnose package install/import issues | root `references/troubleshooting.md` | `scripts/run_import_smoke.py` |
| Use metrics or utility functions | root `references/api-reference.md` | Owning estimator sub-skill if part of a model workflow |

## Typical task flow

1. Start with the user's target output: hard labels, probabilities, continuous values, clusters, embeddings, neural outputs, or RL actions.
2. Read the matching sub-skill route and one reference file. Avoid loading all sub-skills unless the task spans families.
3. Run the closest bundled smoke script against the active environment before adapting larger workflows.
4. When a source example seems relevant, use the bundled skill script or distilled recipe rather than opening/running original example files.
5. Keep native tests/examples for verification of a checkout, not as runtime dependencies of the skill.

## Cross-family patterns

### PCA before a supervised estimator

Use `unsupervised-and-reduction` to fit PCA on the training split, then route to `classical-estimators` for the classifier/regressor:

```python
from mla.pca import PCA
from mla.linear_models import LogisticRegression

pca = PCA(5, solver="svd")
pca.fit(X_train)
X_train_reduced = pca.transform(X_train)
X_test_reduced = pca.transform(X_test)
clf = LogisticRegression(lr=0.001, max_iters=500)
clf.fit(X_train_reduced, y_train)
```

### Neural baseline versus classical baseline

When a user asks whether to use an MLP or a classical model, first build the classical baseline with the smaller smoke/check, then build a short `NeuralNet` dense model if the target task justifies it. MLAlgorithms is educational; prefer correctness and shape validation over benchmark claims.

### Dataset loaders for neural examples

`load_mnist()` and `load_nietzsche()` are owned by the unsupervised/data-loader sub-skill, but CNN/RNN usage patterns are documented in the neural sub-skill. Read both only when the user's task mentions the packaged demo data.

## Verification strategy

- Use bundled root and sub-skill smoke scripts for quick environment checks.
- Use native repo tests only when maintaining or verifying the checkout after the generated skill is complete.
- Skip or bound workflows that open plots, render Gym environments, run long training, or depend on display/video side effects.
