# Troubleshooting: data-pipeline utilities

Start by running the bundled help command. It should work even when cuML is not installed:

```bash
python sub-skills/data-pipeline-utilities/scripts/data_utility_smoke.py --help
```

Then run the CUDA-gated core smoke only in an environment where cuML is expected to be installed:

```bash
python sub-skills/data-pipeline-utilities/scripts/data_utility_smoke.py --case core
```

## Import and backend failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ModuleNotFoundError: cuml`, `cupy`, or `cudf` | RAPIDS/cuML package stack is not installed in the active Python environment. | Activate or install a CUDA-compatible cuML environment. Do not treat source files alone as runtime proof. |
| `CUDA driver version is insufficient`, `cudaErrorInsufficientDriver`, or no visible devices | CUDA package variant and host driver/GPU are incompatible or hidden. | Check `nvidia-smi`, CUDA-visible devices, and that the cuML/CuPy wheel variant matches the driver/runtime. |
| `cupy.cuda.runtime.getDeviceCount()` returns zero | No GPU is visible to the process. | Set device visibility correctly or run on a CUDA host. CPU-only checks are not sufficient for cuML utility behavior. |
| Import succeeds but first utility call fails during allocation | Device memory is exhausted or a stale CUDA context/RMM pool is unhealthy. | Retry with a tiny sample size, single visible GPU, and no benchmark-scale arrays; release other GPU jobs. |

## Data shape, type, and output problems

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `inconsistent number of samples` | Arrays passed to split or metrics have different first dimensions. | Print `shape` for every input immediately before the utility call. Split all aligned arrays together. |
| `Expected 1 column`, `1D array`, or label validation errors | Metrics or encoders received a 2-D label array or a DataFrame with multiple columns. | Flatten labels to shape `(n_samples,)` or select a single target column. |
| Unexpected NumPy/pandas output instead of CuPy/cuDF, or vice versa | Output follows input type, global output setting, or estimator `output_type`. | Set `output_type` where available and assert container type before chaining. |
| Layout-sensitive downstream estimator is slow or rejects input | Generated arrays default to a specific `order`, often `F` for classification/blobs. | Pass `order='C'` or `order='F'` intentionally when generating data, and validate `X.flags`. |
| `copy=False` changed upstream data | In-place preprocessing or missing-value distance logic mutated arrays. | Use `copy=True` unless mutation is safe and documented for that step. |

## Dataset generation failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `n_classes * n_clusters_per_class` exceeds `2**n_informative` | `make_classification` cannot place all clusters in the informative hypercube. | Increase `n_informative`, reduce classes/clusters, or use `make_blobs` for cluster-only data. |
| Informative/redundant/repeated feature sum exceeds total features | Invalid `make_classification` feature budget. | Ensure `n_informative + n_redundant + n_repeated <= n_features`. |
| `centers` shape mismatch in `make_blobs` | Provided centers do not have shape `(n_centers, n_features)` or do not match per-center `n_samples`. | Recompute centers and per-center counts together; verify `centers.shape[1] == n_features`. |
| `make_arima` raises deprecation warnings | Time-series generator is part of the deprecated time-series surface. | Suppress warnings only for compatibility checks and prefer future-proof alternatives when task requirements allow. |

## Preprocessing failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Scaler/imputer rejects sparse input | Centering or dense-only preprocessing was applied to a sparse vectorizer output. | Use sparse-compatible transforms or convert only tiny matrices intentionally. |
| Unknown category during `LabelEncoder`, `OneHotEncoder`, or `OrdinalEncoder.transform` | Transform data contains categories not seen during fit and `handle_unknown='error'`. | Fit on the full category vocabulary where legitimate, or choose a supported unknown-handling mode. |
| One-hot output is too large | High-cardinality categories with dense output. | Keep `sparse_output=True`, use `TargetEncoder`, or route model choice to `python-estimators` for sparse-aware pipelines. |
| `TargetEncoder` validation score looks too good on training data | Target leakage from using global target statistics on training rows. | Use `fit_transform` for training rows and `transform` only for validation/test rows. Use folds and smoothing. |
| `TargetEncoder` output column count is surprising | Multi-feature mode mismatch. | Use `multi_feature_mode='combination'` for one joint encoded feature; use `'independent'` for one encoded feature per input column. |
| Unseen categories in target encoding become a constant | This is expected; unknown categories are imputed with the learned global statistic. | Check whether smoothing/global fallback is acceptable for the task. If not, collect more training category coverage. |
| `fold_ids` rejected | Custom fold values are missing, wrong length, or outside `[0, n_folds - 1]`. | Set `split_method='customize'`, pass one fold id per sample, and verify integer range. |

## Metrics failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `roc_auc_score` or `precision_recall_curve` says all labels are one class | Tiny split lost one class. | Use stratified splitting, larger data, or a fixed split that contains both classes. |
| `log_loss` rejects probability input | Probability matrix shape or class count is invalid. | For binary tasks, verify the expected one-column/two-column convention for the active cuML version; for multiclass, pass class probabilities for all classes. |
| `mean_squared_log_error` rejects inputs | Negative target or prediction values. | Clip or transform only when mathematically justified; otherwise use ordinary squared/absolute error metrics. |
| Cluster metric differs after label renaming | Non-invariant metric chosen. | Use permutation-invariant metrics such as adjusted Rand, homogeneity/completeness, V-measure, or mutual information when labels are arbitrary. |
| Silhouette computation runs out of memory | Pairwise distances over too many samples. | Use a smaller sample or set `chunksize` to reduce peak memory. |
| Pairwise distance says a metric is unsupported on dense or sparse data | Metric/data container combination is invalid. | Choose a metric supported for the current dense/sparse representation or convert the representation intentionally. |
| Dense/sparse mix is not implemented | `X` and `Y` differ in sparse status. | Convert both inputs to the same representation before `pairwise_distances`. |
| Pairwise kernel rejects `chi2`/`additive_chi2` input | These kernels require nonnegative features. | Scale or validate features so all values are nonnegative before using these kernels. |
| Custom pairwise kernel fails | Callable is not a Numba CUDA device function or keyword parameters do not match. | Use a supported string kernel first; for custom kernels, define a device function with `(x, y, ...)` signature and pass only accepted keywords, or use `filter_params=True`. |

## Text vectorizer failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `cuML does not support callable analyzer` | Callable analyzers are not supported. | Preprocess text into a cuDF/pandas Series first, then use `analyzer='word'`, `'char'`, or `'char_wb'`. |
| Unsupported scikit-learn parameter error for `tokenizer`, `token_pattern`, `input`, `encoding`, `decode_error`, or `strip_accents` | cuML vectorizers intentionally do not implement those scikit-learn options. | Clean, tokenize, or normalize text before vectorization; keep constructor parameters within the supported cuML set. |
| `After pruning, no terms remain` | `min_df`, `max_df`, or `max_features` pruned the whole vocabulary. | Lower `min_df`, raise `max_df`, increase `max_features`, or check that documents are not empty after preprocessing. |
| `NotFittedError` during `CountVectorizer.transform` | No vocabulary was learned and no fixed vocabulary was supplied. | Call `fit`/`fit_transform` first, or pass a valid `vocabulary`. |
| Hashing features are hard to interpret | HashingVectorizer is stateless and collisions are possible. | Use Count/Tf-idf vectorizers when feature names are required. |
| Sparse text matrix is rejected by next step | Downstream estimator or preprocessing step requires dense input. | Route estimator compatibility to `python-estimators`; densify only for tiny diagnostics. |

## Explainer failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Explainer is slow despite GPU | Model callable is CPU-bound or background data is too large. | Set `is_gpu_model` correctly, shrink background data for setup, and increase samples only after correctness is proven. |
| Kernel/Permutation explainer fails calling model | Callable cannot accept the container type passed by the explainer. | Wrap the model function to convert inputs explicitly, or force `is_gpu_model=True/False` based on callable behavior. |
| `TreeExplainer` rejects model type | Model is not a supported tree model or cannot be converted through Treelite. | Use supported XGBoost, LightGBM, cuML RandomForest, scikit-learn RandomForest, or Treelite model objects; otherwise use Kernel/Permutation explainer. |
| `TreeExplainer` rejects multi-target model | Multi-target tree models are unsupported. | Explain one compatible target/model at a time or choose a model-agnostic explainer if appropriate. |
| Background data dtype mismatch | Interventional TreeExplainer background and explained rows have different dtype. | Convert both background and explained arrays to `float32` or both to `float64`. |

## Time-series failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Deprecation warning for `cuml.tsa` or `make_arima` | The time-series API surface is deprecated. | Use only for existing compatibility tasks and record the deprecation in handoff. |
| ARIMA rejects exogenous data shape | Exogenous columns are not grouped as `batch_size * n_exog`. | Reshape exogenous data to `(n_obs, batch_size * n_exog)` and provide future exogenous data as `(nsteps, batch_size * n_exog)` for forecasts. |
| Missing exogenous values fail | Exogenous variables do not support missing values. | Impute or remove missing exogenous values before model construction. |
| Leading missing endogenous observations produce constant early predictions | Leading `NaN` padding prevents early model predictions. | Treat early predictions over padded regions as unavailable or constant placeholders. |
| Seasonal ARIMA order rejected | Model order violates implementation constraints or data length is too short. | Reduce `(p, d, q)` or `(P, D, Q, s)`, increase observations, and use tiny generated data to isolate schema errors. |
