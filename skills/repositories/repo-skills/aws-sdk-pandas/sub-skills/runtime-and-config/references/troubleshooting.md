# Runtime and Config Troubleshooting

## Purpose

Read this when import checks, configuration defaults, or distributed-mode switches fail before the workflow reaches a service-specific API.

## Failure patterns

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError` during import for `boto3`, `botocore`, `pandas`, `numpy`, or `pyarrow` | Base dependencies are missing or the environment is not the one that was prepared | Reinstall `awswrangler` into a clean environment and rerun `../../../scripts/check_runtime.py`. |
| `Missing optional dependency ...` when calling a specific helper | The relevant extra is not installed | Install the feature extra, then rerun the import check. |
| `wr.engine.get()` or `wr.memory_format.get()` does not show the expected mode | Ray/Modin were not installed or an environment variable set the mode earlier | Inspect `WR_ENGINE`, `WR_MEMORY_FORMAT`, and `WR_ADDRESS`, then reset the mode explicitly. |
| `boto3_session` / `s3_additional_kwargs` is rejected in distributed mode | The API is being used under Ray with unsupported arguments | Switch back to Python/pandas mode or remove the unsupported kwargs. |
| `NoCredentialsError` or `NoRegionError` appears immediately after import | The runtime is fine, but the AWS session is not configured | Set credentials and region before calling service-specific code. |
| `AttributeError` after `wr.config.reset()` | The config item was reset and is no longer loaded | Set the property again or let the environment variable reload it. |

## Practical recovery order

1. Run `../../../scripts/check_runtime.py --show-config --check-common-extras`.
2. Confirm the intended mode with `wr.engine.get()` and `wr.memory_format.get()`.
3. Check the `WR_*` environment variables that might be overriding defaults.
4. Only after the runtime is stable, route to the service sub-skill that owns the failing API.

## Notes

- Do not treat a successful `awswrangler` import as proof that every extra is installed; many features are lazy-loaded.
- When you need a clean slate, use `wr.config.reset()` and then reload the specific setting you want to test.
- For live AWS work, a valid region and credentials are prerequisites even when the Python import itself succeeds.
