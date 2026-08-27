# Supervised model family guide

River supervised estimators consume one observation at a time as `x` dictionaries and `y` targets. Many models also support mini-batches through `learn_many`/`predict_many`, but choose the model first from the one-at-a-time contract, then route batching and evaluation details to `streaming-evaluation`.

## Selection matrix

| Situation | Prefer | Why | Watch for |
| --- | --- | --- | --- |
| Large sparse dictionaries, one-hot categorical IDs, text-like features, fast updates | `linear_model.LogisticRegression`, `linear_model.LinearRegression`, `linear_model.Perceptron`, `linear_model.PAClassifier`, `linear_model.PARegressor`, `linear_model.AdPredictor` | Weight dictionaries only need keys that appear; optimizers update incrementally | Scale dense numeric features; set compatible losses; use `w=` only where supported |
| Native multiclass linear probabilities | `linear_model.SoftmaxRegression` | A single multiclass model with normalized class probabilities and one weight dictionary per class | It is not a wrapper around binary models; use multiclass metrics |
| Binary classifiers that need multiclass adaptation | `multiclass.OneVsRestClassifier`, `multiclass.OneVsOneClassifier`, `multiclass.OutputCodeClassifier` | Wrap binary classifiers when no native multiclass estimator fits | Probability availability and class growth are wrapper-specific |
| Non-linear decision boundaries, mixed numeric/nominal features, interpretable split structure | `tree.HoeffdingTreeClassifier`, `tree.HoeffdingTreeRegressor`, adaptive/EFDT/SGT variants | Incremental splits handle interactions without dense feature crosses | Growth is delayed by split statistics; memory limits affect leaf activity |
| Stronger non-linear models with randomization or drift-aware trees | `forest.ARFClassifier`, `forest.ARFRegressor`, `forest.AMFClassifier`, `forest.AMFRegressor`, `forest.OXTRegressor` | Ensembles of online trees improve stability and accuracy | More models mean more memory/CPU; metric type must match task |
| Simple probabilistic baselines or text/count features | `naive_bayes.GaussianNB`, `naive_bayes.MultinomialNB`, `naive_bayes.BernoulliNB`, `naive_bayes.ComplementNB` | Fast, low-configuration classifiers with `predict_proba_one` | Count models expect non-negative feature values |
| Recent-neighbor behavior and local non-parametric predictions | `neighbors.KNNClassifier`, `neighbors.KNNRegressor` with `LazySearch` or `SWINN` engines | Uses a sliding memory of observed samples rather than fitted coefficients | Tune window/engine size; distance functions must match feature encoding |
| Sparse high-cardinality feature interactions | `facto.FMClassifier`, `FMRegressor`, `FFM*`, `FwFM*`, `HOFM*` | Learns pairwise, field-aware, field-weighted, or higher-order latent interactions online | Loss/optimizer/initializer choices matter; classification variants are binary |
| Combine several online models | `ensemble.BaggingClassifier`, `BaggingRegressor`, `AdaBoostClassifier`, `ADWIN*`, `LeveragingBaggingClassifier`, `SRP*`, `VotingClassifier`, `StackingClassifier`, `EWARegressor` | Voting, bagging, boosting, stacking, random patches, and hedging support online ensembling | Wrapped base models must support the methods the ensemble calls |
| Tune a small online hyperparameter grid during a stream | `model_selection.SuccessiveHalving*`, `Bandit*`, `GreedyRegressor` | Selects among already-built River models online | Metric must work with every candidate model |
| Need scikit-learn API integration | `compat.convert_river_to_sklearn`, `compat.convert_sklearn_to_river` | Bridges batch ecosystem and River online estimators | Requires scikit-learn; sklearn-to-River requires `partial_fit` and classifier `classes` |

## Linear models

Use `linear_model` when the task is close to a generalized linear model or margin classifier and you want explicit optimizer/loss control.

- `LogisticRegression` is a binary probabilistic classifier. It exposes `predict_proba_one`, `predict_one`, and mini-batch methods. Default loss is binary logistic loss. For multiclass, use `SoftmaxRegression` or a wrapper.
- `LinearRegression` is a numeric regressor. It supports regression losses such as squared, Huber, absolute, quantile, Poisson, Cauchy, and epsilon-insensitive hinge.
- `SoftmaxRegression` is native multiclass logistic regression with multiclass cross-entropy behavior.
- `Perceptron` is implemented as a hinge-loss linear classifier with aggressive learning-rate defaults.
- `PAClassifier` and `PARegressor` implement passive-aggressive updates and are useful when you want large-margin online behavior without selecting a full optimizer object.
- `BayesianLinearRegression` can return predictive distributions via `predict_one(x, with_dist=True)` and is less dependent on feature scaling than standard SGD linear regression.
- `AdPredictor` keeps Gaussian weight beliefs for sparse click-through-rate-style binary classification.

Practical defaults:

```python
from river import linear_model, optim, preprocessing

model = preprocessing.StandardScaler() | linear_model.LogisticRegression(
    optimizer=optim.SGD(0.01),
    l2=1e-4,
)
```

Use scaling for dense numeric features before SGD-like linear models. Sparse one-hot dictionaries often work without centering; if you mix dense numeric and sparse categorical signals, route feature construction to `pipelines-and-features` and keep the final supervised choice here.

## Trees

Use `tree` when non-linear feature interactions should be learned through incremental splits.

- `HoeffdingTreeClassifier` and `HoeffdingTreeRegressor` are the standard online tree choices.
- `HoeffdingAdaptiveTreeClassifier` and `HoeffdingAdaptiveTreeRegressor` add adaptive behavior with drift detectors inside the tree.
- `ExtremelyFastDecisionTreeClassifier` can revise earlier split decisions; it may converge faster in samples but can be slower per observation.
- `LASTClassifier` splits leaves using local change detection.
- `SGTClassifier` and `SGTRegressor` optimize losses directly at leaves; `SGTClassifier` is binary.
- `ISOUPTreeRegressor` handles multi-target regression dictionaries.

Key knobs:

- `grace_period` controls how many samples a leaf observes between split attempts.
- `max_depth` caps tree depth.
- `max_size`, `memory_estimate_period`, `stop_mem_management`, and inactive leaves control memory.
- `leaf_prediction` commonly selects majority-class/naive-Bayes/adaptive behavior for classification or mean/model/adaptive behavior for regression.
- `splitter` chooses numeric split statistics. Common splitters include exhaustive, Gaussian, histogram, EBST, TE-BST, and quantizer-based splitters.
- `nominal_attributes` tells a tree which features should be treated as categorical.

Tiny tree pattern:

```python
from river import tree

model = tree.HoeffdingTreeClassifier(
    grace_period=50,
    leaf_prediction="mc",
    max_depth=8,
)
```

If a tree does not split in a tiny smoke run, that is often expected. Lower `grace_period` for tests and use enough varied observations.

## Forests and supervised ensembles

Use `forest` for ready-made online tree ensembles and `ensemble` for general wrappers around base estimators.

- `forest.ARFClassifier`/`ARFRegressor` are adaptive random forests with resampling, feature-subset diversity, and detector-controlled resets.
- `forest.AMFClassifier`/`AMFRegressor` are aggregated Mondrian forests for online learning with anytime predictions.
- `forest.OXTRegressor` adds online Extra Trees-style split randomization.
- `ensemble.BaggingClassifier`/`BaggingRegressor` use online bootstrap aggregation.
- `ensemble.ADWINBaggingClassifier`, `ADWINBoostingClassifier`, and `LeveragingBaggingClassifier` combine ensembles with drift-aware replacement or stronger resampling.
- `ensemble.SRPClassifier`/`SRPRegressor` train random patches over samples and subspaces; defaults use tree-like learners but can wrap other compatible estimators.
- `ensemble.VotingClassifier` combines classifier probabilities or votes.
- `ensemble.StackingClassifier` learns a meta-classifier from base classifier outputs.
- `ensemble.EWARegressor` hedges several regressors using an online loss.

Pick metrics carefully. Forest and ensemble constructors that accept a metric expect a classification metric for classifiers and a regression metric for regressors. Some classifier selectors use `predict_one` when the metric requires labels and `predict_proba_one` otherwise.

## Naive Bayes

Use `naive_bayes` for fast baselines and count models.

- `GaussianNB` is suitable for real-valued features and maintains per-class Gaussian distributions per feature.
- `MultinomialNB` is suitable for non-negative counts such as word counts.
- `BernoulliNB` binarizes positive/count features using `true_threshold`.
- `ComplementNB` is useful for imbalanced text/count classification.

Naive Bayes classifiers expose probabilities. Before learning any class, probability dictionaries can be empty or uniform depending on the estimator and wrapper; update metrics only after checking prediction availability when your loop starts cold.

## Neighbors

Use `neighbors` when recent examples should remain explicit.

```python
from river import neighbors

model = neighbors.KNNClassifier(
    n_neighbors=3,
    engine=neighbors.LazySearch(window_size=200),
)
```

- `LazySearch` performs exact search over a bounded FIFO window.
- `SWINN` maintains an approximate nearest-neighbor graph with a sliding window.
- `KNNClassifier` supports weighted voting and optional softmax probability smoothing.
- `KNNRegressor` aggregates neighbor targets with `mean`, `median`, or weighted behavior depending on configuration.

Keep feature scales comparable before distance-based models. Route scaling and mixed feature handling to `pipelines-and-features`.

## Factorization machines

Use `facto` when interactions in sparse dictionaries matter more than single coefficients.

- `FMClassifier`/`FMRegressor` learn pairwise latent interactions.
- `FFMClassifier`/`FFMRegressor` use field-aware latent factors.
- `FwFMClassifier`/`FwFMRegressor` add learned field-pair weights.
- `HOFMClassifier`/`HOFMRegressor` support higher-order interactions controlled by `degree`.

The classifier variants are binary classifiers. Use `multiclass.OneVsRestClassifier` or `multiclass.OutputCodeClassifier` if you need multiclass behavior from a binary factorization machine. Use a fixed `seed` when comparing factorization models because latent initializers are stochastic.

## Validation handoff

After choosing the family, route complete train/test mechanics to `streaming-evaluation`. After choosing feature extraction, scaling, dictionaries, or pipeline composition, route to `pipelines-and-features`. For model-specific smoke checks only, run:

```bash
python scripts/supervised_model_smoke.py --checks all
```
