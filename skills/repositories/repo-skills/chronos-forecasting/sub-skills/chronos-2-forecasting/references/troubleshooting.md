# Chronos-2 troubleshooting

Use this when `Chronos2Pipeline` loading or forecasting fails. For deep schema validation, route to [../../data-formats-and-validation/](../../data-formats-and-validation/). For non-Chronos-2 pipeline families, route to [../../chronos-bolt-and-original/](../../chronos-bolt-and-original/). For training/evaluation/deployment failures, route to [../../training-evaluation-deployment/](../../training-evaluation-deployment/).

## Loading, cache, and optional dependency issues

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: chronos` | Package not installed in the active Python environment. | Install `chronos-forecasting` in the environment used by the agent/user. Re-run a no-download import/signature smoke before model loading. |
| `Not a Chronos config file` | The supplied directory/model ID is not a Chronos checkpoint or is incomplete. | Verify the anchor points to a model directory with a Chronos config. Prefer `BaseChronosPipeline.from_pretrained(...)` and print `type(pipeline)`. |
| Returned pipeline is not `Chronos2Pipeline` | The anchor is Chronos-Bolt or original Chronos. | Route to [../../chronos-bolt-and-original/](../../chronos-bolt-and-original/) or change the model ID to a Chronos-2 model. |
| Hugging Face download/auth/cache errors | Remote model not cached, network unavailable, or credentials/token missing for private anchors. | Do not retry indefinitely. Ask the user to provide network approval, a local cached checkpoint, or required auth. Keep default scripts in inspect-only mode unless the user provides `--model-id-or-path`. |
| `Loading models from s3:// URIs requires boto3` | S3 optional dependency is missing. | Install extras that include S3 support, or use a local/HF checkpoint. Use `force_s3_download=True` only if the user explicitly wants a fresh S3 cache. |
| PEFT/LoRA adapter load raises missing `peft` | Adapter checkpoint detected but optional PEFT package unavailable. | Install `peft`, or load a fully merged/saved Chronos-2 checkpoint. S3 LoRA adapters are not the supported path. |

## Device and dtype failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| CUDA requested but unavailable | CPU-only torch build, no visible GPU, or `CUDA_VISIBLE_DEVICES` hides GPUs. | Use `device_map="cpu"`; if GPU is required, switch to a CUDA-enabled torch environment and verify `torch.cuda.is_available()`. |
| CPU inference is very slow | Full model on CPU or large batch/context/horizon. | Reduce `batch_size`, `context_length`, number of items, or use a smaller Chronos-2 checkpoint. Move to GPU only when explicitly available and approved. |
| dtype errors or poor CPU behavior with bfloat16 | Inappropriate dtype for host/model/backend. | Omit dtype or use `torch_dtype="float32"` on CPU. On modern GPUs, `torch_dtype="bfloat16"` can reduce memory but should be validated. |
| Out-of-memory during prediction | Batch includes many item-target-covariate tasks; long horizon multiplies work. | Lower `batch_size`, lower `context_length`, split items, reduce requested quantiles, or move to a larger device. Remember Chronos-2 batch size counts target and covariate series, not only item IDs. |

## Raw tensor/list/list-of-dicts input errors

| Symptom/error text | Likely cause | Recovery |
|---|---|---|
| `Expected 3-d tensor with shape (n_series, n_variates, history_length)` | A raw tensor was 1-D or 2-D. | For one batch, reshape to `(batch, n_variates, history)`, e.g. `x[None, None, :]`. For variable-length inputs, use a list of 1-D/2-D arrays. |
| `Each element should be 1-d or 2-d` | A list element had too many dimensions. | Each list element must be `(history,)` or `(n_variates, history)`. Split extra axes before calling. |
| `Found invalid keys` | A dict contains keys other than `target`, `past_covariates`, and `future_covariates`. | Remove extra keys or move metadata outside the forecast input. |
| `Element ... does not contain the required key 'target'` | Missing target in a list-of-dicts item. | Add `target` as a 1-D or 2-D array. |
| `Target must be 1-d or 2-d` | Target array has shape like `(1, 2, history)`. | Use `(history,)` for univariate or `(n_variates, history)` for multivariate. |
| `Found invalid type for past_covariates/future_covariates` | Covariate group is not a dictionary. | Use `{"past_covariates": {"name": values}}` and `{"future_covariates": {"name": values}}`. |
| ``past_covariates` must be 1-d with length...` | Past covariate length does not match the target history length. | Align every past covariate to the same history index as `target`. |
| `Expected keys in future_covariates must be a subset of past_covariates` | Future values supplied for a covariate with no past history. | Add historical values for that covariate under `past_covariates`, or remove it from `future_covariates`. |
| ``future_covariates` must be 1-d with length equal to prediction_length` | Future covariate horizon mismatch. | Make every provided future covariate exactly `prediction_length` long. |
| `All past_covariates/future_covariates must have same keys` | Heterogeneous list-of-dicts schemas in one call. | Split into homogeneous groups and call the pipeline once per schema. |
| String/categorical covariate fails as torch tensor | Torch tensors cannot represent string dtype. | Use NumPy arrays or pandas Series/DataFrames for categorical covariates. |

## DataFrame `predict_df` errors

| Symptom/error text | Likely cause | Recovery |
|---|---|---|
| `df does not contain all...` | Missing `id_column`, `timestamp_column`, or target column(s). | Verify column names and pass `id_column=...`, `timestamp_column=...`, `target=...` explicitly. |
| `future_df does not contain all...` | `future_df` lacks id/timestamp or required covariate columns. | Build `future_df` with id/timestamp plus known-future covariate columns only. |
| `future_df cannot contain target` | Target leakage in future covariates. | Drop target columns from `future_df`; it should contain only known-future covariates and keys/timestamps. |
| `future_df cannot contain columns not present...` | Future covariate was not present in historical `df`. | Add the same covariate column to historical `df`, or remove it from `future_df`. |
| `same time series IDs` | Context and future tables have different item IDs. | Ensure each item in `df` has exactly one future block in `future_df`; preserve IDs and string/int types. |
| `future_df must contain prediction...` | Each item does not have exactly `prediction_length` future rows. | Generate exactly horizon rows per item. Use a validator before forecasting. |
| `future_df timestamps do not match...` | Future timestamps differ from the expected continuation of the historical frequency. | Regenerate future timestamps from the forecast start and correct frequency, or set `validate_inputs=False` only after manually proving alignment. |
| `Could not infer frequency` or `not infer frequency` | Too few timestamps, irregular timestamps, or gaps. | Provide `freq="h"`, `freq="D"`, etc. when inference is impossible; otherwise sort/fill gaps. |
| `same frequency` | Different series have incompatible timestamp frequencies. | Resample or split series by frequency. |
| Output rows missing expected target ordering | Multi-target output is `(item, target, step)` repeated. | Filter by both item ID and `target_name` before plotting or joining. |

## Prediction length and long horizons

| Symptom | Likely cause | Recovery |
|---|---|---|
| Warning: `We recommend keeping prediction length <= ...` | Requested horizon exceeds `pipeline.model_prediction_length`. | Treat as a quality warning. Reduce horizon, evaluate accuracy carefully, or explicitly accept long-horizon unrolling. |
| Error with `limit_prediction_length=True` | Strict raw prediction rejected a horizon beyond the model default. | Lower `prediction_length` or set `limit_prediction_length=False` only when degraded long-horizon quality is acceptable. |
| `unrolled_quantiles` error | Long-horizon quantiles include levels not in `pipeline.quantiles`. | Choose unrolling quantiles from `pipeline.quantiles`, commonly `[0.1, ..., 0.9]` when available. |
| Future covariates shorter than horizon | Raw list-of-dicts future values do not cover `prediction_length`. | Provide full future covariate arrays. In `predict_df`, provide exactly horizon rows per item. |

## Cross-learning issues

| Symptom | Likely cause | Recovery |
|---|---|---|
| Results change when `batch_size` changes | Cross-learning groups all tasks in each batch. | Fix `batch_size` for comparisons and production runs. |
| Cross-learning is worse than independent forecasts | Task is not homogeneous/related enough or batch grouping is poor. | Compare `cross_learning=False` and `True`; keep the better setting for the target validation metric. |
| Heterogeneous inputs fail or behave unexpectedly | Mixed target/covariate schemas in one cross-learning batch. | Split into homogeneous groups before enabling cross-learning. |

## Quantile and point-forecast interpretation

| Symptom | Likely cause | Recovery |
|---|---|---|
| Requested quantiles outside model range look clipped or poor | Chronos-2 interpolates from trained quantiles and warns outside range. | Prefer quantile levels available in or inside `pipeline.quantiles`. |
| `predictions` differs from an expected arithmetic mean | Chronos-2 point output uses the `0.5` quantile in the implementation. | Treat `predictions`/`mean` as a median-style point forecast unless you compute a separate expectation. |
| Plotting interval columns fails | Quantile columns are string names like `"0.1"`. | Access `forecast_df["0.1"]`, not `forecast_df[0.1]`. |

## When to stop and route elsewhere

- If the user needs to fix timestamps, `future_df`, target/covariate schemas, categorical encoding, or `from_data_frame`/`from_list_of_dicts`, route to [../../data-formats-and-validation/](../../data-formats-and-validation/).
- If the model anchor is Chronos-Bolt or original Chronos, route to [../../chronos-bolt-and-original/](../../chronos-bolt-and-original/).
- If the task involves fitting, benchmark datasets, fev metrics, SageMaker, cloud credentials, or checkpoint training policy, route to [../../training-evaluation-deployment/](../../training-evaluation-deployment/).
