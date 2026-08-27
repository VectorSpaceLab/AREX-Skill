# LightFM troubleshooting

Use this reference for cross-cutting LightFM failures before routing into a deeper sub-skill.

## Install or import fails

### Symptoms

- `ModuleNotFoundError: No module named 'lightfm'`
- `ImportError` from `lightfm._lightfm_fast` or a platform compiler/linker error during install
- `pip check` reports incompatible runtime dependencies

### Recovery

1. Install in an isolated Python environment, not a system Python:

   ```bash
   python -m pip install lightfm
   python -c "import lightfm; print(lightfm.__version__)"
   ```

2. Run the bundled diagnostic:

   ```bash
   python scripts/check_lightfm_environment.py --tiny-run
   ```

3. If maintaining a source checkout or diagnosing compiled extensions, route to [`repo-development`](../sub-skills/repo-development/SKILL.md). It covers OpenMP/no-OpenMP variants, Cython regeneration, `LIGHTFM_NO_CFLAGS`, focused tests, and platform-specific build behavior.

## GPU or accelerator expectations

LightFM has no GPU implementation. If a user asks to make LightFM use CUDA, ROCm, MPS, TPU, or another accelerator:

- State that LightFM training and inference are CPU-only.
- Explain that OpenMP only affects CPU multithreading.
- Use `num_threads` for CPU parallelism where appropriate.
- Do not install GPU framework packages solely for LightFM.

## Built-in dataset downloads fail

### Symptoms

- `requests`/HTTP failures while calling `fetch_movielens` or `fetch_stackexchange`
- `IOError` because `download_if_missing=False` and the cache is empty
- `ValueError: Corrupted Movielens download...`

### Recovery

1. Prefer deterministic local fixtures for skill checks:

   ```bash
   python sub-skills/model-training/scripts/tiny_lightfm_smoke.py
   python sub-skills/evaluation-splitting/scripts/evaluate_lightfm_fixture.py
   ```

2. For package use, set an explicit cache and decide whether downloads are allowed:

   ```python
   from lightfm.datasets import fetch_movielens

   data = fetch_movielens(data_home="lightfm_data", download_if_missing=True)
   ```

3. If offline, set `download_if_missing=False` and provide a pre-populated cache. Route custom local data conversion to [`data-features`](../sub-skills/data-features/SKILL.md).

## Feature schema or shape errors

### Symptoms

- `Number of user feature rows does not equal the number of users`
- `Number of item feature rows does not equal the number of items`
- `The user/item feature matrix specifies more features than there are estimated feature embeddings`
- Feature-normalization failures for zero rows

### Recovery

1. Route to [`data-features`](../sub-skills/data-features/SKILL.md) and verify `Dataset.interactions_shape()`, `user_features_shape()`, `item_features_shape()`, `model_dimensions()`, and `mapping()`.
2. Preserve the same feature column vocabulary between `fit`, `fit_partial`, `predict`, `predict_rank`, and metrics.
3. If adding new feature names after fitting, retrain or explicitly rebuild the model with the expanded dimensions.
4. If identity features are disabled, ensure every row has at least one nonzero feature when building normalized feature matrices.

## Evaluation scores look too good or metric calls fail

### Symptoms

- `ValueError` about train/test interactions sharing entries
- Test precision/AUC is implausibly high
- Metric arrays have unexpected length or zeros for many users

### Recovery

1. Route to [`evaluation-splitting`](../sub-skills/evaluation-splitting/SKILL.md).
2. Keep `check_intersections=True` unless intentionally diagnosing training-set ranking.
3. Pass `train_interactions=train` when evaluating held-out test positives.
4. Use `preserve_rows=True` only when downstream code needs one output value per original user row.

## Model training diverges or recommendations collapse

### Symptoms

- `Not all estimated parameters are finite`
- NaN/Inf input failures
- Very slow WARP epochs
- Same popular items recommended to everyone

### Recovery

1. Route to [`model-training`](../sub-skills/model-training/SKILL.md).
2. Check interactions and feature matrices for NaN/Inf values before fitting.
3. Reduce `learning_rate`, reduce feature magnitudes, or lower sample weights for divergence.
4. Tune `item_alpha`/`user_alpha`, `no_components`, and epochs for overfitting or underfitting.
5. For popularity collapse, inspect item biases, metadata quality, and whether identity features should be retained or disabled for the use case.
