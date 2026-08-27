# Cross-Cutting Troubleshooting

## Import and install failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError` for `ludwig` | Package not installed in the active Python | Install Ludwig in an isolated Python 3.12+ environment, then run `python -c "import ludwig"`. |
| `Requires-Python` or resolver refuses package | Python is too old | Use Python 3.12+. |
| Optional module missing (`fastapi`, `ray`, `optuna`, `captum`, `onnx`, provider SDKs) | Narrow install omitted the extra | Install the workflow-specific extra or library; do not install `full` unless the task really needs many optional workflows. |
| Torch CUDA is unavailable even on GPU host | CPU wheel, incompatible driver/runtime, or container lacks GPU passthrough | Run `python scripts/check_env.py --check-cuda`; match torch/CUDA/runtime before planning GPU tasks. |

## Config and data failures

- Missing or empty `input_features` / `output_features`: validate with `sub-skills/configuration-and-data/scripts/validate_ludwig_config.py`.
- Dataset column mismatch: make sure every feature `name` or `column` is present in the training/prediction data. Prediction datasets usually omit output columns.
- Invalid feature type or encoder/decoder: export schema or render config before training, then route to [configuration-and-data](../sub-skills/configuration-and-data/SKILL.md).

## Runtime failures

- Long training or out-of-memory: reduce batch size, use tiny smoke fixtures first, disable unnecessary saves/logs, and avoid LLM/GPU workflows without explicit hardware planning.
- Missing model metadata during prediction/evaluation: reload a saved Ludwig model directory that contains model weights, hyperparameters, and training-set metadata.
- Forecasting error names timeseries: use a model trained with timeseries input/output features and sufficient window history.
- Server timeout: increase `--prediction_timeout`, reduce model/batch size, or debug locally with batch `predict` before serving.
- Hub upload or config-generation provider errors: verify credentials and avoid running remote side effects unless the user asks.
