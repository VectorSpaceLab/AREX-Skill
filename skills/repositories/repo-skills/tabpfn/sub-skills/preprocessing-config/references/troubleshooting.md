# Preprocessing and Configuration Troubleshooting

## Shape and size errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `X` and `y` length mismatch | The training target has the wrong number of rows | Fix the dataset join or split. |
| `X is not a 2D array` | A vector or nested structure was passed as `X` | Reshape to `(n_samples, n_features)`. |
| Feature or sample limit errors | The dataset exceeds the checkpoint's supported size | Downsample, choose a larger model version, or set `ignore_pretraining_limits=True` if the user accepts the risk. |

## Missing values and infinities

- NaNs are accepted and handled by the preprocessing pipeline.
- Infinities are rejected unless `PASSTHROUGH_INF=True`.
- If `PASSTHROUGH_INF=True`, infinities are temporarily masked for preprocessing and restored afterwards.

## Mixed pandas dtypes

- Nullable booleans and nullable numerics are coerced to float64 before sklearn validation.
- Categorical columns are valid, but mixed object/string columns often become ordinal-encoded.
- Free text columns are usually noisy and should be treated with caution.

## CPU and MPS issues

- CPU large-dataset guards are controlled by `TABPFN_ALLOW_CPU_LARGE_DATASET` and `ignore_pretraining_limits`.
- On Apple Silicon, `TABPFN_MPS_MEMORY_FRACTION` affects the per-process memory cap.
- A CPU import check does not prove that the MPS or CUDA path is healthy.

## When to stop debugging here

- If the issue is about model access, cache paths, auth tokens, or downloads, switch to model-management.
- If the issue is about output interpretation rather than input validation, switch to tabular-prediction.
