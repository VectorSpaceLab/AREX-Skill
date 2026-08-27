# Classification and Regression Troubleshooting

## Fast diagnosis table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `trainSVM_feature ERROR: No data found in any input folder!` | Class folders are empty, paths are wrong, files are unsupported/unreadable, or all files were skipped. | Verify one-folder-per-class layout, use WAV for diagnosis, ensure clips are non-empty and longer than about 0.2 s. |
| `folder is empty or non-existing!` | A path in `paths` has no usable files after feature extraction. | Check spelling, trailing separators, and file extensions. |
| Training returns without model files | Legacy API prints an error and returns instead of raising. | Check for expected artifacts from `model-artifacts.md` immediately after training and fail explicitly if missing. |
| `fileClassification: input model_name not found!` | `model_name` does not point to the saved model prefix. | Pass the same prefix used during training; do not add `MEANS` manually. |
| `fileClassification: wav file not found!` | Inference input path is wrong or file was removed. | Validate the input file before calling `file_classification` or `file_regression`. |
| Inference raises missing `MEANS` file | Non-kNN companion artifact is absent. | Move/copy `<model_name>` and `<model_name>MEANS` together. |
| Wrong class names or surprising winner | Class folder order/names changed, stale model prefix reused, or model type mismatch. | Use unique output prefixes and inspect returned `class_names`. Match `model_type` to the training call. |
| `positive_class` error or metric failure in evaluation | `positive_class` is not in serialized class names or held-out folders lack that class. | Use one returned class name exactly, including case and punctuation. |
| `ValueError` from SMOTE | Too few minority-class samples for SMOTE neighbor requirements. | Disable `use_smote` for tiny data or add enough files per class before enabling it. |
| `ValueError` from train/test split or metrics | Dataset is too small, a split misses a class, or only one class has usable samples. | Add files per class, reduce test demands only for smoke tests, or use grouped splits carefully. |
| `NaN Found! Feature vector not used for training` | Audio produced invalid feature values, often from silence/constant signals or decode problems. | Remove silent/broken files, normalize input audio, or inspect raw feature extraction via `feature-extraction`. |
| Probability vector has unexpected scale for kNN | kNN probability is a neighbor-vote fraction based on selected `K`. | Treat it as relative confidence, not calibrated probability. |
| Regression returns no targets or crashes | No `<model_name>_*` target artifacts exist, CSV names mismatch audio basenames, or stale files conflict. | Check CSV rows, train output pairs, and remove stale artifacts sharing the prefix. |
| Regression target names are truncated | Target artifact names are parsed after the last underscore. | Avoid underscores in CSV stems when target names matter. |
| `plot=True` hangs or opens a browser | Evaluation creates an interactive Plotly HTML file. | Use `plot=False` in non-interactive sessions. |
| MP3 files fail or are skipped | Optional decoder stack is unavailable. | Convert to WAV or install/configure the required media decoder in the runtime environment. |
| Importing legacy CLI module fails on sibling imports | The CLI script uses top-level imports for sibling modules. | Prefer package APIs here; route CLI execution details to `cli-and-io`. |

## Class folder layout checks

Before training a classifier, assert:

```python
from pathlib import Path

class_dirs = [Path("training-data/speech"), Path("training-data/music")]
for d in class_dirs:
    assert d.is_dir(), f"missing class folder: {d}"
    usable = [p for p in d.iterdir() if p.suffix.lower() in {".wav", ".aif", ".aiff", ".mp3", ".au", ".ogg"}]
    assert usable, f"no candidate audio files in {d}"
```

Use folder basenames intentionally; they become class labels.

## Tiny datasets and smoke tests

The public training wrapper performs internal parameter evaluation. On tiny datasets this can be slow or statistically unstable because the package auto-computes many repetitions and random splits. For production training, add data. For a bounded install smoke test, use `../scripts/classification_smoke.py`, which deliberately replaces the expensive parameter selector with a fixed selector while still exercising feature extraction, serialization, and file classification.

## Unsupported or mismatched model types

Classifier identifiers:

```text
svm, svm_rbf, knn, randomforest, gradientboosting, extratrees
```

Regression identifiers for training and file inference:

```text
svm, svm_rbf, randomforest
```

Common mistakes:

- `randomforests` instead of `randomforest`.
- Training with `svm_rbf` and loading with `svm`.
- Expecting kNN regression to work because a legacy folder parser exposes it.
- Reusing an old prefix whose artifacts were created with a different model family.

## Beat features

`compute_beat=True` appends beat and beat-confidence features during training and stores that flag in the model metadata. Inference uses the stored flag and extracts the same extra dimensions.

Use `compute_beat=False` when:

- Clips are short.
- The task is speech/event classification rather than rhythm/music analysis.
- You need fast synthetic or CI smoke tests.
- Beat extraction produces unstable or invalid features.

If you retrain with a different `compute_beat` setting, use a new model prefix.

## Pickle compatibility and security

Do not load model artifacts from untrusted sources. Pickle loading can execute code.

If a model that used to work fails after dependency changes:

1. Recreate the original package/dependency versions if they were recorded.
2. If that is not possible, retrain from data with the current environment.
3. Do not mix old estimator pickles with newly generated `MEANS` files.

## scikit-learn and dependency warnings

Expected warning categories include:

- convergence or probability calibration warnings from SVMs on small/noisy data;
- metrics warnings when a class has no predicted samples;
- deprecation or pickle compatibility warnings across scikit-learn versions.

Warnings in a smoke test are not automatically fatal if the final JSON reports the expected class. Warnings in real training should be reviewed with held-out evaluation before accepting the model.

## Model output side effects

Training overwrites existing artifact paths. Protect previous runs by creating a fresh output directory per experiment or deleting a known complete artifact set before retraining.

For non-kNN classifiers:

```text
<model_name>
<model_name>MEANS
```

For regression:

```text
<model_name>_<target>
<model_name>_<target>MEANS
```

Never clean up by deleting only files ending in `MEANS`; the estimator files would become stale or orphaned.
