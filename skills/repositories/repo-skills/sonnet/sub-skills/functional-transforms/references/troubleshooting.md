# Functional Transforms Troubleshooting

| Symptom | Cause | Recovery |
| --- | --- | --- |
| TensorVariable has no value | Code tried to read captured variables before `init`. | Call transformed `init`; pass returned params to `apply`. |
| Parameters are reinitialized every step | `init` is inside the training loop. | Call `init` once, then reuse/update params. |
| State is lost or stale | A stateful module was wrapped with `transform` rather than `transform_with_state`, or updated state was ignored. | Use `transform_with_state` and thread returned state. |
| Gradients are `None` | Loss function is not written as a function of params. | Ensure `value_and_grad` receives params as an explicit argument. |
| Device helper does not use GPU | TensorFlow runtime has no matching physical device. | Check `tf.config.list_physical_devices('GPU')`; do not infer accelerator support from CPU. |
| Functional optimizer state shape errors | Optimizer state was created for a different parameter tree. | Reinitialize optimizer state after changing model structure. |
