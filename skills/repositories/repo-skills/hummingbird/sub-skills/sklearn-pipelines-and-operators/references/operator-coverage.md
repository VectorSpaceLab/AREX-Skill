# Sklearn operator coverage

This reference distills Hummingbird's sklearn support surface for deciding whether a fitted estimator, transformer, or composite object is a reasonable conversion target. Operator support and backend availability are separate questions: a supported sklearn operator still needs the selected backend to be installed and, for tracing backends, representative `test_input`.

## Core sklearn families

Every child estimator or transformer in a composite object must be supported. If one step is unsupported, change that step or keep it outside Hummingbird conversion.

| Family | Supported classes or representative classes | Typical Hummingbird method family | Notes |
| --- | --- | --- | --- |
| Trees and tree ensembles | `DecisionTreeClassifier`, `DecisionTreeRegressor`, `RandomForestClassifier`, `RandomForestRegressor`, `ExtraTreesClassifier`, `ExtraTreesRegressor`, `GradientBoostingClassifier`, `GradientBoostingRegressor`, `HistGradientBoostingClassifier`, `HistGradientBoostingRegressor`, `IsolationForest` | Classifiers: `predict`, `predict_proba`; regressors: `predict`; isolation forest: `predict`, `decision_function`, `score_samples` | Tree implementation and precision knobs apply. Shifted integer class labels are handled by class remapping. |
| Linear and generalized linear models | `LinearRegression`, `LogisticRegression`, `LogisticRegressionCV`, `SGDClassifier`, `Ridge`, `RidgeCV`, `Lasso`, `ElasticNet`, `TweedieRegressor`, `PoissonRegressor`, `GammaRegressor` | Regressors: `predict`; probabilistic classifiers such as logistic regression: `predict`, `predict_proba` | Linear classifiers require integer class labels. Unsupported SGD losses can fail during conversion. |
| SVM family | `LinearSVC`, `LinearSVR`, `SVC`, `NuSVC` | `predict` for classifiers/regressors | `SVC`/`NuSVC` support `linear`, `poly`, `rbf`, and `sigmoid` kernels. The SVC converter has no class probabilities; do not assume `predict_proba` is available. `precomputed` kernels are unsupported. |
| Neighbors | `KNeighborsClassifier`, `KNeighborsRegressor` | Classifier: `predict_proba`; regressor: `predict` | Requires `extra_config={constants.BATCH_SIZE: <rows>}`. Supported metrics include `minkowski`, `euclidean`, `manhattan`, `chebyshev`, `wminkowski`, `seuclidean`, and `mahalanobis`; weights are `uniform` or `distance`. Class labels must be integers. |
| Naive Bayes | `BernoulliNB`, `GaussianNB`, `MultinomialNB` | `predict`, `predict_proba` | Tested for binary, multiclass, shifted integer labels, priors, smoothing, and Bernoulli binarization options. |
| Neural network estimators | `MLPClassifier`, `MLPRegressor` | Classifier: `predict`, `predict_proba`; regressor: `predict` | Treat as fitted sklearn estimators; validate parity on representative data. |
| Clustering and mixture | `KMeans`, `MeanShift`, `BayesianGaussianMixture` | `predict` | `MeanShift` support depends on the sklearn version exposing the class. |
| Preprocessing and encoders | `Binarizer`, `KBinsDiscretizer`, `LabelEncoder`, `MaxAbsScaler`, `MinMaxScaler`, `Normalizer`, `OneHotEncoder`, `PolynomialFeatures`, `RobustScaler`, `StandardScaler` | `transform` | `OneHotEncoder` and `LabelEncoder` have dedicated string handling; see the data-format reference before combining them with pandas or `ColumnTransformer`. |
| Imputation and missing indicators | `SimpleImputer`, `MissingIndicator`, legacy `Imputer` when present | `transform` | `Imputer` is version-dependent because sklearn removed it in newer versions. |
| Decomposition and cross-decomposition | `PCA`, `KernelPCA`, `FastICA`, `TruncatedSVD`, `PLSRegression` | Decomposition: `transform`; `PLSRegression`: `predict` | Validate with looser tolerances when algorithms are numerically sensitive. |
| Feature selection | `SelectKBest`, `SelectPercentile`, `VarianceThreshold` | `transform` | Use after fitting so selected feature masks/statistics are available. |
| Model selection wrappers | `GridSearchCV`, `RandomizedSearchCV` | Same as `best_estimator_` | Convert only after fitting/refitting; Hummingbird parses the selected `best_estimator_`, not the whole search process. |

## Parser-level composite wrappers

These wrappers are handled by Hummingbird's sklearn parser. They are not all ordinary operators from the public supported list; they describe how Hummingbird expands sklearn compositions into an internal graph.

| Wrapper | Parser behavior | Practical implication |
| --- | --- | --- |
| `Pipeline` | Sequentially parses each step, feeding each step's outputs into the next. | Every step must be supported. Validate the final method the pipeline exposes. |
| `ColumnTransformer` | Parses fitted `transformers_`, slices selected columns, supports `drop`, `passthrough`, and `transformer_weights`, then concatenates transformed outputs. | Column selectors, names, pandas/tuple layouts, and string dtypes are the main failure points. |
| `FeatureUnion` | Applies each transformer to the same inputs, optionally multiplies by `transformer_weights`, then concatenates outputs. | Good for parallel feature transforms such as scaler + min-max. Child transformers must be supported. |
| `FunctionTransformer` | Acts as identity when there is one input or concat when there are multiple inputs. | Do not expect arbitrary Python functions to be compiled. |
| `MultiOutputRegressor` | Parses each fitted estimator and concatenates outputs. | Children must be supported. `tree_op_precision_dtype="float64"` can be useful for tree children in multi-output tests. |
| `RegressorChain` | Parses each fitted estimator and concatenates previous outputs into later inputs before final output reorder. | Validate numeric parity carefully; children must be supported. |
| `BaggingClassifier`, `BaggingRegressor` | Parses fitted base estimators and aggregates them with a Hummingbird bagging operator. | Tested with SVC/logistic classifiers and linear regressors/SVR; regression aggregation can introduce small rounding differences. |
| `StackingClassifier`, `StackingRegressor` | Parses fitted estimators, extracts either `predict_proba` or `predict`, optionally passes through original inputs, then parses the final estimator. | Available only when the sklearn version provides stacking. `decision_function` stack methods are rejected. |

## Output method families

After conversion, validate the method the downstream code will call. Do not rely on generic estimator labels alone.

| Desired behavior | Hummingbird method to validate | Common sources |
| --- | --- | --- |
| Feature transform | `hb.transform(X)` vs `skl.transform(X)` | Scalers, encoders, imputers, decomposition, feature selection, `FeatureUnion`, transformer-only pipelines. |
| Class labels | `hb.predict(X)` vs `skl.predict(X)` | Tree classifiers, linear/SVM classifiers, clustering-like predictors, classifier pipelines. |
| Class probabilities | `hb.predict_proba(X)` vs `skl.predict_proba(X)` | Tree classifiers, logistic regression, naive Bayes, KNN classifiers, MLP classifiers, bagging classifiers when the source exposes probabilities. |
| Regression values | `hb.predict(X)` vs `skl.predict(X)` | Linear/GLM regressors, tree regressors, KNN regressors, `PLSRegression`, regressor pipelines. |
| Anomaly detection | `hb.decision_function(X)`, `hb.score_samples(X)`, and/or `hb.predict(X)` | `IsolationForest`. |

If a source estimator exposes a method that Hummingbird does not implement for that converter, either pick a different source estimator or keep that postprocessing outside the converted model.

## Tree implementation choices

Tree models can be represented using three strategies. If `constants.TREE_IMPLEMENTATION` is absent, Hummingbird selects by maximum tree depth:

| Strategy | Automatic heuristic | Good first use | Caveats |
| --- | --- | --- | --- |
| `"gemm"` | Max depth `<= 3` | Shallow trees; follows the matrix-multiplication tree strategy described in Hummingbird's public overview. | Can be inefficient or memory-heavy for deeper trees. |
| `"perf_tree_trav"` | Max depth `<= 10` and above the shallow threshold | Moderate-depth trees where a perfect-tree traversal layout is reasonable. | Validate parity and memory for nontrivial ensembles. |
| `"tree_trav"` | Deep or unknown max depth | Safest explicit choice for deep trees and many troubleshooting paths. | May be less throughput-oriented than shallower specialized layouts. |

Explicit pattern:

```python
from hummingbird.ml import constants, convert

hb_model = convert(
    fitted_tree_model,
    "torch",
    extra_config={
        constants.TREE_IMPLEMENTATION: "perf_tree_trav",
        constants.TREE_OP_PRECISION_DTYPE: "float64",
    },
)
```

`constants.TREE_OP_PRECISION_DTYPE` accepts only `"float32"` and `"float64"`; Hummingbird defaults to `"float32"`. Use `"float64"` when parity is sensitive to tree thresholds or leaf values, especially for deep trees, multi-output tree regressors, or float64 source data. For ONNX-source conversion paths, Hummingbird forces tree traversal internally to avoid a known GEMM issue, so do not use ONNX output as the place to compare tree implementation strategies.
