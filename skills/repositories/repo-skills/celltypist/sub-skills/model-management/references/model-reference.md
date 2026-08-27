# Model Reference

This reference covers CellTypist 1.7.1 model discovery, cache behavior, local model persistence, prediction behavior, and marker extraction.

## Cache Layout

CellTypist creates its model cache when `celltypist.models` is imported.

- `CELLTYPIST_FOLDER` controls the cache root when set before import.
- Without `CELLTYPIST_FOLDER`, CellTypist uses a `.celltypist` directory under the current user's home directory.
- Built-in model files live under `data/models/` inside that root.
- `celltypist.models.models_path` is the active model directory for the current Python process.
- `celltypist.models.get_model_path("Name.pkl")` returns the active-cache path for one model or `models.json`.

Set `CELLTYPIST_FOLDER` before Python imports CellTypist if you need a non-default cache:

```bash
CELLTYPIST_FOLDER=/project/celltypist-cache python -c "from celltypist import models; print(models.models_path)"
```

Do not assume changing `os.environ["CELLTYPIST_FOLDER"]` after `from celltypist import models` will move the already-imported module's `models_path`.

## Remote Model Index and Downloads

Verified functions:

```python
from celltypist import models

models.models_description(on_the_fly=False)
models.download_models(force_update=False, model=None)
models.get_default_model()
models.get_all_models()
```

Network-sensitive behavior:

- `models.download_models()` fetches `models.json` when missing, then downloads all models listed in the index unless `model=` restricts the list.
- `models.download_models(model="Immune_All_Low.pkl")` downloads only matching names from the index.
- `force_update=True` re-fetches the index and re-downloads requested model files instead of skipping existing files.
- `models.models_description(on_the_fly=False)` reads `models.json`; if it is absent it fetches the remote index.
- `models.models_description(on_the_fly=True)` calls `get_all_models()`, which downloads all models when no `.pkl` files are present in the cache.
- `models.get_default_model()` reads `models.json`; if it is absent it fetches the remote index.
- `models.get_all_models()` calls `download_if_required()`, which downloads all models when the cache contains no `.pkl` files.

Use [model_cache_check.py](../scripts/model_cache_check.py) for offline cache inventory instead of `get_all_models()`, `get_default_model()`, or `models_description()` when the cache may be empty.

## Loading Models Safely

Verified signature:

```python
celltypist.models.Model.load(model: Optional[str] = None)
```

Behavior:

- `model=None` resolves through `get_default_model()`, so it can fetch `models.json` in a fresh cache.
- A built-in model name such as `"Immune_All_Low.pkl"` is accepted when it appears in the model inventory; if no local models are present, inventory lookup can download models.
- A path containing `/`, such as `"./local.pkl"`, `"models/local.pkl"`, or an absolute path, is treated as a direct file path and avoids built-in inventory lookup.
- A bare local filename with no slash and no matching built-in inventory entry is checked as a filesystem path only after `get_all_models()` has run, so it is not strict-offline safe in an empty cache.
- Missing files raise `FileNotFoundError`.
- Invalid pickle contents raise an `Exception` with an `Invalid model` message.

Offline-safe pattern:

```python
from pathlib import Path
from celltypist import models

model = models.Model.load(Path("local_model.pkl").resolve().as_posix())
```

A valid model pickle contains a dictionary with these keys:

- `Model`: a fitted sklearn-style classifier with `classes_`, `coef_`, `intercept_`, `features`, and `decision_function()`.
- `Scaler_`: a fitted `StandardScaler`-style object with `mean_`, `var_`, `scale_`, and `n_features_in_`.
- `description`: a dictionary containing at least `date`, `details`, `url`, `source`, and `version`; `number_celltypes` is also commonly present.

## Inspecting and Writing Models

Useful `Model` attributes and methods:

```python
model.cell_types        # numpy array from model.classifier.classes_
model.features          # numpy array from model.classifier.features
model.description       # metadata dictionary
model.write("out.pkl")  # writes a CellTypist-compatible pickle
```

`Model.write(file)` always writes a `.pkl` path by replacing the supplied suffix with `.pkl`. For example, `model.write("converted")` and `model.write("converted.txt")` both produce a pickle path ending in `converted.pkl`.

Keep user-facing model files in a project-controlled path or the active `models.models_path`. For reproducible offline examples, prefer a relative or absolute local path and pass that path explicitly to annotation.

## Prediction Labels and Probabilities

Verified signature:

```python
model.predict_labels_and_prob(indata, mode="best match", p_thres=0.5) -> tuple
```

Behavior:

- `indata` must already be scaled/aligned the way CellTypist annotation prepares it; normal annotation workflows should call `celltypist.annotate()` rather than this method directly.
- The method returns `(decision_scores, probabilities, labels)`.
- For binary classifiers, one-dimensional sklearn decision scores are expanded to two columns as `[-score, score]`.
- Probabilities are `scipy.special.expit(decision_scores)`, not a softmax whose rows sum to 1.
- `mode="best match"` assigns each row to the class with the largest decision score.
- `mode="prob match"` assigns all classes whose probability is greater than `p_thres`, joins multiple labels with `|`, and uses `Unassigned` when none pass.
- Any other `mode` raises a `ValueError`.

Route full input normalization, model-feature alignment, majority voting, result tables, and CLI annotation to [annotation-workflows](../../annotation-workflows/SKILL.md).

## Marker Extraction

Verified signature:

```python
model.extract_top_markers(cell_type, top_n=10, only_positive=True)
```

Behavior:

- `cell_type` must exactly match one of `model.cell_types`.
- For binary models, markers for the second class use the classifier coefficient vector and markers for the first class use its negation.
- For multiclass models, markers use the row of `classifier.coef_` corresponding to the requested class.
- With `only_positive=True`, markers are sorted by largest positive coefficient.
- With `only_positive=False`, markers are sorted by largest absolute coefficient, so negative markers may be included.
- The return value is a NumPy array of feature names from `model.features`.

Example:

```python
markers = model.extract_top_markers("T cells", top_n=20, only_positive=True)
```

If the task is to interpret marker biology or visualize marker-level outputs after annotation, route downstream presentation work to [visualization-and-results](../../visualization-and-results/SKILL.md).
