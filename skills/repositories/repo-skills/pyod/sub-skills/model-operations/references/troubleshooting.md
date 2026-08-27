# Model-Operations Troubleshooting

Use this reference to diagnose PyOD persistence, thresholding, combination, optional-extra, and post-load validation issues.

## Persistence and Trust

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ValueError` mentioning refusal to deserialize an untrusted pickle/joblib artifact | `load` or `compat_load` called without `trusted=True` | If and only if the artifact came from a trusted model registry/training pipeline/owner, rerun with `trusted=True`. Otherwise do not load it. |
| User asks whether `trusted=True` makes a downloaded artifact safe | Misunderstanding of trust flag | Explain that pickle/joblib can execute code and `trusted=True` is only acknowledgement. Obtain a trusted source or retrain. |
| Raw `joblib.load` of a PyOD-saved artifact returns a dict | File was written with `pyod.utils.persistence.save`; raw joblib sees the envelope | Use `pyod.utils.persistence.load(path, trusted=True)` to unwrap. |
| `load(strict=True, trusted=True)` rejects a raw joblib file | Raw legacy artifact lacks PyOD envelope metadata | Load non-strict only for trusted migration, validate behavior, then re-save with `save`; or re-fit and save with envelope. |
| `load` emits dependency-drift warning | Envelope versions for sklearn/joblib/numpy/scipy differ from runtime | Validate scores against probe/golden data. For production, re-fit or re-save in the target environment; use `strict=True` when drift should be blocked. |
| `node array from the pickle has an incompatible dtype` | Legacy sklearn Tree pickle loaded under a newer sklearn dtype layout | Use `load(path, trusted=True)` or `compat_load(path, trusted=True)` only for trusted artifacts. If recovered, validate and re-save with `save`; if not, re-fit. |
| `compat_load` raises about an unknown/missing dtype field or incompatible field dtype | Compatibility shim refuses unsafe Tree-state changes beyond its allowlist | Re-fit on the current sklearn environment. Do not patch around it unless maintaining PyOD with tests and a documented default. |
| Loaded model predicts but differs on rows with missing values | sklearn Tree dtype repair zero-filled a missing-value routing field | Re-fit on current sklearn for reliable missing-value behavior. Treat compat repair as migration aid, not exact replay guarantee. |
| Post-load detector lacks `decision_scores_`, `threshold_`, or `labels_` | Artifact is unfitted, wrong object, or non-BaseDetector object | Confirm object class and source. If expected to be fitted, retrain or locate the correct artifact. |

## Post-Load Validation Failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `decision_function(X_probe)` shape is not `(n_samples,)` | Wrong input shape, non-PyOD object, or modality-specific detector | Check expected input dimensionality and route modality issues to `specialized-modalities`. |
| Scores contain `nan` or `inf` | Invalid input data, missing preprocessing, numerical instability, incompatible migrated model | Validate input finite values and preprocessing. If the artifact was migrated, re-fit. |
| `predict` returns only zeros after load | Threshold too high for current score distribution, feature schema drift, or changed preprocessing | Compare `decision_scores_`, `threshold_`, and probe-score distribution with training expectations. Check feature order/schema metadata. |
| `predict_proba` raises invalid method error | Method must be `"linear"` or `"unify"` | Use a supported method and verify probabilities are in `[0, 1]`. |

## Thresholding

| Symptom | Likely cause | Recovery |
|---|---|---|
| `No module named 'pythresh'` when calling `FILTER()`, `IQR()`, etc. | PyThresh optional extra missing | Install `pip install 'pyod[pythresh]'` or `pip install pythresh`. |
| Importing `pyod.models.thresholds` works but using a factory fails | Factories import pythresh lazily | Install/repair pythresh and retry the specific factory. |
| Thresholder resource error mentioning `PathLike` / `NoneType` / internal `.pkl` resources | Version/Python-specific pythresh resource packaging issue | Capture Python and pythresh versions; upgrade/downgrade pythresh or use a Python version where the wheel's resources load. |
| `VAE()` thresholder fails with torch/import/device error | VAE thresholding needs torch-backed components | Install and verify torch (`pyod[torch]` plus pythresh) or select a non-neural thresholder. |
| Thresholding returns no anomalies on a small synthetic set | Score distribution or selected method not suitable; not necessarily failure | Validate shapes and finite scores. Try a simpler threshold such as numeric contamination, `IQR`, `MAD`, or `ZSCORE`, and evaluate on representative data. |
| `labels_` and `threshold_` are missing after fit | Detector fit failed before `BaseDetector._process_decision_scores()` or wrong detector path | Inspect earlier exception and detector support. Do not manually set labels unless designing a controlled wrapper. |

## Score Combination

| Symptom | Likely cause | Recovery |
|---|---|---|
| `No module named 'combo'` importing `pyod.models.combination` | `combo` optional extra missing | Install `pip install 'pyod[combo]'` or `pip install combo`. |
| Combined scores dominated by one detector | Detector scores on different scales | Standardize score matrices with `pyod.utils.utility.standardizer(train_scores, test_scores)` before combining. |
| `ValueError` from AOM/MOA with static buckets | Invalid `n_buckets` for the number of estimator columns | Choose a valid smaller bucket count, change the number of estimators, or intentionally use dynamic/bootstrapped settings. |
| Combined output shape unexpected | Input matrix transposed or 1-D | Ensure shape `(n_samples, n_estimators)`, not `(n_estimators, n_samples)`. |
| `majority_vote` gives surprising output | Function expects label/class-like inputs, not raw continuous scores | Use `average`, `maximization`, `median`, `aom`, or `moa` for continuous scores; use `majority_vote` after converting each detector to labels. |
| Combined labels unavailable | Combination functions return scores except majority-vote labels | Apply an explicit thresholding rule to combined scores and document it. |

## Optional Extras and Accelerated/Supervised Models

| Symptom | Likely cause | Recovery |
|---|---|---|
| Importing SUOD fails with `No module named 'combo'` | PyOD's SUOD module imports combination helpers, which need combo | Install `pip install 'pyod[combo,suod]'`. |
| Constructing SUOD raises message requiring optional `suod` package | SUOD extra missing | Install `pip install 'pyod[suod]'`; include `combo` if import still fails. |
| SUOD parallel run hangs or produces confusing worker errors | Joblib/process parallelism, base estimator issue, or environment conflict | Debug with `n_jobs=1`, fit each base estimator independently, then restore parallelism. |
| XGBOD import fails with `No module named 'xgboost'` | XGBoost extra missing | Install `pip install 'pyod[xgboost]'`. |
| `XGBOD.fit(X)` missing required `y` | XGBOD is supervised/semi-supervised and requires binary labels | Call `fit(X, y)` with labels where 0=inlier and 1=outlier. For unsupervised workflows, route to another detector. |
| XGBOD estimator-list length error | `estimator_list` and `standardization_flag_list` differ in length | Make the lists equal length or omit `standardization_flag_list` for default behavior. |
| XGBOD default features fail on very small datasets | Default KNN/LOF neighbor ranges may be invalid or too few | Increase data size, provide a smaller custom `estimator_list`, and validate `n_detector_`. |

## Operational Incident Playbook

1. Identify the surface: persistence, thresholding, combination, optional extra, or detector/modality. Route detector-family and modality questions to sibling sub-skills.
2. Reproduce with a tiny trusted probe or the bundled `scripts/persistence_smoke.py` when persistence is involved.
3. Check package extras with `importlib.util.find_spec` before debugging PyOD internals.
4. For loaded artifacts, validate type, fitted attributes, finite score shape, threshold, and a known probe batch.
5. If a compatibility repair occurred, re-save with `pyod.utils.persistence.save` after validation or re-fit for production.
6. Never load untrusted pickle/joblib artifacts to inspect them. Ask for a trusted source, training code, or a non-pickle export instead.
