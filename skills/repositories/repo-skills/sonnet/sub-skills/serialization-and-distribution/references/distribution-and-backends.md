# Distribution and Backend Guidance

## Replicator helpers

Sonnet exposes `snt.distribute.Replicator` and `snt.distribute.TpuReplicator` wrappers around TensorFlow distribution ideas. Use them only after verifying the TensorFlow runtime sees the required devices.

```python
import tensorflow as tf
print(tf.config.list_physical_devices())
```

A host with accelerator hardware is not enough; the active TensorFlow build must load the relevant runtime libraries.

## CrossReplicaBatchNorm

`CrossReplicaBatchNorm` is intended for replica context. Calling it outside the correct replica/cross-replica context raises context errors. For single-process CPU validation, prefer ordinary `snt.BatchNorm`.

## Backend classification

- CPU: sufficient for module construction, checkpoints, SavedModel, tiny smokes, and most API behavior.
- CUDA/GPU: required only for performance or GPU-specific distribution claims. Verify `tf.config.list_physical_devices('GPU')` and run a GPU tensor op.
- TPU: required for `TpuReplicator` claims; CPU cannot substitute.
- XLA: verify with `tf.function(jit_compile=True)` on the target device when the task needs compiled execution.
