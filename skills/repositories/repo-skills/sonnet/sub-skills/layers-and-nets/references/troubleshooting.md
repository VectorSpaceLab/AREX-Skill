# Layers and Nets Troubleshooting

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `Input size must be specified` or variable shape contains `None` | Final feature/channel dimension is unknown on first call. | Provide a statically shaped tensor or build after shape inference. |
| `b_init` error when `with_bias=False` | Bias initializer is incompatible with disabled bias. | Remove `b_init` or enable bias. |
| BatchNorm raises about missing `is_training` | BatchNorm call requires explicit training/inference mode. | Thread `is_training` through the containing module. |
| BatchNorm evaluation changes unexpectedly | Moving-average state was not built/restored or training flag is wrong. | Build once, checkpoint all variables, and call with `is_training=False` for eval. |
| Dropout MLP complains about `is_training` | Dropout-enabled `snt.nets.MLP` needs the flag. | Pass `is_training` or remove dropout. |
| VectorQuantizer shape mismatch | Input last dimension does not match embedding dimension. | Project features with `snt.Linear(embedding_dim)` first. |
| ResNet/Cifar net memory or device failure | Image model is too large for current runtime. | Start with small synthetic batches on CPU; verify accelerator separately. |
