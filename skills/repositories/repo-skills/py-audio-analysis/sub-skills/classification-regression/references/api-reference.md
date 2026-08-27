# Classification and Regression API Reference

This reference distills pyAudioAnalysis 0.3.14 classification and regression behavior into operating guidance. It is self-contained; use installed package APIs rather than opening repository files.

## Import surface

```python
from pyAudioAnalysis import audioTrainTest as aT
```

`audioTrainTest` imports the package feature extraction and audio I/O modules internally. The backend requirement for the workflows here is CPU only. MP3 and some non-WAV media paths may additionally need a working media decoder such as ffmpeg through the package's audio I/O stack.

## Classifier training

```python
aT.extract_features_and_train(
    paths,
    mid_window,
    mid_step,
    short_window,
    short_step,
    classifier_type,
    model_name,
    compute_beat=False,
    train_percentage=0.9,
    dict_of_ids=None,
    use_smote=False,
)
```

### Inputs

| Argument | Meaning | Operating notes |
| --- | --- | --- |
| `paths` | List of class folders. | Each folder is one class; class names are derived from folder basenames in the order provided. Training scans common audio extensions including WAV, AIFF, MP3, AU, and OGG. |
| `mid_window`, `mid_step` | Mid-term window and step in seconds. | `1.0, 1.0` is the legacy default in the command wrapper. Use smaller values for short synthetic files, but keep files comfortably longer than the window. |
| `short_window`, `short_step` | Short-term feature window and step in seconds. | Package constants are `aT.shortTermWindow == 0.050` and `aT.shortTermStep == 0.050`. |
| `classifier_type` | Classifier identifier. | Supported classifier parser/code identifiers are `svm`, `svm_rbf`, `knn`, `randomforest`, `gradientboosting`, and `extratrees`. Validate before calling; unsupported strings can fail late. |
| `model_name` | Output model prefix/path. | This call writes files as a side effect; it does not return a model object. See `model-artifacts.md`. |
| `compute_beat` | Append beat features. | Requires beat extraction to work on the audio. Keep `False` for speech, short clips, or synthetic smoke tests unless beat features are part of the experiment. |
| `train_percentage` | Fraction used for train split during parameter evaluation. | The package performs repeated internal evaluation unless you use a custom bounded smoke helper. Small datasets can produce unstable validation splits. |
| `dict_of_ids` | Optional grouping map from full audio filename to group id. | Use to avoid leakage between related recordings; keys must exactly match the filenames discovered by feature extraction. |
| `use_smote` | Apply SMOTE during evaluation and final training. | Only use with enough minority-class samples for SMOTE neighbor requirements. Tiny class folders commonly fail. |

### Behavior

1. Extracts one long-term-averaged mid-term feature vector per audio file in each class folder.
2. Filters feature vectors with NaN or infinite values.
3. Evaluates a fixed parameter grid for the chosen classifier family.
4. Standardizes features with `StandardScaler`.
5. Trains the selected classifier and serializes model artifacts to `model_name`-derived files.

### Parameter grids used internally

| `classifier_type` | Parameter meaning | Candidate values |
| --- | --- | --- |
| `svm` | Linear SVC `C` | `0.001, 0.01, 0.5, 1.0, 5.0, 10.0, 20.0` |
| `svm_rbf` | RBF SVC `C`, `gamma='auto'` | `0.001, 0.01, 0.5, 1.0, 5.0, 10.0, 20.0` |
| `knn` | `K` neighbors for the package kNN wrapper | `1, 3, 5, 7, 9, 11, 13, 15` |
| `randomforest` | Number of trees | `10, 25, 50, 100, 200, 500` |
| `gradientboosting` | Number of estimators | `10, 25, 50, 100, 200, 500` |
| `extratrees` | Number of trees | `10, 25, 50, 100, 200, 500` |

## File classification

```python
class_id, probabilities, class_names = aT.file_classification(
    input_file,
    model_name,
    model_type,
)
```

| Return | Meaning |
| --- | --- |
| `class_id` | Integer index of the winning class. Convert with `class_names[int(class_id)]`. |
| `probabilities` | Probability-like vector ordered like `class_names`. For kNN this is the neighbor-vote fraction. |
| `class_names` | Class names serialized during training. |

Error behavior is legacy-style: missing input or unreadable audio can print a message and return `(-1, -1, -1)` instead of raising. For non-kNN model types, both `model_name` and `model_name + "MEANS"` must be present even though the initial existence check only checks `model_name`.

`model_type` must match the family used during training. Loading a `svm_rbf` model with `svm`, or a tree model with `knn`, is not a safe compatibility shortcut.

## Folder evaluation

```python
cm, thr_prre, pre, rec, thr_roc, fpr, tpr = aT.evaluate_model_for_folders(
    input_test_folders,
    model_name,
    model_type,
    positive_class,
    plot=True,
)
```

Use this for held-out class folders with the same one-folder-per-class layout as training.

- `positive_class` must be one of the serialized/derived class names.
- Set `plot=False` in headless jobs. With `plot=True`, the package writes `temp.html` in the current working directory and may try to open it.
- The returned `cm` is the confusion matrix. Precision/recall and ROC arrays are for the selected positive class.
- The function also prints the confusion matrix and aggregate metrics.

## Regression training

```python
errors, errors_base, best_params = aT.feature_extraction_train_regression(
    folder_name,
    mid_window,
    mid_step,
    short_window,
    short_step,
    model_type,
    model_name,
    compute_beat=False,
)
```

### Data layout

`folder_name` contains audio files plus one or more CSV files. Each CSV defines one regression target and contains rows:

```csv
filename.wav,numeric_value
another.wav,0.73
```

The filename field must match an audio filename basename discovered in `folder_name`. One CSV creates one regression output dimension/task.

### Supported regression model types

For training and file regression, use:

- `svm`
- `svm_rbf`
- `randomforest`

The legacy folder-regression CLI parser exposes `svm` and `knn`, but the underlying `file_regression(...)` implementation in this version only loads `svm`, `svm_rbf`, and `randomforest` regression artifacts correctly. Prefer the Python API above for regression.

### Return values

| Return | Meaning |
| --- | --- |
| `errors` | Validation absolute-error estimates per CSV target. |
| `errors_base` | Baseline errors per CSV target. |
| `best_params` | Selected hyperparameter per CSV target. |

Training serializes one model pair per CSV target; see `model-artifacts.md`.

## File regression

```python
values, regression_names = aT.file_regression(
    input_file,
    model_name,
    model_type,
)
```

- `model_name` is the prefix originally passed to `feature_extraction_train_regression(...)`.
- The function discovers concrete target models by globbing `model_name + "_*"` and excluding files ending in `MEANS`.
- `values` is a list of predictions, ordered like `regression_names`.
- `regression_names` are derived from the suffix after the last underscore in each model artifact name.
- Because discovery is glob-based, avoid underscores in target names when stable downstream parsing matters, and sort or map outputs by name in your own code if deterministic display order is required.

## Legacy CLI relation

The legacy `audioAnalysis.py` script wraps these APIs with tasks such as `trainClassifier`, `classifyFile`, `classifyFolder`, `trainRegression`, `regressionFile`, and `regressionFolder`. Its source uses top-level intra-package imports, so command-line execution needs the package directory importable as top-level modules or an execution mode documented by the `cli-and-io` sub-skill. Use this sub-skill for API behavior and model semantics; use `cli-and-io` for command syntax details.
