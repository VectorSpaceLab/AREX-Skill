# Serialization and Distribution Troubleshooting

| Symptom | Cause | Recovery |
| --- | --- | --- |
| Checkpoint has no variables | Module was saved before first call. | Build the module with representative input before saving. |
| Restore reports unmatched objects | Target module structure or variable names differ. | Recreate the same module structure and build with compatible shape before restore. |
| SavedModel load result is not a Sonnet class | SavedModel restores TensorFlow objects/signatures, not original Python class identity. | Use exported signatures for inference; use checkpoints for Python module restoration. |
| Optimizer state missing after restore | Checkpoint was saved before first `optimizer.apply`. | Run one training step before checkpointing optimizer state. |
| `CrossReplicaBatchNorm` context error | Called outside replica context. | Use a valid distribution strategy or ordinary BatchNorm for CPU/single replica. |
| GPU/TPU unavailable despite hardware | Active TensorFlow build cannot load accelerator runtime. | Verify TensorFlow physical devices; install compatible backend packages before claiming support. |
| XLA compile error | Unsupported TensorFlow op or target backend. | Fall back to eager/graph execution or simplify the compiled function. |
