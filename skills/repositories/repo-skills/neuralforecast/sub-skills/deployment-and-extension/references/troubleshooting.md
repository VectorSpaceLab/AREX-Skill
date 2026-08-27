# Deployment and Extension Troubleshooting

## Purpose

Read this when save/load, optional export, MLflow logging, or maintainer
extension work fails.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Save/load path error | Directory missing, not writable, or already exists unexpectedly. | Use a writable path and `overwrite=True` only when replacement is intended. |
| Loaded bundle behaves differently | The artifact is stale relative to the current code version. | Refit or refresh the serialized artifact. |
| ONNX import error | Optional ONNX packages are missing. | Install the optional export stack only if the user explicitly needs ONNX. |
| MLflow import or tracking error | Optional logging stack or tracking setup is missing. | Install/configure MLflow only when the user needs logging. |
| Docs generation issue | Maintainer docs tooling is not installed. | Treat docs generation as maintainer-only and do not use it as a runtime smoke. |

## Next checks

1. Run `../../scripts/check_serialization.py`.
2. If the model itself fails before serialization, route to `core-forecasting`.
3. If the model cannot fit because of data shape, route to `data-and-exogenous`.

## When to stop

Stop when the workflow truly needs optional packages or external services that
are not present. Do not claim export or logging support without the optional
stack.
