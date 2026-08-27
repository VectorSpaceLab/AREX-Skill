# Model Management Troubleshooting

## Access and auth

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| License or gated-repo error | Token or browser-based acceptance is missing | Use `TABPFN_TOKEN`, clear stale cache state, or complete the browser flow. |
| Browser login fails in headless CI | No interactive browser is available | Set `TABPFN_NO_BROWSER=1` and provide a token. |
| Download keeps retrying | Cache path is wrong or inaccessible | Set `TABPFN_MODEL_CACHE_DIR` explicitly. |

## Cache and version issues

- If the cache path is not where you expect, inspect the resolved cache directory first.
- If the user passes a bare filename, remember that TabPFN resolves it against the current working directory and then the cache directory.
- If a checkpoint version does not match the requested model family, use a version-pinned model path or `create_default_for_version`.

## Persistence issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `.tabpfn_fit` error | Wrong output suffix | Rename the save path to end in `.tabpfn_fit`. |
| Load fails after save | Archive contents are missing or corrupted | Recreate the fitted-state archive from a live fitted estimator. |
| SafeTensors conversion fails | Input checkpoint is missing a tensor-valued state dict | Verify the input checkpoint before conversion. |

## Visualization and endpoint issues

- Missing plotting extras should be handled by installing the visualization extra.
- The SageMaker template needs an existing endpoint name and AWS credentials.

## When to move on

- If the task is about one-dataset prediction, go to tabular-prediction.
- If the task is about preprocessing or validation, go to preprocessing-config.
- If the task is about batched scoring, go to batched-performance.
