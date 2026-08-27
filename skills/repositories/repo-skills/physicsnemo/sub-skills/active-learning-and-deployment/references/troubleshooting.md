# Active learning and deployment troubleshooting

## Protocol/config shape

- Symptom: the driver or restart path cannot reconstruct a workflow.
- Likely cause: the config contains runtime objects, pools, devices, or non-serializable callables.
- Fix: keep configs JSON-serializable and re-provide runtime objects at restart.

## Registry / strategy lookup

- Symptom: a custom strategy cannot be recreated from a checkpoint.
- Likely cause: it was not registered in the active-learning registry.
- Fix: register the strategy before serialization and use the protocol surface rather than ad hoc objects.

## Logging backend issues

- Symptom: MLflow or W&B logging fails.
- Likely cause: project/entity/auth details were not supplied or the backend was not intended to be used.
- Fix: make tracking explicit, or use offline/no-backend mode for smoke checks.

## ONNX export issues

- Symptom: export fails or the output cannot be run.
- Likely cause: the model uses unsupported ops, the export path was mixed with training capture, `onnxscript` is missing for the PyTorch exporter, or `onnxruntime` is missing for runtime inference.
- Fix: export a tiny model first, install `onnxscript` if the exporter requests it, treat ORT as optional, and keep export separate from training capture.

## Wrong route

- Symptom: the user only wants a model family, a datapipe, or a mesh utility.
- Likely cause: active-learning was selected just because the task mentioned training.
- Fix: route to the sibling sub-skill that owns the actual data/model/scaling task.
