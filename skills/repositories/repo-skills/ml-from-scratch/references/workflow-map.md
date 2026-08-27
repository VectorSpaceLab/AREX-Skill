# Workflow map

This map tells future agents which self-contained skill entry point replaces or distills the package's legacy demonstration families. Do not reopen demonstration files from a source checkout at runtime; use the bundled sub-skills, references, and smoke helpers.

## Model-family routing

| Workflow intent | Skill owner | Primary reference | Bundled helper |
| --- | --- | --- | --- |
| Linear or polynomial regression, regularized regression, MSE checks | `sub-skills/supervised-learning/` | `sub-skills/supervised-learning/references/workflows.md` | `sub-skills/supervised-learning/scripts/run_regression_smoke.py` |
| Binary or multiclass classical classification, label encoding, accuracy checks | `sub-skills/supervised-learning/` | `sub-skills/supervised-learning/references/model-catalog.md` | `sub-skills/supervised-learning/scripts/run_classification_smoke.py` |
| KMeans, DBSCAN, PCA, and cluster-label diagnostics | `sub-skills/unsupervised-learning/` | `sub-skills/unsupervised-learning/references/workflows.md` | `sub-skills/unsupervised-learning/scripts/run_clustering_smoke.py` |
| Apriori/FPGrowth frequent itemsets and association rules | `sub-skills/unsupervised-learning/` | `sub-skills/unsupervised-learning/references/algorithm-catalog.md` | `sub-skills/unsupervised-learning/scripts/run_association_smoke.py` |
| Toy string-target genetic search | `sub-skills/unsupervised-learning/` | `sub-skills/unsupervised-learning/references/workflows.md` | `sub-skills/unsupervised-learning/scripts/run_optimization_smoke.py` |
| MLP tabular classifier, one-hot labels, softmax/CrossEntropy | `sub-skills/deep-learning/` | `sub-skills/deep-learning/references/workflows.md` | `sub-skills/deep-learning/scripts/run_mlp_smoke.py` |
| CNN classifier with channels-first image tensors | `sub-skills/deep-learning/` | `sub-skills/deep-learning/references/api-reference.md` | `sub-skills/deep-learning/scripts/run_cnn_smoke.py` |
| RNN, autoencoder, GAN/DCGAN, RBM, and advanced neural/generative model-building | `sub-skills/deep-learning/` plus `sub-skills/unsupervised-learning/` for RBM ownership | `sub-skills/deep-learning/references/workflows.md` and `sub-skills/unsupervised-learning/references/workflows.md` | Reference-only by default; no long training helper bundled |
| CartPole DQN, replay memory, epsilon decay, old Gym API compatibility | `sub-skills/reinforcement-learning/` | `sub-skills/reinforcement-learning/references/workflows.md` | `sub-skills/reinforcement-learning/scripts/run_dqn_smoke.py` |
| Cross-cutting import, dependency, plotting, and utility behavior | Root skill | `references/troubleshooting.md`, `references/shared-utilities.md` | `scripts/check_install.py` |

## Choosing between overlapping owners

- If a task names a classical estimator even when it uses a neural target encoding, start in `supervised-learning` and cross-link to `deep-learning` only for model-builder details.
- If a task names neural layers, optimizers, losses, or activation functions, start in `deep-learning` even if the final task is classification.
- If a task names RBM as an unsupervised reconstruction algorithm, start in `unsupervised-learning`; use `deep-learning` only for shared layer/optimizer concepts.
- If a task names CartPole, Gym, replay memory, epsilon, or `DeepQNetwork`, start in `reinforcement-learning`; route to `deep-learning` for the callback model architecture.
- If a task asks for a package-wide installation check or dependency diagnosis, start at root `references/troubleshooting.md` and then route to the sub-skill that owns the failing workflow.

## Native verification candidates retained for final checks

The strongest native-backed validation families are:

- Supervised regression smoke from the polynomial/linear regression family.
- Supervised classification smoke from logistic/KNN/NaiveBayes/LDA/SVM/Adaboost families.
- Unsupervised clustering/PCA smoke.
- Association mining smoke.
- MLP and CNN one-epoch neural-network smokes.
- DQN one-epoch no-render CartPole smoke with Gym compatibility wrapper.

Longer, plotted, or broad multi-model demonstrations are documented as reference-only evidence unless a user explicitly requests an experiment-scale run.
