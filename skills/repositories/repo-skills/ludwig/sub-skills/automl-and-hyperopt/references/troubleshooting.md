# AutoML and Hyperopt Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: ray` while importing AutoML | Ray backend is imported by AutoML utilities but not installed | Install the distributed/Ray dependencies for the chosen workflow or avoid AutoML paths that require Ray. |
| `ModuleNotFoundError: dask` | AutoML/dataframe support dependency missing | Install Dask/DataFrame support or use CLI/config-only routes. |
| Executor type not found | Optional executor library missing or typo in config | Check `executor.type` and install only that executor dependency. |
| Search metric not found | `output_feature`/`validation_metrics` does not match outputs | Verify output feature names and metrics before running HPO. |
| Search runs too long | Unbounded samples/time or expensive model | Set small `num_samples`, lower epochs/train steps, and explicit time budgets. |
| Ray cluster error | Ray not initialized or incompatible environment | Start with local executor or run Ray initialization as a separate, user-approved step. |
