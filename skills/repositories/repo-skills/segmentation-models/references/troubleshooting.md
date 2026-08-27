# Segmentation Models Troubleshooting

Read this for package-wide installation, import, framework, backend, and version problems before routing to a workflow-specific sub-skill.

## Import selects the wrong Keras framework

**Symptoms**

- Import prints `Segmentation Models: using 'keras' framework` when the task expects TensorFlow Keras.
- Errors mention standalone `keras` even though the environment has TensorFlow.
- Loss/metric objects fail because Keras submodules were not initialized.

**Likely causes**

Segmentation Models chooses a framework at import time. If `SM_FRAMEWORK` is unset, it tries standalone `keras` first and falls back to `tf.keras` only after an import failure.

**Recovery**

Set the framework before importing the package:

```python
import os
os.environ["SM_FRAMEWORK"] = "tf.keras"
import segmentation_models as sm
assert sm.framework() == "tf.keras"
```

If an interactive session already imported `segmentation_models` with the wrong framework, restart the Python process or notebook kernel and set `SM_FRAMEWORK` before import.

## TensorFlow/Keras backend is missing or incompatible

**Symptoms**

- `ModuleNotFoundError: No module named 'keras'` or `No module named 'tensorflow'`.
- Import errors from `efficientnet`, `classification_models`, or `keras_applications`.
- Modern standalone Keras 3 errors appear while using a Segmentation Models 1.x package.

**Likely causes**

The package dependencies do not install TensorFlow itself. Segmentation Models 1.x was written for Keras/TensorFlow-Keras APIs from the Keras 2 era.

**Recovery**

Install a TensorFlow/Keras backend compatible with the platform, then prefer `SM_FRAMEWORK=tf.keras` for modern environments. Verify with:

```bash
python scripts/check_environment.py --framework tf.keras
```

If standalone `keras` mode is required, ensure the standalone Keras version is compatible with Segmentation Models 1.x and its dependency stack.

## `encoder_weights="imagenet"` fails or downloads unexpectedly

**Symptoms**

- The constructor stalls on a download, fails behind a firewall, or cannot find cached weight files.
- Non-RGB input with ImageNet weights fails or produces channel-shape errors.

**Likely causes**

ImageNet encoder weights are fetched by the backbone package and are RGB-oriented. They are not needed for shape or plumbing checks.

**Recovery**

Use `encoder_weights=None` for offline, smoke, and non-RGB direct-input workflows:

```python
model = sm.Unet("resnet18", input_shape=(32, 32, 3), encoder_weights=None)
```

For non-RGB data that still needs pretrained RGB encoders, route to `sub-skills/training-utilities/references/data-and-masks.md` and add an explicit channel-mapping layer before the 3-channel base model.

## GPU is visible but the package does not use it

**Symptoms**

- `nvidia-smi` shows GPUs but TensorFlow lists no GPU devices.
- Training is slow on CPU.

**Likely causes**

Segmentation Models itself has no CUDA-only API. GPU use depends entirely on the installed TensorFlow/Keras backend and driver/runtime compatibility.

**Recovery**

For package usage and tiny validation, CPU is sufficient. For real training acceleration, install a TensorFlow build that supports the target GPU stack and verify TensorFlow device visibility independently before blaming Segmentation Models. Keep the Segmentation Models code the same after TensorFlow sees the GPU.

## Model constructor shape or backbone errors

Route to `sub-skills/model-construction/SKILL.md` when symptoms mention:

- invalid `backbone_name`;
- `decoder_block_type`, `pyramid_aggregation`, `downsample_factor`, or `psp_pooling_type` values;
- `PSPNet` input dimensions;
- output spatial shape mismatches;
- non-RGB inputs with pretrained weights.

The bundled `sub-skills/model-construction/scripts/model_constructor_smoke.py` can build a safe offline model with `encoder_weights=None`.

## Loss, metric, or mask-channel errors

Route to `sub-skills/losses-metrics/SKILL.md` when symptoms mention:

- `class_indexes`, `class_weights`, `threshold`, `smooth`, or `per_image`;
- unexpected IoU/F-score/Dice/Jaccard values;
- activation/loss mismatches such as `softmax` targets with binary losses;
- all-zero masks or empty predictions.

The bundled `sub-skills/losses-metrics/scripts/check_losses_metrics.py` runs deterministic in-memory assertions.

## Training or data-layout errors

Route to `sub-skills/training-utilities/SKILL.md` when symptoms mention:

- `model.fit`, `fit_generator`, `evaluate`, or `predict`;
- image preprocessing, augmentation, or mask one-hot/channel layout;
- freezing/unfreezing encoders;
- `set_trainable` or `set_regularization`;
- non-RGB training data.

The bundled `sub-skills/training-utilities/scripts/tiny_training_smoke.py` checks training plumbing with synthetic arrays only.
