# Custom strategies

This reference shows the main composition patterns for modAL query strategies.

## 1) Build a combined utility

Use this when you want one score from several compatible measures.

```python
from modAL.uncertainty import classifier_uncertainty, classifier_margin
from modAL.utils.combination import make_linear_combination, make_query_strategy
from modAL.utils.selection import multi_argmax

# margin is a loss-like signal, so invert or normalize it before mixing.
def top2_selector(values):
    return multi_argmax(values, n_instances=2)

combined_utility = make_linear_combination(
    classifier_uncertainty,
    lambda learner, X: 1.0 - classifier_margin(learner, X),
    weights=[0.7, 0.3],
)

query_strategy = make_query_strategy(combined_utility, top2_selector)
```

Use this pattern when:
- all utilities share the same call signature
- the outputs are already on comparable scales, or you normalize them first
- you want `learner.query(..., return_metrics=True)` to preserve the selector values

## 2) Combine learner and density signals

`information_density` only needs `X`, so wrap it before combining it with a learner-based utility.

```python
from modAL.density import information_density
from modAL.uncertainty import classifier_margin
from modAL.utils.combination import make_linear_combination, make_query_strategy
from modAL.utils.selection import multi_argmax


def density_only(_, X):
    return information_density(X)


def top1_selector(values):
    return multi_argmax(values, n_instances=1)

margin_plus_density = make_linear_combination(
    lambda learner, X: 1.0 - classifier_margin(learner, X),
    density_only,
    weights=[0.6, 0.4],
)

margin_density_strategy = make_query_strategy(margin_plus_density, top1_selector)
```

This is a good fit when you want a synthetic case such as a combined margin+density strategy.

## 3) Freeze ranked-batch parameters

`uncertainty_batch_sampling` accepts `n_instances`, `metric`, and `n_jobs` directly. If you want a reusable configuration, close over those values.

```python
from functools import partial
from modAL.batch import uncertainty_batch_sampling

preset_batch = partial(
    uncertainty_batch_sampling,
    n_instances=3,
    metric='euclidean',
    n_jobs=1,
)
```

Use this pattern when:
- you want the batch size to stay fixed
- you want the same distance metric in every query
- you need deterministic local execution on CPU-only data

Remember:
- the batch helper returns `(indices, uncertainty_scores)`
- if the learner has no training data yet, the helper cold-starts from the most central pool instance

## 4) Use density as a standalone inspection metric

```python
from scipy.spatial.distance import euclidean
from modAL.density import information_density, similarize_distance

cosine_like = information_density(X_pool)
euclidean_like = information_density(X_pool, similarize_distance(euclidean))
```

Use `similarize_distance` when a custom distance is easier to express than a similarity.

## 5) Multilabel strategy recipes

`SVM_binary_minimum` needs the underlying binary estimators to expose `decision_function`. The probability-based multilabel scorers need `predict_proba` and `predict`.

```python
from modAL.multilabel import SVM_binary_minimum, max_loss
from modAL.models import ActiveLearner
from sklearn.multiclass import OneVsRestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import LinearSVC

svm_learner = ActiveLearner(
    estimator=OneVsRestClassifier(LinearSVC(dual=False, max_iter=5000, random_state=0)),
    query_strategy=SVM_binary_minimum,
    X_training=X_train,
    y_training=y_train,
)

query_idx, query_row = svm_learner.query(X_pool)

prob_model = OneVsRestClassifier(GaussianNB())
prob_model.fit(X_train, y_train)
query_idx, query_metric = max_loss(prob_model, X_pool, n_instances=2, random_tie_break=False)
```

## 6) Selector discipline

- Use `multi_argmax` / `multi_argmin` when you want both indices and the selected values.
- Use `weighted_random` when you want stochastic exploration and only need indices.
- If your selector returns only indices, `BaseLearner.query(..., return_metrics=True)` cannot invent metrics.
- A scalar index from a strategy will usually produce a 1-D sample row from `retrieve_rows`; an index array preserves batch shape.

## 7) When to stop and route elsewhere

- If you still need the learner or committee object, switch to `../../learners-and-committees/SKILL.md`.
- If the strategy is really an acquisition function, switch to `../../bayesian-optimization/SKILL.md`.
- If the strategy depends on MC dropout or another optional deep backend, switch to `../../deep-and-optional-integrations/SKILL.md`.
