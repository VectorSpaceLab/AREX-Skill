# Model Artifacts

pyAudioAnalysis classification and regression training APIs serialize pickle artifacts directly to paths derived from `model_name`. Treat every `model_name` as an output prefix, not just a display name.

## Classifier artifacts

### kNN classifiers

Training with `classifier_type="knn"` writes one file:

```text
<model_name>
```

That single pickle stream contains, in order:

1. normalized training feature matrix
2. numeric labels
3. feature means
4. feature standard deviations
5. class names
6. selected neighbor count
7. mid-term window
8. mid-term step
9. short-term window
10. short-term step
11. `compute_beat`

`file_classification(..., model_type="knn")` expects this single file.

### SVM and tree classifiers

Training with `svm`, `svm_rbf`, `randomforest`, `gradientboosting`, or `extratrees` writes two files:

```text
<model_name>
<model_name>MEANS
```

- `<model_name>` is a pickle of the trained estimator.
- `<model_name>MEANS` stores the scaler mean/std vectors, class names, window parameters, and `compute_beat` flag.

Move, copy, checksum, or delete these two files together. Inference may pass the initial model existence check and then fail later if the `MEANS` companion file is missing.

## Regression artifacts

`feature_extraction_train_regression(...)` writes one model pair for each CSV target in the training folder:

```text
<model_name>_<target>
<model_name>_<target>MEANS
```

For example, `model_name="models/emotion"` and CSV files `arousal.csv` and `valence.csv` create:

```text
models/emotion_arousal
models/emotion_arousalMEANS
models/emotion_valence
models/emotion_valenceMEANS
```

`file_regression(input_file, model_name, model_type)` discovers targets by globbing `model_name + "_*"` and ignoring files ending in `MEANS`. It derives the displayed target name from the text after the last underscore in each discovered model filename.

Operational consequences:

- Keep each target model file with its `MEANS` companion.
- Avoid target CSV stems with underscores if downstream code relies on the returned `regression_names` exactly.
- Do not rely on glob order for user-facing display; map or sort by returned target names in your own code.
- If no concrete target model exists, `file_regression` can fail before a helpful diagnostic.

## Naming and isolation rules

Use an explicit output directory and a unique prefix per experiment:

```python
from pathlib import Path

model_dir = Path("models") / "run-2026-01-15"
model_dir.mkdir(parents=True, exist_ok=True)
model_prefix = str(model_dir / "speech_music_svm")
```

Avoid:

- Reusing the same `model_name` for incompatible model types.
- Training a new model over an old prefix without removing stale companion files.
- Writing model prefixes into a source-controlled package directory unless that is intentional.
- Passing a directory path as `model_name`; it must be a file prefix.

The package does not create missing parent directories for model files. Create them before training.

## Compatibility and safety

The artifacts are Python pickles. Load them only from trusted training runs.

Compatibility can be affected by:

- Python version.
- scikit-learn version.
- numpy/scipy version.
- pyAudioAnalysis model serialization order.
- Model type mismatch between training and inference.

For durable experiments, record alongside the artifacts:

```text
pyAudioAnalysis version
Python version
numpy/scipy/scikit-learn/imblearn versions
classifier or regression model_type
mid_window, mid_step, short_window, short_step
compute_beat value
class folder names or regression CSV targets
training data manifest or checksum
```

Do not edit the pickle streams manually. Retrain instead.

## Side effects to plan for

| Operation | Side effect |
| --- | --- |
| classifier training | writes model pickle files; prints validation tables |
| regression training | writes one model pair per CSV; prints validation diagnostics |
| classifier evaluation with `plot=True` | writes `temp.html` in the current working directory and may open it |
| `file_regression` | reads all files matching `model_name + "_*"`; stale model files can create unexpected outputs |
| model overwrite | existing files with the same prefix are replaced without a high-level confirmation prompt |

## Cleaning up safely

Before deleting a classifier model, remove the complete artifact set:

```python
from pathlib import Path

prefix = Path("models/speech_music_svm")
for suffix in ["", "MEANS"]:
    path = Path(str(prefix) + suffix)
    if path.exists():
        path.unlink()
```

For regression prefixes, delete all matching target model files and their `MEANS` companions only when you are sure no unrelated file uses the same prefix.
