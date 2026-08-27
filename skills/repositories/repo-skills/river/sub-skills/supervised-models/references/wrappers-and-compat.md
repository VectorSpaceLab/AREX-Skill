# Wrappers, multiclass, multioutput, model selection, and compatibility

Use this reference when the base model family is known but the target shape, external API, or online hyperparameter-selection strategy needs an adapter.

## Binary, native multiclass, or wrapped multiclass

River has both native multiclass estimators and wrappers around binary classifiers.

| Need | Prefer | Rationale |
| --- | --- | --- |
| Binary probability or margin model | `linear_model.LogisticRegression`, `Perceptron`, `PAClassifier`, binary `facto` classifier, `tree.SGTClassifier` | These estimators are binary by design |
| Multiclass linear probabilities | `linear_model.SoftmaxRegression` | Native normalized multiclass probabilities; calibrated relative to one shared softmax objective |
| Multiclass from a strong binary model | `multiclass.OneVsRestClassifier(base_binary_classifier)` | One binary model per observed class; simple and supports mini-batches when the base classifier does |
| Multiclass with many classes and cheaper per-update work | `multiclass.OneVsOneClassifier(base_binary_classifier)` | One model per class pair, but each update touches models associated with the observed class pairs |
| Multiclass with error-correcting codes | `multiclass.OutputCodeClassifier(base_binary_classifier, code_size=...)` | Trades code size for redundancy and scalability |
| Count/text multiclass baseline | `naive_bayes.MultinomialNB`, `ComplementNB`, `BernoulliNB`, `GaussianNB` | Naive Bayes estimators are naturally multiclass classifiers |
| Tree multiclass | `tree.HoeffdingTreeClassifier`, `forest.ARFClassifier`, `forest.AMFClassifier` | Trees and forests can handle multiple class labels as they are observed |

A common hard decision is `SoftmaxRegression` versus `OneVsRestClassifier(LogisticRegression())`:

- Choose `SoftmaxRegression` when the task is truly multiclass, probabilities should sum to one by construction, and a linear decision surface is acceptable.
- Choose `OneVsRestClassifier` when you need the binary base classifier's special behavior, custom binary loss, or a classifier family that has no native multiclass version.
- Choose `OutputCodeClassifier` when the number of classes is large and a full one-vs-rest set becomes too expensive.

Example:

```python
from river import linear_model, multiclass, preprocessing

native = preprocessing.StandardScaler() | linear_model.SoftmaxRegression()
wrapped = preprocessing.StandardScaler() | multiclass.OneVsRestClassifier(
    linear_model.LogisticRegression()
)
```

When a wrapper creates class-specific models online, predictions only cover classes seen so far. Early in a stream, guard metrics against `None`, empty probability dictionaries, or missing class keys according to the metric's requirements.

## Multioutput supervised targets

River multioutput estimators expect `y` to be a dictionary of output names to target values.

| Target shape | Estimator | Behavior |
| --- | --- | --- |
| Independent multilabel or multiclass outputs | `multioutput.PerOutputClassifier(classifier=...)` | One cloned classifier per output key; no dependency features are shared between outputs |
| Independent multi-target regression | `multioutput.PerOutputRegressor(model=...)` | One cloned regressor per target key |
| Dependent multilabel/multiclass outputs | `multioutput.ClassifierChain(model=..., order=...)` | Prediction/probability for earlier outputs becomes a feature for later outputs |
| Dependent multi-target regression | `multioutput.RegressorChain(model=..., order=...)` | Earlier target predictions become features for later targets |
| Small to moderate binary multilabel set with probabilistic search | `multioutput.ProbabilisticClassifierChain` or `MonteCarloClassifierChain` | Enumerates or samples label combinations using `predict_proba_one` |
| Multi-label as observed label combinations | `multioutput.MultiClassEncoder(model=...)` | Encodes label sets into a multiclass target for the wrapped classifier |

Set `order` explicitly for chains when output dependencies are known or when reproducible feature names matter. Without an explicit order, chains infer order from target keys as they arrive.

Example:

```python
from river import linear_model, multioutput, preprocessing

model = multioutput.RegressorChain(
    model=preprocessing.StandardScaler() | linear_model.LinearRegression(),
    order=["sales", "returns", "profit"],
)

model.learn_one({"price": 9.99, "promo": 1}, {"sales": 12.0, "returns": 1.0, "profit": 20.5})
```

For multioutput metrics and progressive validation loops, route to `streaming-evaluation`.

## Model selection wrappers

`model_selection` selectors are themselves estimators. They hold multiple candidate River models and expose prediction/learning methods through the current best or selected model.

- `SuccessiveHalvingClassifier` and `SuccessiveHalvingRegressor` train all candidates for rungs and discard poor performers under a fixed `budget` and elimination rate `eta`.
- `BanditClassifier` and `BanditRegressor` use a `river.bandit` policy to choose which candidate model to update at each step.
- `GreedyRegressor` updates every candidate on every step and predicts with the current best.

Candidate rules:

1. Build candidates as full River estimators or pipelines, not parameter dictionaries.
2. Use a metric that `works_with` every candidate; selectors validate this and raise if the metric/class pair is incompatible.
3. Match classifier metrics to classifiers and regression metrics to regressors.
4. If a classification metric requires probabilities, ensure every candidate exposes `predict_proba_one`.
5. Give enough budget for at least one meaningful rung. Very small budgets can leave the first candidate as the best by default.

Example successive halving grid:

```python
from river import linear_model, metrics, model_selection, optim, preprocessing, utils

base = preprocessing.StandardScaler() | linear_model.LogisticRegression()
models = utils.expand_param_grid(base, {
    "LogisticRegression": {
        "optimizer": [
            (optim.SGD, {"lr": [0.1, 0.01]}),
            (optim.Adam, {"lr": [0.01, 0.001]}),
        ]
    }
})
selector = model_selection.SuccessiveHalvingClassifier(
    models=models,
    metric=metrics.Accuracy(),
    budget=200,
    eta=2,
)
```

Bandit selection example:

```python
from river import bandit, linear_model, metrics, model_selection, optim

models = [linear_model.LogisticRegression(optimizer=optim.SGD(lr)) for lr in [0.1, 0.01, 0.001]]
selector = model_selection.BanditClassifier(
    models=models,
    metric=metrics.Accuracy(),
    policy=bandit.Exp3(gamma=0.2, seed=42),
)
```

Bandit policies belong to River's specialized bandit module. If the task is about contextual bandits or bandit-only workflows rather than model selection among supervised candidates, route to `specialized-workflows`.

## scikit-learn compatibility

The `compat` module is only available when scikit-learn is installed.

### River estimator as scikit-learn estimator

Use `compat.convert_river_to_sklearn(estimator)` when a River model must be passed to an sklearn-compatible `fit`, `partial_fit`, `predict`, or `predict_proba` interface.

```python
from river import compat, linear_model, preprocessing

river_model = preprocessing.StandardScaler() | linear_model.LogisticRegression()
sk_model = compat.convert_river_to_sklearn(river_model)
```

Cautions:

- The wrapper deep-copies the River estimator to satisfy scikit-learn's fit conventions.
- Binary River classifiers are checked as binary when fitted through sklearn.
- The sklearn wrapper consumes arrays and, when pandas is installed, pandas frames.
- River dictionary feature names are converted from array column positions unless a dataframe provides names.

### scikit-learn incremental estimator as River estimator

Use `compat.convert_sklearn_to_river(estimator, classes=...)` when an sklearn estimator has `partial_fit` and you want to train it inside a River stream.

```python
from river import compat
from sklearn import linear_model as sk_linear_model

model = compat.convert_sklearn_to_river(
    sk_linear_model.SGDClassifier(loss="log_loss"),
    classes=[False, True],
)
```

Rules:

- The sklearn estimator must implement `partial_fit`.
- For classifiers, `classes` is required at conversion time.
- For regressors, do not pass `classes`.
- Classifier wrappers call `predict_proba`; choose an sklearn classifier/loss that supports probabilities if River code will call `predict_proba_one`.
- Feature order is fixed from the first dictionary or frame. Later mini-batches must include the same features, and missing columns raise a value error.

## Mini-batch wrappers

`multiclass.OneVsRestClassifier` supports `learn_many`, `predict_many`, and `predict_proba_many` when the wrapped binary classifier supports compatible mini-batch methods. Some linear models and naive Bayes estimators have mini-batch support; many trees, ensembles, and neighbors are primarily one-at-a-time.

Optional dependency cues:

- Use River's core `learn_one`/`predict_one` path when no dataframe backend is installed.
- Install a supported dataframe backend, commonly pandas through River's optional pandas extra, before relying on mini-batch APIs.
- Install scikit-learn before using `river.compat`.

## Wrapper validation checklist

Before handing a wrapper to an evaluation loop:

1. Identify the base estimator's task type: binary classifier, multiclass classifier, regressor, multilabel classifier, or multi-target regressor.
2. Confirm the wrapper's expected `y` shape: scalar label, numeric scalar, or dictionary of outputs.
3. Confirm prediction method availability: `predict_one`, `predict_proba_one`, `predict_many`, or `predict_proba_many`.
4. Choose a metric that works with the outer wrapped estimator.
5. For sample weights, verify both the wrapper and the base estimator accept and forward the chosen weight keyword.
6. Run a tiny stream before a long progressive validation pass.
