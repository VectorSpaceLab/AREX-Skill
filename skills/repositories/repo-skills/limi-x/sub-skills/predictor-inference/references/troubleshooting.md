# Predictor Inference Troubleshooting

## Common symptoms

| Symptom or message | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: Retrieval is not supported for CPU inference! Please use the noretrieval configuration when running on a CPU device!` | `device=torch.device("cpu")` with a config whose first pipeline has `retrieval_config.use_retrieval=true`. | Use a non-retrieval config such as `cls_default_noretrieval.json` or `reg_default_noretrieval.json`, or run on CUDA/GPU with a retrieval config. |
| `ValueError: inference_config is not a config file path: ...` | Constructor or `set_inference_config()` received a string that is not an existing local JSON path. | Pass an existing local JSON config path or load the JSON yourself and pass the list. Confirm the config is a non-empty list with `retrieval_config` in each pipeline. |
| `FileNotFoundError`, `torch.load` failure, or checkpoint key errors during construction | `model_path` is missing, not a LimiX checkpoint, or points to an incomplete/corrupt file. | Provide a local `.ckpt` file. The constructor loads immediately and this sub-skill does not download weights. Use a checkpoint that supports the requested task; MVI is identified for the 16M checkpoint family. |
| `ModuleNotFoundError` for `torch`, `einops`, `kditransform`, `sklearn`, `pandas`, or related packages | LimiX runtime dependencies are not installed in the active Python environment. | Use an environment with Python, PyTorch, NumPy, pandas, scikit-learn, SciPy, einops, kditransform, and the other LimiX runtime packages. CUDA runs may also need a matching flash-attn wheel. |
| `Flash attention is not supported. Please install/reinstall flash attention.` | CUDA execution reached a flash-attention-only fallback path but `flash_attn` is missing or incompatible. | Install a flash-attn build matching the active Python, PyTorch, and CUDA versions, or switch to a compatible environment. CPU/no-retrieval smoke checks may avoid flash attention but are not proof that CUDA inference works. |
| CUDA/NCCL/distributed initialization errors with `inference_with_DDP=True` | DDP flag was enabled outside a prepared GPU distributed launch, or on a CPU-only host. | Disable `inference_with_DDP` for local API use. Only enable it when the parent workflow controls CUDA devices and distributed launch semantics. |
| `ValueError: All features are constant! Please check your data.` | Every feature was constant, all-NaN, or removed as invalid after train/test preprocessing. | Remove constant/all-NaN columns, verify train/test columns are aligned, and make sure at least one informative feature remains. MVI still needs observed values; do not make every entry of every feature missing. |
| Warning: `Missing value imputation does not currently support the preprocessing method of power! Using the default worker_tags method` | `mask_prediction=True` with a config pipeline using a `power` feature rebalance worker. | Use the MVI/non-retrieval regression config or edit the config to remove `power` workers. Pass a deep copy if you do not want the predictor to mutate an in-memory config list. |
| `ValueError: Missing value imputation does not currently support the preprocessing method of power!` | A power-transform worker survived into MVI postprocessing. | Replace that config pipeline with a non-power MVI-compatible transform before running full inference. |
| `Unsupport string dtypes! ...` | Feature matrix is a fixed-width NumPy string array rather than a pandas/object/numeric container. | Use a pandas dataframe/object columns or pre-encode strings to numbers before calling `predict()`. |
| Output has no `.to()` method | Classification output is already a NumPy probability array. | Use NumPy operations directly for classification. Only regression predictions are torch tensors. |
| Output is a tuple, not an array/tensor | `mask_prediction=True` is enabled. | Unpack it: `primary_pred, reconstructed_features = predictor.predict(...)`. Slice `reconstructed_features[-len(x_test):]` for test-row imputation. |
| Classification metrics look class-swapped | Probability columns were assumed to be `[0, 1]` without checking encoded class order. | Read `predictor.classes` after prediction and map columns to those labels. |

## Fast diagnostic sequence

1. Run the smoke helper without `--run-inference` to validate imports, config shape, local checkpoint path existence, and tiny fixture shapes.
2. If CPU is selected, inspect the config's `retrieval_config.use_retrieval` and switch to a non-retrieval config if needed.
3. If constructor fails, treat it as a checkpoint/environment issue because model loading happens during construction.
4. If `predict()` fails after construction, inspect data shape, target dtype, NaNs, all-constant features, and task/config mismatch.
5. For retrieval tuning or benchmark directory loops, route out to the appropriate sibling sub-skill instead of debugging that workflow here.
