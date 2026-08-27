# Task API Workflows

These workflows use synthetic data only. They avoid external dataset downloads and avoid running repository examples as runtime dependencies. For a quick environment/API probe, use the bundled scripts with `--dry-run` first.

## Environment preflight

Set the Keras backend before importing Keras or AutoKeras:

```python
import os
os.environ.setdefault("KERAS_BACKEND", "torch")
import keras, autokeras as ak
print("AutoKeras", ak.__version__)
print("Backend", keras.backend.backend())
```

## Image classification

```python
import tempfile, numpy as np, autokeras as ak
rng = np.random.default_rng(5)
x = rng.random((8, 28, 28), dtype=np.float32)
y = np.array([0, 1, 0, 1, 0, 1, 0, 1])
clf = ak.ImageClassifier(max_trials=1, overwrite=True, directory=tempfile.mkdtemp(), seed=5)
clf.fit(x, y, epochs=1, validation_split=0.25, batch_size=2)
print(clf.predict(x[:2], verbose=0).shape)
```

For RGB images, use `(samples, width, height, channels)`.

## Text classification

```python
import tempfile, numpy as np, autokeras as ak
x = np.array(["bright calm movie", "dull noisy movie", "happy short story", "sad weak story"] * 2)
y = np.array([1, 0, 1, 0] * 2)
clf = ak.TextClassifier(max_trials=1, overwrite=True, directory=tempfile.mkdtemp(), seed=5)
clf.fit(x, y, epochs=1, validation_split=0.25, batch_size=2)
print(clf.predict(x[:2], verbose=0).shape)
```

Text inputs should be one-dimensional strings.

## Structured-data classification

```python
import tempfile, numpy as np, autokeras as ak
column_names = ["age", "fare", "ticket_class", "embark_town"]
column_types = {"age": "numerical", "fare": "numerical", "ticket_class": "categorical", "embark_town": "categorical"}
x = np.array([[22.0, 7.25, "third", "S"], [38.0, 71.28, "first", "C"], [26.0, 7.93, "third", "S"], [35.0, 53.10, "first", "S"]] * 2, dtype=object)
y = np.array([0, 1, 1, 1] * 2)
clf = ak.StructuredDataClassifier(column_names=column_names, column_types=column_types, max_trials=1, overwrite=True, directory=tempfile.mkdtemp(), seed=5)
clf.fit(x, y, epochs=1, validation_split=0.25, batch_size=2)
print(clf.predict(x[:2], verbose=0).shape)
```

## Regression variants

Use `ak.ImageRegressor`, `ak.TextRegressor`, or `ak.StructuredDataRegressor` with numeric targets. Set `output_dim=1` when a scalar target needs to be explicit.

## Bundled helper examples

From the sub-skill directory:

```bash
python scripts/run_tiny_image_task.py --help
python scripts/run_tiny_image_task.py --task classifier --dry-run
python scripts/run_tiny_text_task.py --task regressor --dry-run
python scripts/run_tiny_structured_task.py --task classifier --dry-run
```

Add `--run-fit` only when a tiny local training smoke is acceptable.
