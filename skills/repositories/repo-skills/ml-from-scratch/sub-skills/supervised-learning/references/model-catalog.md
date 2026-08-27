# Supervised Model Catalog

This catalog summarizes the supervised estimators exposed by `mlfromscratch.supervised_learning`. The implementations are educational, NumPy-based classes with repo-specific constructors and method signatures; do not assume scikit-learn's `fit(X, y)` / `predict(X)` pattern always applies.

## Common input conventions

- Features: pass numeric `numpy.ndarray` data shaped `(n_samples, n_features)`. For a single feature, use `x.reshape(-1, 1)` rather than a 1-D vector.
- Regression targets: most regressors expect a 1-D numeric target array shaped `(n_samples,)`.
- Nominal labels: most multiclass classifiers use non-negative integer labels such as `0, 1, 2`.
- Binary margin labels: `SupportVectorMachine` and `Adaboost` expect labels in `{-1, 1}`.
- One-hot labels: `Perceptron`, `Neuroevolution`, and `ParticleSwarmOptimizedNN` workflows use neural-network style one-hot targets, usually from `mlfromscratch.utils.to_categorical`.
- Scaling: SVM, KNN, logistic regression, Perceptron, and gradient-descent regressors are more stable with normalized or standardized features.

## Regression estimators

| Class | Constructor | Methods | Use when | Notes |
| --- | --- | --- | --- | --- |
| `LinearRegression` | `LinearRegression(n_iterations=100, learning_rate=0.001, gradient_descent=True)` | `fit(X, y)`, `predict(X)` | Linear numeric target prediction. | Gradient descent stores `training_errors`. The `gradient_descent=False` least-squares path can be useful, but verify it on a smoke case before trusting it. |
| `PolynomialRegression` | `PolynomialRegression(degree, n_iterations=3000, learning_rate=0.001)` | `fit(X, y)`, `predict(X)` | Nonlinear scalar regression using polynomial feature expansion. | Expands features internally; keep `degree` modest and check learning rate. |
| `LassoRegression` | `LassoRegression(degree, reg_factor, n_iterations=3000, learning_rate=0.01)` | `fit(X, y)`, `predict(X)` | Polynomial regression with L1 regularization. | Normalizes polynomial features internally. |
| `RidgeRegression` | `RidgeRegression(reg_factor, n_iterations=1000, learning_rate=0.001)` | `fit(X, y)`, `predict(X)` | Linear regression with L2 regularization. | Does not polynomial-expand input. |
| `PolynomialRidgeRegression` | `PolynomialRidgeRegression(degree, reg_factor, n_iterations=3000, learning_rate=0.01, gradient_descent=True)` | `fit(X, y)`, `predict(X)` | Regularized polynomial regression. | Constructor accepts `gradient_descent`, but implementation still follows the gradient-descent base path. |
| `ElasticNet` | `ElasticNet(degree=1, reg_factor=0.05, l1_ratio=0.5, n_iterations=3000, learning_rate=0.01)` | `fit(X, y)`, `predict(X)` | Polynomial regression with mixed L1/L2 penalty. | Use small `learning_rate` for high-degree features. |
| `RegressionTree` | `RegressionTree(min_samples_split=2, min_impurity=1e-7, max_depth=inf, loss=None)` | `fit(X, y)`, `predict(X)` | Tree-structured numeric target prediction. | Shares the decision-tree implementation; see NumPy compatibility notes. |
| `GradientBoostingRegressor` | `GradientBoostingRegressor(n_estimators=200, learning_rate=0.5, min_samples_split=2, min_var_red=1e-7, max_depth=4, debug=False)` | `fit(X, y)`, `predict(X)` | Additive tree regression. | Uses progress bars and repeated regression trees; use very small `n_estimators` for smokes. |

## Classification estimators

| Class | Constructor | Methods | Labels | Use when | Notes |
| --- | --- | --- | --- | --- | --- |
| `LogisticRegression` | `LogisticRegression(learning_rate=0.1, gradient_descent=True)` | `fit(X, y, n_iterations=4000)`, `predict(X)` | Binary `0/1` | Fast baseline for binary separable tabular data. | No intercept is inserted automatically; add/scale features if needed. |
| `KNN` | `KNN(k=5)` | `predict(X_test, X_train, y_train)` | Non-negative integers | Simple multiclass lookup baseline. | No `fit`; `np.bincount` requires integer-like labels. |
| `NaiveBayes` | `NaiveBayes()` | `fit(X, y)`, `predict(X)` | Integer or comparable class labels | Gaussian feature model baseline. | Returns a Python list; convert to `np.asarray` for metrics. |
| `LDA` | `LDA()` | `fit(X, y)`, `predict(X)`, `transform(X, y)` | Binary `0/1` | Fisher discriminant for two classes. | `fit` separates `X[y == 0]` and `X[y == 1]`; remap labels before training. |
| `MultiClassLDA` | `MultiClassLDA(solver='svd')` | `transform(X, y, n_components)`, `plot_in_2d(X, y, title=None)` | Nominal integers | Supervised dimensionality reduction before visualization or downstream models. | It is a transformer, not a classifier; prefer `transform` in headless workflows. |
| `Perceptron` | `Perceptron(n_iterations=20000, activation_function=Sigmoid, loss=SquareLoss, learning_rate=0.01)` | `fit(X, y_one_hot)`, `predict(X)` | One-hot targets | Single-layer neural classifier. | `predict` returns activation scores/probabilities; use `argmax` for class labels. |

## Trees, ensembles, margin methods, and boosting

| Class | Constructor | Methods | Labels | Notes |
| --- | --- | --- | --- | --- |
| `ClassificationTree` | `ClassificationTree(min_samples_split=2, min_impurity=1e-7, max_depth=inf, loss=None)` | `fit(X, y)`, `predict(X)` | Nominal labels | Uses information gain and majority-vote leaves. Current NumPy may expose `divide_on_feature` shape incompatibilities. |
| `RandomForest` | `RandomForest(n_estimators=100, max_features=None, min_samples_split=2, min_gain=0, max_depth=inf)` | `fit(X, y)`, `predict(X)` | Integer labels | Trains many `ClassificationTree` instances and uses `np.bincount`, so labels must be integer-like. |
| `SupportVectorMachine` | `SupportVectorMachine(C=1, kernel=rbf_kernel, power=4, gamma=None, coef=4)` | `fit(X, y)`, `predict(X)` | `{-1, 1}` | Requires `cvxopt`. Kernels come from `mlfromscratch.utils.kernels`: `linear_kernel`, `polynomial_kernel`, `rbf_kernel`. |
| `Adaboost` | `Adaboost(n_clf=5)` | `fit(X, y)`, `predict(X)` | `{-1, 1}` | Decision-stump boosting. Keep `n_clf` small for quick checks. |
| `GradientBoostingClassifier` | `GradientBoostingClassifier(n_estimators=200, learning_rate=0.5, min_samples_split=2, min_info_gain=1e-7, max_depth=2, debug=False)` | `fit(X, y)`, `predict(X)` | Nominal integers | Converts labels to one-hot internally and trains regression trees on gradients. |
| `XGBoost` | `XGBoost(n_estimators=200, learning_rate=0.001, min_samples_split=2, min_impurity=1e-7, max_depth=2)` | `fit(X, y)`, `predict(X)` | Nominal integers | Educational XGBoost-like classifier using custom regression trees and logistic loss. |

## Optimization-driven neural classifiers

| Class | Constructor | Main method | Target convention | Use when |
| --- | --- | --- | --- | --- |
| `Neuroevolution` | `Neuroevolution(population_size, mutation_rate, model_builder)` | `evolve(X, y_one_hot, n_generations)` | One-hot matrix | Evolve a `NeuralNetwork` population built by a callback. |
| `ParticleSwarmOptimizedNN` | `ParticleSwarmOptimizedNN(population_size, model_builder, inertia_weight=0.8, cognitive_weight=2, social_weight=2, max_velocity=20)` | `evolve(X, y_one_hot, n_generations)` | One-hot matrix | Optimize neural-network weights with particle swarm updates. |

The `model_builder` callback for the optimization-driven neural classifiers receives `n_inputs` and `n_outputs` and must return a compatible `mlfromscratch.deep_learning.NeuralNetwork`. Use the deep-learning sub-skill for layer, optimizer, and loss details.
