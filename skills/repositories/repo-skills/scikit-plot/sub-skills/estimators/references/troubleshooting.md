# Troubleshooting

If the import fails before either plot runs, fix the runtime first. This repository was verified against the pinned compatibility window `scipy<1.11` and `matplotlib<3.9`.

## Failure surfaces

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `TypeError: "feature_importances_" attribute not in classifier. Cannot plot feature importances.` | The estimator has not been fitted to a model that exposes `feature_importances_`, or the estimator simply does not provide that attribute. | Fit a compatible tree-based estimator or switch to another route. |
| `ValueError: Invalid argument ... for "order"` | `order` is not one of the supported values. | Use `ascending`, `descending`, or `None`. |
| Learning-curve errors about cloning, fitting, or prediction | The estimator does not satisfy the sklearn interface expected by `learning_curve`, or the target/scoring choice is incompatible with the estimator. | Use a cloneable sklearn-style estimator with `fit`/`predict`, and make the scorer match the task. |
| Errors about `cv` or `scoring` | The cross-validation input or scorer is malformed. | Pass a valid CV integer, splitter, or iterable, and use a valid sklearn scorer string or callable. |
| The plot appears on a new figure instead of the one you expected | `ax` was omitted or a `Figure` was passed where an `Axes` was expected. | Create `fig, ax = plt.subplots()` and pass `ax=ax`; keep the returned axes object. |

## Recovery checklist

1. Verify the estimator is fitted and exposes the expected attribute or sklearn interface.
2. Recheck `order`, `cv`, `shuffle`, `random_state`, `train_sizes`, `n_jobs`, and `scoring`.
3. Reuse an explicit `Axes` if the plot must land in a specific subplot.
4. If the problem happens at import time, repair the pinned environment before debugging the plot call.
