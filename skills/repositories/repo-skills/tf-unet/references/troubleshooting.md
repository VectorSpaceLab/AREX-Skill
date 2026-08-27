# Troubleshooting

## Cross-cutting issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `TypeError: Descriptors cannot not be created directly` | TensorFlow 1.15.x is paired with a too-new `protobuf` | Pin `protobuf==3.20.3` or lower and rerun the import smoke. |
| `AttributeError` for `tf.Session`, `tf.placeholder`, or `tf.reset_default_graph` | A TensorFlow 2.x install is being used | Switch to TensorFlow 1.15.x for this legacy package surface. |
| `ModuleNotFoundError` for `click`, `PIL`, `scipy`, or `h5py` | Launcher/dependency extras were not installed | Add the workflow dependency that matches the selected launcher or provider workflow. |
| Tiny toy generation crashes with `ValueError: low >= high` | The requested image size is smaller than the generator border | Use larger `nx`/`ny` values or a smaller `border` for synthetic checks. |
| Predictions are smaller than labels | `VALID` convolutions shrink spatial dimensions | Crop labels with `util.crop_to_shape(label, prediction.shape)` before comparing or training. |
| `ImageDataProvider` reports no training files | The glob pattern or mask naming convention is wrong | Make sure data and mask files are paired and the masks use the configured suffix. |
| Output directories disappear during a smoke run | `Trainer.train(..., restore=False)` recreates them | Use a fresh temp directory or set `restore=True` when continuing an existing run. |

## Workflow-specific guidance

- The root smoke script is the first place to check when the environment looks suspicious.
- Use tiny synthetic dimensions for inspection. The default toy generator parameters are not meant for small 32x32 examples.
- `tf_unet` is a graph/session package. If a workflow assumes eager execution, it is the wrong mental model for this repo.
- Keep the save path as the base checkpoint path (`model.ckpt` style); the trainer and predictor expect that convention.
- If a launcher workflow depends on external data, confirm the data contract first instead of debugging the model graph.
