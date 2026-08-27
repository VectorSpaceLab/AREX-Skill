# Training and Optimization Troubleshooting

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `model.trainable_variables` is empty | Model has not been built. | Run a forward pass with representative input before the tape step. |
| All gradients are `None` | Loss is disconnected from variables, non-floating tensors are used, or operations ran outside the tape. | Compute the forward pass under `tf.GradientTape`; inspect variables and loss dtype. |
| `apply` raises about different structures or lengths | Gradients and parameters do not have matching nest structure. | Use `variables = model.trainable_variables`; compute gradients from exactly that list. |
| `None` gradient error for one variable | A variable did not affect the loss. | Remove unused variables from the update or fix the forward path. |
| Sparse update errors | Embedding-style sparse gradients require matching indexed slices. | Test with the native SGD sparse pattern or start with dense gradients. |
| Loss does not change | Learning rate, model output scale, or target fixture is wrong. | Start with the bundled tiny training smoke and compare pre/post loss. |
| Keras legacy optimizer reference tests fail | New TensorFlow/Keras combinations may not expose `tf.keras.optimizers.legacy`. | Validate Sonnet optimizer behavior directly with dense/sparse assertions. |
