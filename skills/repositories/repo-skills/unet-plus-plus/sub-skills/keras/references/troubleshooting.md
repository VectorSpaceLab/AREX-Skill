# Keras troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Import fails because the environment looks modern | The stack is pinned to TensorFlow 1.4.1 / Keras 2.2.2 | Use the legacy Python 3.6 environment used for the smoke checks |
| TensorFlow import emits numpy compatibility warnings | Old TF 1.x binary interacting with a newer host | Keep the warning in mind; the model-build smoke may still succeed |
| `Input size must be at least 48x48` | The chosen backbone rejects the requested input shape | Increase the input size or choose a different backbone |
| PSPNet rejects the input shape | `downsample_factor` and image dimensions do not satisfy the divisibility guard | Make H and W divisible by `6 * downsample_factor` |
| `plot_model` or graph rendering fails | `pydot`/graphviz missing or misconfigured | Install `pydot` and the graphviz runtime, or skip plotting |
| Pretrained weights fail to download | No network access, cache miss, or weight mismatch | Use `encoder_weights=None` for structure-only inspection, or retry with network access |
| `BRATS2013_application.py` is hard to run | It expects the BRATS data arrays and a long training loop | Treat it as a reference workflow, not a smoke check |
| The backbone catalog seems to accept a model but shape checks fail later | The architecture validates the shape at build time | Recheck the selected backbone, head, and input dimensions |
| `segmentation_models` lacks `__version__` at import time | The runtime package exposes a version file, not a top-level attribute | Inspect `segmentation_models/__version__.py` instead |

## Good recovery sequence

1. Confirm you are in the legacy Keras environment.
2. Use `encoder_weights=None`.
3. Start from a `64x64x3` VGG16-friendly test shape, or a valid PSPNet shape.
4. Check backbone-specific preprocessing only after the model builds.
5. Move to the BRATS2013 script only when you actually have the dataset.

## Safety note

Do not use the ImageNet test bundle as a default runtime check unless the user
explicitly accepts the network download requirement.
