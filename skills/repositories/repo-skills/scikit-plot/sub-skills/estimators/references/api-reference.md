# API reference

Source anchors: `scikitplot/estimators.py`, `docs/estimators.rst`, `docs/functionsapidocs.rst`, `scikitplot/tests/test_estimators.py`, `examples/plot_feature_importances.py`, `examples/plot_learning_curve.py`.

## `plot_feature_importances`

```python
plot_feature_importances(
    clf,
    title='Feature Importance',
    feature_names=None,
    max_num_features=20,
    order='descending',
    x_tick_rotation=0,
    ax=None,
    figsize=None,
    title_fontsize='large',
    text_fontsize='medium',
) -> matplotlib.axes.Axes
```

- `clf` must already expose `feature_importances_`.
- Tree ensembles may also expose `estimators_`; when each sub-estimator has `feature_importances_`, the plot adds per-feature standard-deviation bars.
- `feature_names` is optional; when provided, it is reordered to match the sorted importances.
- `order` accepts `descending` (default), `ascending`, or `None`; any other value raises `ValueError`.
- `max_num_features` is clipped to the available number of importances.
- `ax` is optional; if omitted, the function creates a new figure and axes.
- The function returns the same `Axes` that it draws on.

## `plot_learning_curve`

```python
plot_learning_curve(
    clf,
    X,
    y,
    title='Learning Curve',
    cv=None,
    shuffle=False,
    random_state=None,
    train_sizes=None,
    n_jobs=1,
    scoring=None,
    ax=None,
    figsize=None,
    title_fontsize='large',
    text_fontsize='medium',
) -> matplotlib.axes.Axes
```

- `clf` is passed to `sklearn.model_selection.learning_curve`; use a cloneable sklearn-style estimator with the required fit/predict behavior.
- `X` and `y` are forwarded unchanged to `learning_curve`.
- `cv` can be an int, a cross-validation splitter, or an iterable of train/test splits.
- `shuffle` and `random_state` are forwarded to `learning_curve` and control the learning-curve sampling behavior.
- `train_sizes=None` defaults to `numpy.linspace(.1, 1.0, 5)`.
- `n_jobs` and `scoring` are forwarded unchanged.
- The plot shows mean training and cross-validation scores with standard-deviation bands.
- The function returns the same `Axes` that it draws on.

## Boundary notes

- Metric curves belong in `../../metrics/SKILL.md`.
- Elbow-curve workflows belong in `../../clustering/SKILL.md`.
- Bound-method wrappers belong in `../../legacy-factories/SKILL.md`.
