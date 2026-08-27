# Workflows

## Feature-importance workflow

Use this route when the model is already fitted and you want to inspect which input features matter most.

1. Fit an estimator that exposes `feature_importances_`.
2. Keep feature names in input-feature order.
3. Choose the ranking rule:
   - `descending` for the most important features first.
   - `ascending` for the least important features first.
   - `None` to preserve the raw importance order.
4. Pass `ax=` when the plot needs to live inside a larger figure.
5. If the estimator is a tree ensemble, the plot can show error bars from the ensemble members automatically.

```python
import matplotlib.pyplot as plt
import scikitplot as skplt
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier

iris = load_iris()
clf = RandomForestClassifier(n_estimators=16, random_state=0, n_jobs=1)
clf.fit(iris.data, iris.target)

fig, ax = plt.subplots(figsize=(6, 4))
skplt.estimators.plot_feature_importances(
    clf,
    feature_names=iris.feature_names,
    max_num_features=4,
    order='descending',
    ax=ax,
)
```

## Learning-curve workflow

Use this route when you want to compare training and validation scores as the sample size increases.

1. Choose a cloneable sklearn-style estimator with fit/predict behavior.
2. Decide on the validation policy:
   - `cv` for the split strategy.
   - `shuffle` and `random_state` for reproducible sampling.
   - `train_sizes` for the subset schedule.
   - `scoring` for the metric.
3. Pass `ax=` if you are composing multiple panels.
4. Read the red line as the training score and the green line as the cross-validation score.

```python
import matplotlib.pyplot as plt
import numpy as np
import scikitplot as skplt
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier

X, y = load_breast_cancer(return_X_y=True)
fig, ax = plt.subplots(figsize=(6, 4))
skplt.estimators.plot_learning_curve(
    RandomForestClassifier(n_estimators=16, random_state=0, n_jobs=1),
    X,
    y,
    cv=3,
    shuffle=True,
    random_state=0,
    train_sizes=np.linspace(0.3, 1.0, 3),
    scoring='accuracy',
    ax=ax,
)
```

## Axes reuse pattern

When you already own the figure, always pass the axes back in and keep the returned axes object for chaining.

```python
fig, ax = plt.subplots()
out_ax = skplt.estimators.plot_learning_curve(..., ax=ax)
assert out_ax is ax
```

## When to reroute

- Confusion matrix, ROC, precision-recall, KS, calibration, cumulative gain, lift, or silhouette: use `../../metrics/SKILL.md`.
- Elbow-curve or cluster-score workflows: use `../../clustering/SKILL.md`.
- Legacy injected methods on an estimator instance: use `../../legacy-factories/SKILL.md`.
