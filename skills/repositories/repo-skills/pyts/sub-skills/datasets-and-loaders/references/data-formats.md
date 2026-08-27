# Dataset Formats

## Bundled toy datasets

| Loader | Shape returned by `return_X_y=True` | Notes |
| --- | --- | --- |
| `load_coffee` | train `(100, 96)`, test `(100, 96)` | univariate, packaged in the repo |
| `load_gunpoint` | train `(50, 150)`, test `(150, 150)` | univariate, often used in examples |
| `load_pig_central_venous_pressure` | train `(104, 2000)`, test `(208, 2000)` | univariate, longer series |
| `load_basic_motions` | train `(40, 6, 100)`, test `(40, 6, 100)` | multivariate, use the multivariate sub-skill |

## Synthetic generator

`make_cylinder_bell_funnel(n_samples=12, random_state=0)` produces a univariate
feature matrix with shape `(12, 128)` and labels with shape `(12,)`.

## Return conventions

- Packaged loaders and fetchers return train/test splits when
  `return_X_y=True`.
- Use the multivariate sub-skill for any `3D` output such as BasicMotions.
- `fetch_ucr_dataset` and `fetch_uea_dataset` use dataset names and may return
  cached data or trigger a download depending on the environment.

## Notes for future agents

- Treat the `train/test` split as separate arrays, not as a single stacked
  matrix.
- Use the catalog helpers before remote fetches so you can fail fast on a bad
  dataset name.
- Keep the dataset-handling logic in this sub-skill; do not hide shape
  assumptions in the modeling sub-skills.
