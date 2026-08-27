# Troubleshooting datasets and metrics

Start with the bundled synthetic smoke before debugging raw data or optional dependencies:

```bash
python scripts/metric_report_smoke.py --pretty
```

Run that command from this sub-skill directory, or pass the script path to Python from another working directory.

## Install/import issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'aif360'` | AIF360 is not installed in the active Python environment. | Install `aif360` into the active environment, then re-run a minimal import: `python -c "import aif360; print(aif360.__version__ if hasattr(aif360, '__version__') else 'aif360 imported')"`. |
| Import prints warnings about TensorFlow, fairlearn, inFairness, POT, or other extras | Optional algorithms/metrics are imported through package modules but their extras were not installed. | For this sub-skill, base dataset and legacy metric classes do not require those extras. Treat warnings as non-blocking unless the task explicitly needs the optional workflow. |
| `pip check` or dependency solver failures | Conflicting numpy/scipy/pandas/scikit-learn versions in a shared environment. | Use an isolated Python environment and install the package there. Avoid broad optional extras unless the task requires them. |
| A script imports from a local checkout accidentally | Running from inside a checkout can shadow the installed package. | For verification, run from a neutral working directory or inspect `aif360.__file__` only in private diagnostics. Do not bake private paths into runtime outputs. |

## Optional dependency issues

| Workflow | Extra / dependency | Status in this generated skill | Guidance |
| --- | --- | --- | --- |
| Base dataset and metric classes | Base install only | Verified for CPU import and synthetic metric smoke. | Safe to use without optional extras. |
| Optimal transport distance | `aif360[OptimalTransport]` / `pot` imported as `ot` | Optional and unverified. | Use only after installing the extra and running an OT-specific smoke. Prefer the sklearn-interface route for pandas OT metrics. |
| Algorithm-related warnings such as TensorFlow, torch, fairlearn, cvxpy, BlackBoxAuditing | Mitigation extras | Optional and unverified here. | Route to the mitigation sub-skill; do not claim algorithms are available from a dataset/metric import warning alone. |
| Law School GPA data helper | Network/cache and package metadata inconsistency may apply | Optional and unverified. | Prefer synthetic `RegressionDataset` for metric mechanics; verify data acquisition before using the built-in wrapper. |

## Data and schema misuse

### `ValueError: DataFrame values must be numerical`

`StructuredDataset` and `BinaryLabelDataset` cast the entire DataFrame to `float64`. Encode strings first or use `StandardDataset`.

Fix pattern:

```python
clean = raw.copy()
clean["sex"] = clean["sex"].map({"female": 0.0, "male": 1.0})
clean["approved"] = clean["approved"].map({"no": 0.0, "yes": 1.0})
clean = clean.dropna()
```

### `ValueError: Input DataFrames cannot contain NA values`

Drop or impute NAs before `StructuredDataset`/`BinaryLabelDataset`. `StandardDataset` drops NA rows after optional preprocessing, but direct `BinaryLabelDataset` construction does not.

### `The favorable and unfavorable labels provided do not match the labels in the dataset`

The label column contains values outside the declared two labels.

Recovery:

1. Inspect `sorted(df[label_name].unique())`.
2. Map labels to exactly two numeric values, or pass `favorable_label` and `unfavorable_label` that match the data.
3. Rebuild the dataset and check `set(dataset.labels.ravel())`.

### Protected-attribute group errors

Common messages include disjointness failures, missing group values, and unobserved value warnings.

Recovery checklist:

```python
print(dataset.protected_attribute_names)
print(dataset.privileged_protected_attributes)
print(dataset.unprivileged_protected_attributes)
print(dataset.convert_to_dataframe()[0][dataset.protected_attribute_names].drop_duplicates())
```

Then rebuild groups using encoded values:

```python
privileged_groups = [{"sex": 1.0}]
unprivileged_groups = [{"sex": 0.0}]
```

Remember: inside one group dictionary, keys are ANDed; multiple dictionaries in the list are ORed.

## Raw built-in dataset failures

### Wrapper exits or prints missing-file instructions

Legacy wrappers for Adult, German, COMPAS, Bank, and MEPS expect raw public files in package data locations. If files are absent, some constructors print instructions and call `sys.exit(1)` rather than raising a normal exception.

Recovery:

- Use the in-memory synthetic pattern if raw data is not essential.
- If raw data is essential, acquire the public files by file name, satisfy any data-use obligations, place them where the installed package expects its raw data, then instantiate the wrapper.
- Avoid calling raw wrappers in library import code, smoke scripts, or tests that must run without data.
- For workflow code that may run without raw data, isolate wrapper construction behind an explicit user/data-availability check.

### MEPS conversion problems

MEPS panel wrappers require converted CSV files. Panels 19 and 20 use 2015-derived data; panel 21 uses 2016-derived data. Conversion and data-use acceptance are outside the base package. Treat MEPS wrappers as unavailable until the converted CSV files are known present.

### Law School GPA network/cache problems

`LawSchoolGPADataset` is a `RegressionDataset` wrapper that reads LSAC data through the package's dataset helper. Network access or cache state may affect it, and this generated skill did not verify it in the base CPU environment. Use synthetic regression workflows when validating mechanics.

## `ClassificationMetric` workflow errors

### `ValueError: The two datasets are expected to differ only in 'labels' or 'scores'.`

The predicted dataset has different features, protected attributes, weights, label names, protected names, instance order, or metadata-sensitive structure.

Reliable construction:

```python
classified = true_dataset.copy(True)
classified.labels = predicted_labels.reshape((-1, 1)).astype(float)
classified.scores = predicted_scores.reshape((-1, 1)).astype(float)
```

If the two datasets came from separate DataFrames, use `true_dataset.align_datasets(other)` only when feature, label, and protected-name sets match.

### Confusion-derived metrics are `nan`, `inf`, or noisy

Some rates divide by the number of positives, negatives, predicted positives, or group members. A tiny or filtered group may have a zero denominator.

Recovery:

```python
print(metric.num_positives(privileged=False), metric.num_negatives(privileged=False))
print(metric.num_positives(privileged=True), metric.num_negatives(privileged=True))
print(metric.binary_confusion_matrix(privileged=False))
print(metric.binary_confusion_matrix(privileged=True))
```

Report the missing denominator rather than forcing a fairness interpretation.

### Generalized metrics look identical to hard-label metrics

If `classified_dataset.scores` was copied from hard labels, generalized confusion counts reduce to hard-label-like counts. Use calibrated probabilities or model scores when the task asks for generalized true/false positive/negative rates or calibrated postprocessing.

## `SampleDistortionMetric` workflow errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `distorted_dataset should be a StructuredDataset` | Passed raw arrays or a pandas DataFrame. | Build a `StructuredDataset` or deep-copy the original dataset and mutate `features`, `labels`, or `scores`. |
| `The two datasets may differ in features and labels/scores only.` | Protected attributes, weights, names, or row order changed. | Copy the original dataset first, preserve row order/protected attrs/weights, then mutate features. |
| Mahalanobis distance linear algebra error | Too few samples, duplicate/collinear features, or singular covariance. | Use Euclidean/Manhattan distance, add enough non-collinear samples, or regularize outside AIF360 before calling. |
| Mean distance difference/ratio helpers fail | Some AIF360 0.6.1 helper methods are less reliable than the aggregate primitives. | Compute `average_*_distance(privileged=False) - average_*_distance(privileged=True)` and ratio manually. |

## `RegressionDatasetMetric` workflow errors

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `Desired proportions must be specified for all values of the protected attributes` | `target_prop` keys do not exactly match encoded protected values. | Inspect `dataset.convert_to_dataframe()[0]` and provide all observed protected values, commonly `{0.0: ..., 1.0: ...}`. |
| `normalized is set to True, but full_dataset is not specified` | `discounted_cum_gain(normalized=True)` needs a reference dataset. | Pass `full_dataset=...`, usually the full ranking before truncation. |
| Unexpected DCG order | `RegressionDatasetMetric` uses current row order. | Sort the DataFrame into the intended ranking before constructing the `RegressionDataset`. |

## MDSS and OT metric-specific issues

- `MDSSClassificationMetric` needs `classified_dataset.scores` as expectation-like values. If scores are missing or are hard labels, the score may not reflect model calibration.
- `MDSSClassificationMetric.score_groups` scores the provided groups; it does not discover arbitrary subgroups. Route full subgroup discovery to the detectors sub-skill.
- OT distance is optional and requires `ot`. Without the extra, use non-OT metrics or install and verify the extra before use.
- For nominal/ordinal OT modes, the classifier input shape must match the number of classes; route detailed pandas/sklearn OT usage to the sklearn-interface sub-skill.
