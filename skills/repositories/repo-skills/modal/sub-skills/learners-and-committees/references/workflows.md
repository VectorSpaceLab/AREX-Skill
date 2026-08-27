# Workflows

## 1) ActiveLearner: pool-based classification

Use this when you have a classifier with `fit`, `predict`, and usually `predict_proba`.

### Minimal lifecycle

1. Build a labeled seed set `X_training`, `y_training`.
2. Create the learner.
3. Query the pool.
4. Teach the newly labeled row.
5. Repeat until the budget is exhausted.
6. Use `fit()` only when you want to replace the stored history.

```python
from modAL.models import ActiveLearner
from modAL.uncertainty import uncertainty_sampling

learner = ActiveLearner(
    estimator=estimator,
    query_strategy=uncertainty_sampling,
    X_training=X_training,
    y_training=y_training,
    bootstrap_init=True,
)

query_idx, query_rows, metrics = learner.query(X_pool, return_metrics=True)
X_new = X_pool[query_idx[0]].reshape(1, -1)
y_new = y_pool[query_idx[0]].reshape(1,)
learner.teach(X_new, y_new)
```

### What to remember

- `query()` returns the selected indices plus the matching rows from `X_pool`.
- If the query strategy reports metrics, `return_metrics=True` returns them as a third item.
- If the strategy does not report metrics, the learner warns and returns `None` for the metrics slot.
- `teach()` appends to stored training history by default.
- `teach(..., bootstrap=True)` refits on a bootstrap sample of the stored history.
- `teach(..., only_new=True)` fits only on the new batch and does not extend the stored history.
- `fit()` replaces the stored history.

## 2) ActiveLearner: stream-based sampling

Use this when samples arrive one at a time and you only label the uncertain ones.

```python
from modAL.uncertainty import classifier_uncertainty

uncertainties = classifier_uncertainty(learner, X_stream)
threshold = float(np.median(uncertainties))

for row, label, uncertainty in zip(X_stream, y_stream, uncertainties):
    if uncertainty >= threshold:
        learner.teach(row.reshape(1, -1), np.array([label]))
```

### Shape rules

| Situation | Safe shape |
| --- | --- |
| Single NumPy feature row | `X_pool[idx].reshape(1, -1)` |
| Single DataFrame feature row | `X_pool.iloc[[idx]]` |
| Single NumPy label | `np.array([label])` or `y_pool[idx].reshape(1,)` |
| Single DataFrame label row | `y_pool.iloc[[idx]]` |

Keep the new row shape consistent with the original training data. If the estimator expects a 2D target array, keep the label in that form.

## 3) Pipeline and `on_transformed`

Use `on_transformed=True` when the query strategy should work in feature space after preprocessing.

Typical pattern:

```python
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from modAL.batch import uncertainty_batch_sampling

learner = ActiveLearner(
    estimator=make_pipeline(
        StandardScaler(),
        PCA(n_components=2),
        LogisticRegression(max_iter=500, solver="liblinear"),
    ),
    query_strategy=uncertainty_batch_sampling,
    X_training=X_training,
    y_training=y_training,
    on_transformed=True,
)
```

Notes:
- The preprocessing part of the pipeline is applied without the final estimator.
- Use this only with query strategies that can work with transformed features.
- If the strategy should operate on raw `X`, leave `on_transformed` off.

## 4) Committee: query by committee and bagging

Use this when you want multiple learners voting on the same pool.

### Build and query

1. Create several `ActiveLearner` instances.
2. Put them in a list.
3. Build the `Committee`.
4. Query and teach the committee as a group.

```python
from modAL.models import Committee
from modAL.disagreement import vote_entropy_sampling

committee = Committee(
    learner_list=[learner_a, learner_b, learner_c],
    query_strategy=vote_entropy_sampling,
)

query_idx, query_rows, metrics = committee.query(X_pool, return_metrics=True)
committee.teach(X_new, y_new)
```

### Voting and class alignment

- `vote(X)` returns the raw learner predictions with shape `(n_samples, n_learners)`.
- `vote_proba(X)` returns class probabilities with shape `(n_samples, n_learners, n_classes)`.
- `predict_proba(X)` averages learner probabilities across the committee.
- `predict(X)` chooses the consensus class from the averaged probabilities.
- `Committee.classes_` is the union of learner class labels.
- Learners can see different class subsets; the committee aligns probabilities automatically.

### Bagging

Use the bootstrap surfaces rather than a nonexistent `bag()` method.

- `bootstrap_init=True` on a learner bootstraps the first fit.
- `committee.teach(..., bootstrap=True)` bootstraps the refit.
- `committee.rebag()` refits each learner on a bootstrap sample of its own stored history.

## 5) CommitteeRegressor

Use this for ensemble regression and query-by-std selection.

```python
from modAL.models import CommitteeRegressor
from modAL.disagreement import max_std_sampling

committee = CommitteeRegressor(
    learner_list=[reg_1, reg_2, reg_3],
    query_strategy=max_std_sampling,
)

mean, std = committee.predict(X_pool, return_std=True)
query_idx, query_rows, metrics = committee.query(X_pool, return_metrics=True)
```

### Notes

- `predict(X)` returns the ensemble mean.
- `predict(X, return_std=True)` returns `(mean, std)` across learner predictions.
- `vote(X)` returns the raw learner predictions with shape `(n_samples, n_learners)`.
- There is no `predict_proba()` on `CommitteeRegressor`.
- `max_std_sampling` ranks samples by the ensemble standard deviation, not by class probabilities.

## 6) Decision guide

| Need | Use |
| --- | --- |
| Query a classifier pool | `ActiveLearner` + an uncertainty strategy |
| Query a stream with a confidence threshold | `classifier_uncertainty()` + `teach()` |
| Rebuild a learner from scratch | `fit()` |
| Keep the old history but teach only the latest batch | `teach(..., only_new=True)` |
| Build a voting ensemble | `Committee` |
| Build a regression ensemble | `CommitteeRegressor` |
| Refit the ensemble on bootstrapped history | `rebag()` |
