# PhysicsNeMo active learning and deployment

## Active-learning workflow

Use `physicsnemo.active_learning` when the user is building an iterative loop such as:

`training -> metrology/validation -> query -> labeling -> data integration -> checkpoint/restart`

### Important package shape

- Root `physicsnemo.active_learning` exports the registry, `Driver`, `DefaultTrainingLoop`, and the main config classes.
- Protocol interfaces live in `physicsnemo.active_learning.protocols`.
- Config objects are intentionally JSON-serializable so checkpoints and restarts stay portable.

### Workflow outline

1. Choose or implement the learner, query strategy, label strategy, metrology strategy, and queue.
2. Keep runtime state and large pools out of the serialized config.
3. Use the driver to orchestrate the loop and checkpoint/restart policy.
4. Route model choice, dataloading, mesh preprocessing, and distributed scaling to sibling sub-skills.

## Deployment / export workflow

- Use `physicsnemo.deploy.onnx.export_to_onnx_stream` for ONNX byte-stream export.
- Current PyTorch ONNX export paths may require `onnxscript` even when `onnx` is installed; install it when export reports a missing `onnxscript` module.
- Treat `onnxruntime` as optional and only needed if you want to run the exported model.
- Keep export separate from CUDA-graph/static-capture training.

## Support utilities

- `physicsnemo.utils.logging` for LaunchLogger/MLflow/W&B style logging.
- `physicsnemo.utils.checkpoint` for checkpoint save/load helpers.
- `physicsnemo.metrics` and `physicsnemo.optim` are useful support surfaces when the active-learning loop manages metrics or optimizer state.

## Tiny smoke guidance

- Use the bundled ONNX export helper to prove the export surface.
- Avoid credentialed logging backends by default; only enable them when the user provided the needed project/entity details.
- Do not use a fixed-dataset training question to force the active-learning driver; route ordinary training to the model or data sub-skill instead.
