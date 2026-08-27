# Tuning and Distributed Troubleshooting

## Purpose

Read this when an Auto*, Ray, Optuna, or Spark job fails to configure or when
resource choices do not match the workflow.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Missing config key | A required search-space argument such as `input_size` was omitted. | Add the missing key and rerun the config check. |
| Wrong backend warning | `ray_options` or `optuna_options` was supplied to the other backend. | Keep Ray options with Ray and Optuna options with Optuna. |
| GPU trial crash | Too many GPUs were reserved per trial or the model config conflicts. | Use conservative GPU allocation and tiny trial counts. |
| `use_fitted` validation error | `cross_validation` was called with an unsupported combination. | Follow the restrictions in the backend reference. |
| Spark scaling failure | Local/static scaling was requested in a distributed path. | Remove unsupported scalers or keep the workflow local. |
| Bad partition path | The distributed output path is unwritable or malformed. | Choose a writable `partitions_path`. |

## Next checks

1. Run `../../scripts/check_auto_config.py`.
2. If the problem is about model choice or data shape, route elsewhere first.
3. If the problem is only about core training, use `core-forecasting` after the
   config is fixed.

## When to stop

If the user needs Spark or GPU hardware that is not present, stop and explain
the missing backend rather than silently falling back to an unverified path.
