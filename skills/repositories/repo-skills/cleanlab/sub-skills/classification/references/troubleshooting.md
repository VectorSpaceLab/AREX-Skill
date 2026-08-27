# Troubleshooting

## Labels are strings, one-hot, or otherwise not zero-based integers

Symptom:

- `Labels cannot be strings`
- `Labels must be zero-indexed integers`
- `Labels must be 1D`

Fix:

- encode the classes to integers `0..K-1`
- keep the same encoding aligned with `pred_probs` column order
- if the user wants multi-label, send them to the multi-label sub-skill instead

## `pred_probs` shape or value errors

Symptom:

- `pred_probs array must have shape: num_examples x num_classes`
- `pred_probs and labels must have same length`
- `pred_probs must have at least ... columns`
- `Values in pred_probs must be between 0 and 1`

Fix:

- make sure `pred_probs` is `(N, K)`
- verify the class order matches `labels`
- ensure the probabilities are out-of-sample if they will be used for issue finding
- if classes are missing, compress labels and columns together or keep dummy columns aligned to the highest class index

## Cross-validation is failing or says there is not enough data

Symptom:

- `Need more data from each class for cross-validation`

Fix:

- lower `cv_n_folds`
- collect more examples for rare classes
- for tiny fixtures, set `cv_n_folds` to a value that every class can support

## Sample weights or estimator compatibility problems

Symptom:

- `sample_weight must be a supported fit() argument`
- sklearn clone or fit/predict/proba errors

Fix:

- use a sklearn-compatible, clonable estimator
- ensure it implements `fit`, `predict_proba`, and `predict`
- pass `sample_weight` directly to `fit` or `clf_final_kwargs`, not inside `clf_kwargs`

## Multiprocessing or `n_jobs` trouble

Symptom:

- hangs, import-side issues, or confusing multiprocessing behavior
- the user wants the safest deterministic path

Fix:

- set `n_jobs=1`
- use the direct pred-probability route when possible
- on tiny smoke fixtures, prefer a single process

## Low-memory route confusion

Symptom:

- the user asks for batched label checking or limited-memory operation

Fix:

- keep the main classification route here
- cross-link to `experimental.label_issues_batched`
- note that `low_memory=True` in `CleanLearning` ignores `thresholds`, `noise_matrix`, and `inverse_noise_matrix`

## Latent matrix inconsistencies

Symptom:

- trace or matrix consistency looks wrong
- confidence matrices do not round-trip cleanly

Fix:

- confirm the supplied matrices are valid probability matrices
- use `compute_inv_noise_matrix` and `compute_noise_matrix_from_inverse` as consistency checks
- if the user supplied a noise matrix with trace `<= 1`, reject it

## Import errors for core dependencies

Symptom:

- missing `numpy`, `scipy`, `pandas`, or `scikit-learn`
- optional plotting errors while displaying dataset-health output

Fix:

- install the stable cleanlab stack for the core route
- if the user only needs this classification sub-skill, they do not need the full Datalab stack
- for plotting-related output, `matplotlib` is optional rather than required

## Scope mismatches

- dataset audit spanning multiple issue types -> `datalab`
- outlier scoring from features or `pred_probs` alone -> `outlier`
- multiannotator consensus or active learning -> `multiannotator`
- multi-label, regression, token, object-detection, or segmentation workflows -> task-specific sub-skills
- experimental deep-learning helpers -> `experimental`
