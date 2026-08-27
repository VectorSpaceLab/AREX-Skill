# Classical Algorithms Topic Map

## Purpose

Read this for self-contained explanations of the ML Glossary classical-algorithm pages and code evidence: decision trees, KNN, logistic-regression routing, random forests, boosting, SVM, regression variants, clustering placeholders, and introductory reinforcement learning.

## Classification algorithms

### Bayesian

The source page only marked this as overlapping/incomplete. If a user asks for Bayesian classifiers, explain at a high level that Bayesian classifiers use probability and Bayes' rule to choose the most probable class given features, then label deeper details as outside the repo-grounded coverage unless the user asks for a modern addition.

### Decision trees

Decision trees split a dataset recursively into smaller segments until nodes are pure enough, too small, or cannot be split further. They are greedy: each split is chosen for local quality, not guaranteed global optimality.

Generic tree construction:

1. Put all training instances at the root.
2. Choose a split feature and split value using a split criterion.
3. Partition examples into child nodes.
4. If a child is pure or meets a stopping rule, make it a leaf.
5. Otherwise recurse.

#### ID3 vs C4.5 vs CART

| Algorithm | Split criterion | Feature types | Problem type | Tree shape |
| --- | --- | --- | --- | --- |
| ID3 | Information gain | Categorical | Classification | Multiway tree |
| C4.5 | Gain ratio / normalized information gain | Categorical and numerical | Classification | Multiway tree |
| CART | Gini for classification; MSE/MAE-style criteria for regression | Categorical and numerical | Classification and regression | Binary tree |

Use this comparison when a user asks why there are multiple tree algorithms. For modern library usage, note that scikit-learn's tree implementation is CART-like.

### K-nearest neighbors (KNN)

KNN is supervised learning for classification and regression. It stores the training examples and predicts from the nearest examples to a target point.

Procedure:

1. Choose `k` and a distance metric, commonly Euclidean distance.
2. Compute distance from the target point to every training example.
3. Sort by distance and keep the top `k` neighbors.
4. For regression, average the neighbors' labels/values.
5. For classification, take the most common neighbor class.

Important decisions:

- `k` too small can be noisy; `k` too large can oversmooth.
- Feature scaling matters because distance is sensitive to units.
- KNN can be intuitive but slow for large datasets without indexing/approximation.

A safe bundled demo lives at `../scripts/knn_demo.py`.

### Logistic regression

The classification page routes logistic regression to the basics/math material. Use `../../basics-and-math/SKILL.md` for sigmoid, decision boundary, log loss, and gradient formulas.

### Random forests

A random forest is an ensemble of decision trees. The source page referenced a random forest classifier built from ID3-like trees, but the code is best treated as educational evidence, not a stable implementation.

Key ideas:

- Many trees vote for classification or average for regression.
- Bagging/bootstrap aggregation reduces variance by training on resampled data.
- Feature randomness helps decorrelate trees.
- More trees can improve stability but increase compute.

### Boosting

Boosting is an ensemble strategy that trains weak learners sequentially, with later learners focusing on earlier mistakes. It can increase predictive power for classification or regression.

Teaching cues from the source:

- Ensembles use the wisdom of multiple models.
- Voting or averaging combines predictions.
- Boosting differs from bagging/random forests because learners are trained one after another.
- Misclassified or high-error examples receive more attention/weight in later rounds.
- Boosting can overfit if pushed too far or if weak learners are too complex.

### Support vector machines (SVM)

SVMs separate classes with a hyperplane. The best hyperplane maximizes the margin, the distance to the nearest training points from each class. Those nearest points are support vectors.

Types:

- **Linear SVM**: used when classes can be separated with a straight line/flat hyperplane in the feature space.
- **Nonlinear SVM**: uses kernels or feature transformations to separate data that is not linearly separable in the original space.

Kernel trick intuition: instead of manually adding higher-dimensional features such as `z = x^2 + y^2`, a kernel computes similarity as if points were mapped into a richer space.

## Regression algorithm variants

These source sections are compact definitions. Route deeper formulas to basics/math.

| Variant | Explanation | Useful caveat |
| --- | --- | --- |
| Ordinary least squares (OLS) | Linear regression fit by minimizing sum of squared residuals. | Sensitive to outliers and multicollinearity. |
| Polynomial regression | Maps original features into polynomial combinations, then fits a linear model in that expanded space. | Can overfit if degree is too high. |
| Lasso regression | Adds L1 penalty `alpha * Σ |w_j|` to reduce complexity and encourage sparse coefficients. | Useful for feature selection; too much penalty underfits. |
| Ridge regression | Adds L2 penalty `alpha * Σ w_j^2` to constrain coefficient size. | Keeps all variables but shrinks them; helps multicollinearity. |
| Stepwise/spline regression | Fits piecewise behavior using step functions or selected terms. | Easy to overfit or misuse without validation. |

## Clustering page status

The clustering page named these categories but did not provide substantive explanations:

- Centroid methods
- Density methods
- Distribution methods
- Hierarchical methods
- K-means
- Mean shift

When asked to write content for these, be explicit that the source was a placeholder. A concise starter entry can say:

- K-means is a centroid method that alternates assigning points to the nearest cluster center and moving centers to the mean of assigned points.
- Density methods group dense regions separated by sparse regions.
- Hierarchical methods build nested clusters either bottom-up or top-down.

Label any deeper modern explanation as an addition beyond original coverage.

## Reinforcement-learning overview

The source reinforcement-learning page was introductory with some TODO sections.

Core vocabulary:

| Term | Explanation |
| --- | --- |
| Agent | The decision-making algorithm. |
| Environment | The world/process containing states. |
| State | Current situation of the environment. |
| Action | Choice made by the agent that changes or interacts with the state. |
| Reward | Feedback signal returned by the environment. |
| Policy | Mapping from states to actions. |
| Value function | Expected cumulative reward from a state under a policy. |
| Discount factor `γ` | Weight for future rewards; values below 1 encourage convergence and nearer rewards. |

### Exploration vs exploitation

- Exploitation chooses the best currently known action.
- Exploration tries other actions to discover better options.
- Epsilon-greedy policies pick the best action with high probability and a random action with small probability.

### MDP framing

A Markov decision process describes states `S`, actions `A`, transition probabilities `T`, rewards `R`, and discount factor `γ`. The goal is to maximize expected discounted cumulative reward.

### Q-learning

Q-learning is an off-policy model-free RL algorithm for learning action values `Q(s,a)`.

Sketch:

1. Initialize Q-values.
2. At state `s_t`, choose an action, often epsilon-greedy.
3. Observe reward and next state.
4. Use the best next action value to compute a temporal-difference target.
5. Update `Q(s_t, a_t)` toward that target with learning rate `α`.

Limitations:

- Tabular Q-learning struggles with very large or continuous state/action spaces.
- Deep Q-learning uses a neural network to approximate Q-values for larger spaces.

## Algorithm-selection heuristics

| Situation | Candidate family | Why |
| --- | --- | --- |
| Need a transparent rule path | Decision tree | Easy to visualize and explain. |
| Need robust tabular baseline | Random forest / boosting | Ensembles often perform well without deep feature engineering. |
| Need simple distance-based explanation | KNN | Intuitive nearest-example reasoning. |
| Need maximum-margin classifier | SVM | Strong for medium-size feature vectors with appropriate kernels. |
| Need continuous output | Linear/ridge/lasso/polynomial regression | Fits numeric targets and exposes coefficients. |
| Need unlabeled grouping | Clustering | Use placeholder caveat; choose a clustering family based on data shape. |
| Need sequential decisions with rewards | Reinforcement learning | Use agent/environment/reward/policy framing. |
