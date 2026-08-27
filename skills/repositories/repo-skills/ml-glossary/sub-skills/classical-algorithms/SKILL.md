---
name: classical-algorithms
description: "Explains ML Glossary classical algorithm families including
  decision trees, KNN, random forests, boosting, SVM, regression variants,
  clustering placeholders, and reinforcement-learning basics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Classical Algorithms

Use this sub-skill for ML Glossary tasks about non-neural model families and algorithm comparisons. It covers decision trees, K-nearest neighbors, random forests, boosting, SVMs, ordinary/polynomial/lasso/ridge/stepwise regression, clustering placeholder status, and introductory reinforcement-learning vocabulary.

## Read when

- The user asks to compare classical ML classifiers or regressors.
- The task mentions ID3, C4.5, CART, information gain, gain ratio, Gini, KNN, Euclidean distance, random forests, bagging, boosting, AdaBoost-style error focus, SVM margins, kernel trick, OLS, polynomial regression, lasso, ridge, stepwise/spline regression, clustering categories, or Q-learning.
- A documentation task needs a beginner-friendly algorithm entry or caveat about placeholder sections.
- The user asks whether a classical algorithm has an illustrative source snippet in the ML Glossary lineage.

## Main references

- `references/topic-map.md` contains the self-contained classical algorithm map and comparison tables.
- `references/troubleshooting.md` covers algorithm-selection mistakes, placeholder pages, and legacy code caveats.
- `scripts/knn_demo.py` is a safe pure-Python KNN demo adapted from the original source idea.

## Fast routing

| Task | Use |
| --- | --- |
| Compare ID3/C4.5/CART | `topic-map.md` decision-tree section. |
| Explain KNN in classification and regression | `topic-map.md` plus `scripts/knn_demo.py`. |
| Compare random forests, bagging, and boosting | `topic-map.md` ensemble section. |
| Explain SVM hyperplanes, support vectors, margins, and kernel trick | `topic-map.md` SVM section. |
| Explain regression variants such as OLS, lasso, ridge, polynomial | `topic-map.md` regression section, then cross-link to basics for formulas. |
| Explain Q-learning or RL vocabulary at a glossary level | `topic-map.md` reinforcement-learning section. |
| Fill in clustering or applications placeholders | `troubleshooting.md` placeholder guidance and root `../../references/resources-catalog.md`. |

## Workflow for answers

1. Identify the prediction type: classification, regression, clustering/unsupervised, or reinforcement learning.
2. Give the intuition first: nearest neighbors, tree splits, ensemble voting/averaging, margins, or reward-maximizing policy.
3. Explain required data assumptions: labeled data for supervised classifiers/regressors, distance metric and `k` for KNN, split criteria for trees, weak learners for boosting, kernel/feature space for SVM.
4. If code is requested, use the bundled `knn_demo.py` for KNN. For trees/random forests, describe the algorithm and cite legacy caveats rather than presenting source code as production-ready.
5. Route math-heavy logistic regression, gradient descent, and evaluation metrics back to `../basics-and-math/SKILL.md`.
6. Route neural-network classifier comparisons to `../neural-networks/SKILL.md` after covering the classical side.

## Boundaries

This sub-skill owns:

- Classical supervised algorithm explanations and comparisons.
- The repo's non-neural algorithm-page status, including placeholders.
- Introductory RL glossary content from the repository.
- Safe KNN demonstration.

Route elsewhere:

- Logistic-regression derivations, sigmoid/log loss, MSE, gradient descent formulas → `../basics-and-math/SKILL.md`.
- Neural-network architectures or deep classifiers → `../neural-networks/SKILL.md`.
- Library/dataset/paper recommendations for algorithm practice → `../../references/resources-catalog.md`.
- Sphinx authoring and build maintenance → `../../references/site-maintenance.md`.

## Quality checks

- Do not overstate placeholder sections: clustering pages and several RL subsections were incomplete.
- Do not claim legacy tree/random-forest source files are polished APIs; they were evidence for explanations.
- When comparing algorithms, tie the choice to data shape, interpretability, feature scaling, noise/outliers, nonlinearity, and computational cost.
- If the user needs modern scikit-learn commands, label them as modern external guidance rather than repo-grounded API facts.
