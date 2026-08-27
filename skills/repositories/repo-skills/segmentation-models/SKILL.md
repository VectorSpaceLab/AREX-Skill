---
name: segmentation-models
description: "Use Segmentation Models for Keras/TensorFlow image segmentation
  model construction, losses, metrics, preprocessing, training utilities, and
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Segmentation Models Repo Skill

Use this repo skill when a task asks about the Python package `segmentation_models` / Segmentation Models: constructing Keras semantic-segmentation models, selecting backbones, configuring preprocessing, choosing segmentation losses/metrics, or assembling small training/evaluation/fine-tuning workflows.

This skill is for using the package as an operating library. If the task is about editing the repository source, packaging releases, or changing tests, use a Python repository maintenance skill instead.

## Install and import baseline

Segmentation Models 1.x expects a Keras backend plus its own package dependencies. The package metadata installs `keras_applications`, `image-classifiers`, and `efficientnet`; TensorFlow/Keras itself is chosen separately for the target platform.

```bash
pip install segmentation-models
# Install a compatible TensorFlow/Keras backend for the environment.
```

In modern TensorFlow environments, prefer TensorFlow Keras and set the framework before import:

```python
import os
os.environ.setdefault("SM_FRAMEWORK", "tf.keras")
import segmentation_models as sm

print(sm.__version__)
print(sm.framework())
print(sm.get_available_backbone_names()[:5])
```

Run `scripts/check_environment.py` when a task needs a no-data import/framework/backbone smoke check. Add `--build-model` only when the environment can import TensorFlow/Keras and can build a tiny offline model with `encoder_weights=None`.

## Route map

| User task | Read |
| --- | --- |
| Instantiate `Unet`, `Linknet`, `FPN`, or `PSPNet`; choose `backbone_name`, `input_shape`, `classes`, `activation`, `encoder_weights`; debug shape/backbone/framework constructor errors. | `sub-skills/model-construction/SKILL.md` |
| Choose `IOUScore`, `FScore`, Dice/Jaccard/focal/CE losses; configure class weights/indexes, thresholds, per-image reduction; hand-check metric math. | `sub-skills/losses-metrics/SKILL.md` |
| Assemble training/evaluation/fine-tuning loops; use `get_preprocessing`; set image/mask shapes; handle non-RGB data; freeze/unfreeze encoders; add regularization; run synthetic training smoke checks. | `sub-skills/training-utilities/SKILL.md` |
| Diagnose package-wide install/import/backend/version problems before a workflow-specific route. | `references/troubleshooting.md` |
| Decide whether this skill is current for a checkout or package release. | `references/repo-provenance.md` |

## Fast workflow patterns

### Binary segmentation model

```python
import os
os.environ.setdefault("SM_FRAMEWORK", "tf.keras")
import segmentation_models as sm

BACKBONE = "resnet34"
preprocess_input = sm.get_preprocessing(BACKBONE)
model = sm.Unet(
    BACKBONE,
    classes=1,
    activation="sigmoid",
    encoder_weights="imagenet",
)
model.compile("Adam", loss=sm.losses.bce_jaccard_loss, metrics=[sm.metrics.iou_score])
```

### Multiclass model

```python
model = sm.FPN(
    "efficientnetb0",
    input_shape=(256, 256, 3),
    classes=4,
    activation="softmax",
    encoder_weights="imagenet",
)
model.compile("Adam", loss=sm.losses.cce_jaccard_loss, metrics=[sm.metrics.IOUScore()])
```

### Offline smoke construction

```python
model = sm.Unet(
    "resnet18",
    input_shape=(32, 32, 3),
    classes=1,
    activation="sigmoid",
    encoder_weights=None,
)
```

## Safety and scope notes

- `encoder_weights="imagenet"` may download weights and expects RGB-compatible input. Use `encoder_weights=None` for offline checks, non-RGB direct inputs, and deterministic smoke tests.
- The bundled scripts use synthetic data or parser/help checks only; they do not clone datasets, train benchmark models, or require GPU.
- CUDA/GPU is optional acceleration for real training in this package. CPU TensorFlow/Keras is sufficient for import, model-construction, loss/metric, and tiny training validation.
- Original notebooks and tests were used as evidence, but runtime guidance here is self-contained; do not require future agents to open or execute files from the original checkout.
