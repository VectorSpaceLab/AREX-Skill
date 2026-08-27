# Classic Igel Model and Metric Catalog

Use this reference when choosing `model.type`, `model.algorithm`, CV estimator behavior, or metric expectations for classic tabular Igel workflows.

## Inspect from the CLI

```bash
igel models
igel models --model_type classification --model_name RandomForest
igel models -type regression -name Ridge
igel metrics
```

`model_type` is limited to `regression`, `classification`, and `clustering`. Algorithm names are exact registry keys and are case-sensitive inside configs.

## Regression algorithms

Use `model.type: regression` with one of these exact `model.algorithm` names:

| Algorithm | Underlying family |
| --- | --- |
| `LinearRegression` | linear model |
| `SGDRegressor` | linear stochastic-gradient regressor |
| `Lasso` | linear L1 model; CV class registered |
| `LassoLars` | LARS/Lasso model; CV class registered |
| `BayesianRegression` | Bayesian ridge |
| `HuberRegression` | robust linear model |
| `Ridge` | ridge regression; CV class registered |
| `PoissonRegression` | generalized linear model |
| `ARDRegression` | automatic relevance determination |
| `TweedieRegression` | generalized linear model |
| `TheilSenRegression` | robust linear model |
| `GammaRegression` | generalized linear model |
| `RANSACRegression` | robust RANSAC regressor |
| `DecisionTree` | tree regressor |
| `ExtraTree` | extra tree regressor |
| `RandomForest` | random forest regressor |
| `ExtraTrees` | extra-trees regressor |
| `SVM` | support vector regressor |
| `LinearSVM` | linear support vector regressor |
| `NuSVM` | Nu support vector regressor |
| `NearestNeighbor` | k-neighbors regressor |
| `NeuralNetwork` | multilayer perceptron regressor |
| `ElasticNet` | linear mixed L1/L2 model; CV class registered |
| `BernoulliRBM` | neural-network/RBM class registered as a regressor option |
| `BoltzmannMachine` | alias to the RBM class |
| `Adaboost` | AdaBoost regressor |
| `Bagging` | bagging regressor |
| `GradientBoosting` | gradient-boosting regressor |

## Classification algorithms

Use `model.type: classification` with one of these exact `model.algorithm` names:

| Algorithm | Underlying family |
| --- | --- |
| `LogisticRegression` | linear classifier; CV class registered |
| `SGDClassifier` | linear stochastic-gradient classifier |
| `Ridge` | ridge classifier; CV class registered |
| `DecisionTree` | tree classifier |
| `ExtraTree` | extra tree classifier |
| `RandomForest` | random forest classifier |
| `ExtraTrees` | extra-trees classifier |
| `SVM` | support vector classifier |
| `LinearSVM` | linear support vector classifier |
| `NuSVM` | Nu support vector classifier |
| `NearestNeighbor` | k-neighbors classifier |
| `NeuralNetwork` | multilayer perceptron classifier |
| `PassiveAgressiveClassifier` | passive-aggressive classifier; preserve this historical spelling |
| `Perceptron` | perceptron classifier |
| `BernoulliRBM` | neural-network/RBM class registered as a classifier option |
| `BoltzmannMachine` | alias to the RBM class |
| `CalibratedClassifier` | calibrated classifier CV wrapper |
| `Adaboost` | AdaBoost classifier |
| `Bagging` | bagging classifier |
| `GradientBoosting` | gradient-boosting classifier |
| `BernoulliNaiveBayes` | Bernoulli naive Bayes |
| `CategoricalNaiveBayes` | categorical naive Bayes |
| `ComplementNaiveBayes` | complement naive Bayes |
| `GaussianNaiveBayes` | Gaussian naive Bayes |
| `MultinomialNaiveBayes` | multinomial naive Bayes |

## Clustering algorithms

Use `model.type: clustering` with one of these exact `model.algorithm` names:

| Algorithm | Underlying family |
| --- | --- |
| `KMeans` | k-means clustering |
| `KMedoids` | k-medoids implementation |
| `KMedians` | k-medians implementation |
| `AffinityPropagation` | affinity propagation |
| `Birch` | BIRCH clustering |
| `AgglomerativeClustering` | hierarchical agglomerative clustering |
| `FeatureAgglomeration` | feature agglomeration |
| `DBSCAN` | density-based clustering |
| `MiniBatchKMeans` | mini-batch k-means |
| `SpectralBiclustering` | spectral biclustering |
| `SpectralCoclustering` | spectral co-clustering |
| `SpectralClustering` | spectral clustering |
| `MeanShift` | mean-shift clustering |
| `OPTICS` | OPTICS clustering |

Clustering configs can omit `target`; fit stores cluster labels/centers when available and evaluation uses the estimator's score path rather than the regression/classification metric table.

## CV estimator support

`model.use_cv_estimator: true` switches to a registered sklearn CV class only when Igel's registry defines one:

| Model type | Algorithms with CV class registered |
| --- | --- |
| regression | `Lasso`, `LassoLars`, `Ridge`, `ElasticNet` |
| classification | `LogisticRegression`, `Ridge` |
| clustering | none |

This is separate from `model.cross_validate`, which runs `sklearn.model_selection.cross_validate` around the estimator.

## Metrics surfaced by `igel metrics`

| Model type | Metrics listed by the CLI |
| --- | --- |
| regression | `mean_squared_error`, `mean_absolute_error`, `mean_squared_log_error`, `median_absolute_error`, `r2_score` |
| classification | `accuracy_score`, `f1_score`, `precision_score`, `recall_score` |
| clustering | no separate metric table; clustering uses estimator score behavior |

Evaluation notes:

- For simple regression/classification shapes, Igel computes the metric functions above.
- For multiclass classification, precision/recall/f1 use micro averaging; accuracy uses standard accuracy.
- For multi-target predictions, Igel returns the estimator score instead of expanding every simple metric.
- Metric kwargs can be supplied only through programmatic calls that reach `evaluate_model`; the CLI does not expose metric-specific flags.

## Selection checklist

1. Choose `model.type` from the task: regression for continuous targets, classification for labels/classes, clustering for no target.
2. Pick an exact `model.algorithm` registry key from this file or `igel models`.
3. Put sklearn constructor kwargs under `model.arguments`.
4. Use `use_cv_estimator` only for algorithms with registered CV classes.
5. Use `cross_validate` or `hyperparameter_search` only when the runtime budget can cover it.
6. If ONNX export is required, verify the chosen sklearn estimator and feature shape convert successfully before promising deployment-ready ONNX.
