# Model overview

This sub-skill covers exporting **already fitted** Python estimators with the m2cgen 0.10.1 public export surface. The package itself has a base `numpy` dependency; optional estimator libraries such as scikit-learn, XGBoost, LightGBM, statsmodels, and lightning must be installed when their models are created or unpickled.

## Supported languages

m2cgen can emit native source code for:

- C
- C#
- Dart
- Elixir
- F#
- Go
- Haskell
- Java
- JavaScript
- PHP
- PowerShell
- Python
- R
- Ruby
- Rust
- Visual Basic / VBA-compatible Basic

The CLI names are lowercase with underscores where needed: `c`, `c_sharp`, `dart`, `elixir`, `f_sharp`, `go`, `haskell`, `java`, `javascript`, `php`, `powershell`, `python`, `r`, `ruby`, `rust`, `visual_basic`.

## Supported model catalog

Exact support is based on the fitted object's runtime library prefix and class name. Subclasses or wrappers can fail even when they are conceptually similar to a supported model.

### Linear models

| Library | Classification | Regression |
| --- | --- | --- |
| scikit-learn | `LogisticRegression`, `LogisticRegressionCV`, `PassiveAggressiveClassifier`, `Perceptron`, `RidgeClassifier`, `RidgeClassifierCV`, `SGDClassifier` | `ARDRegression`, `BayesianRidge`, `ElasticNet`, `ElasticNetCV`, `GammaRegressor`, `HuberRegressor`, `Lars`, `LarsCV`, `Lasso`, `LassoCV`, `LassoLars`, `LassoLarsCV`, `LassoLarsIC`, `LinearRegression`, `OrthogonalMatchingPursuit`, `OrthogonalMatchingPursuitCV`, `PassiveAggressiveRegressor`, `PoissonRegressor`, `RANSACRegressor`, `Ridge`, `RidgeCV`, `SGDRegressor`, `TheilSenRegressor`, `TweedieRegressor` |
| statsmodels | GLM binary-style results when represented as supported statsmodels result wrappers | `GLS`, `GLSAR`, `GLM`, `OLS`, `ProcessMLE`, `QuantReg`, `WLS` result wrappers |
| lightning | `AdaGradClassifier`, `CDClassifier`, `FistaClassifier`, `SAGAClassifier`, `SAGClassifier`, `SDCAClassifier`, `SGDClassifier` | `AdaGradRegressor`, `CDRegressor`, `FistaRegressor`, `SAGARegressor`, `SAGRegressor`, `SDCARegressor`, `SGDRegressor` |

Notes:

- `RANSACRegressor` is supported only when its fitted base estimator is also supported.
- scikit-learn GLM-style regressors are limited to supported inverse links: identity, log, and logit style links used by the fitted estimator.
- statsmodels GLM inverse links seen in implementation/tests include logit, power, inverse power, square root, inverse squared, identity, log, complementary log-log, negative binomial / nbinom, and cauchy.
- statsmodels results with unknown constant placement, unsupported underlying model, or unsupported link function fail during export.

### SVM models

| Library | Classification / outlier | Regression |
| --- | --- | --- |
| scikit-learn | `LinearSVC`, `NuSVC`, `OneClassSVM`, `SVC` | `LinearSVR`, `NuSVR`, `SVR` |
| lightning | `KernelSVC`, `LinearSVC` | `LinearSVR` |

Kernel notes:

- scikit-learn kernel SVM support covers `rbf`, `sigmoid`, `poly`, and `linear` kernels.
- lightning `KernelSVC` also covers a `cosine` kernel.
- A custom callable kernel is not supported.

### Tree models

| Classification | Regression |
| --- | --- |
| `DecisionTreeClassifier`, `ExtraTreeClassifier` | `DecisionTreeRegressor`, `ExtraTreeRegressor` |

### Random forest models

| Library | Classification | Regression |
| --- | --- | --- |
| scikit-learn | `ExtraTreesClassifier`, `RandomForestClassifier` | `ExtraTreesRegressor`, `RandomForestRegressor` |
| LightGBM | `LGBMClassifier` with RF booster mode | `LGBMRegressor` with RF booster mode |
| XGBoost | `XGBRFClassifier` | `XGBRFRegressor` |

### Boosting models

| Library | Classification | Regression |
| --- | --- | --- |
| LightGBM | `LGBMClassifier` with `gbdt`, `dart`, or `goss` booster modes | `LGBMRegressor` with `gbdt`, `dart`, or `goss` booster modes |
| XGBoost | `XGBClassifier` with `gbtree`, boosted-forest-style tree boosting, or `gblinear` booster modes | `XGBRegressor` with `gbtree`, boosted-forest-style tree boosting, or `gblinear` booster modes |

LightGBM objective support includes common regression, binary, multiclass, one-vs-rest, cross-entropy, gamma, poisson, tweedie, quantile, mape, huber, fair, and custom-output cases exercised by tests. Unsupported objectives such as ranking can fail with an `Unsupported objective function` error.

## Output semantics by family

### Linear and linear SVM

- Regression output is a scalar numeric score.
- Binary classification output is a scalar signed distance to the hyperplane for the second class.
- Multiclass classification output is a vector of signed distances, one value per class.
- This is decision-function style output, not automatically class labels.

### Kernel SVM

- Outlier detection output is a scalar signed distance: positive for inliers and negative for outliers.
- Binary classification output is a scalar signed distance to the hyperplane for the second class.
- Multiclass SVM output is a vector of one-vs-one scores with shape equivalent to `n_classes * (n_classes - 1) / 2` for scikit-learn `SVC`/`NuSVC` decision functions.

### Tree

- Regression leaves emit scalar leaf values.
- Classification leaves emit class probabilities when there is more than one class.
- Classifier leaf probabilities are normalized from stored class counts.

### Random forest

- Each tree is exported and evaluated independently.
- Tree outputs are averaged by multiplying the summed tree outputs by `1 / n_estimators`.
- Regression therefore returns an averaged scalar score.
- Classification returns averaged probability-like vectors when the tree outputs are vector-valued.

### Boosting

- Boosted trees assemble additive score expressions from the booster dump.
- XGBoost regression includes the configured base score plus additive tree or linear-booster contributions.
- Binary boosting classification usually returns `[1 - sigmoid(raw_score), sigmoid(raw_score)]`.
- Multiclass boosting classification uses softmax or objective-specific vector transforms.
- LightGBM regression objectives can add transforms such as sigmoid, `log1p(exp(x))`, exponential, or squared-magnitude style transforms depending on the objective.

## Version and compatibility notes

- Package metadata declares Python `>=3.7` and a base dependency on `numpy`.
- The console script entry point is `m2cgen = m2cgen.cli:main`.
- The repo's test matrix pins representative optional libraries: scikit-learn 1.0.2, XGBoost 1.6.2, LightGBM 3.3.2, statsmodels 0.13.2, and sklearn-contrib-lightning 0.6.2.post0. Other versions can work but are not guaranteed by that matrix.
