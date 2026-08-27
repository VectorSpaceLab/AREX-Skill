---
name: mask-rcnn
description: "Guides Matterport Mask_RCNN package workflows for instance
  segmentation, dataset preparation, training, inference, visualization, and
  evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Mask_RCNN Repo Skill

Use this skill when a task names **Mask_RCNN**, **Matterport Mask R-CNN**, the `mrcnn` Python package, `mask-rcnn` distribution, or asks for Mask R-CNN instance segmentation workflows with Keras/TensorFlow.

This is a self-contained operating guide for the package API and sample workflows. It does not require the original repository checkout; scripts and references here replace the reusable parts of the source samples.

## Quick compatibility check

Mask_RCNN is legacy TensorFlow/Keras code. Prefer a Python 3.7-era stack for faithful execution:

```bash
python -m pip install "tensorflow==1.15.5" "Keras==2.3.1" "numpy==1.18.5" \
  "h5py==2.10.0" "scikit-image==0.16.2" "opencv-python==4.5.5.64" \
  imgaug pycocotools
python -m pip install mask-rcnn
python - <<'PY'
import mrcnn
from mrcnn.config import Config
from mrcnn import model as modellib
print("mrcnn import ok", mrcnn.__file__)
print("Config", Config.__name__)
print("MaskRCNN", modellib.MaskRCNN.__name__)
PY
```

If a modern TensorFlow/Keras environment fails with `No module named 'keras.engine'`, `tf.log` missing, or reshape errors during graph construction, read [installation-and-compatibility.md](references/installation-and-compatibility.md) and [troubleshooting.md](references/troubleshooting.md) before patching or porting.

For a reusable runtime diagnostic, run:

```bash
python scripts/check_env.py --show-signatures
```

## Route by task

- **Core package APIs and compatibility**: read [core-apis](sub-skills/core-apis/SKILL.md) for `Config`, `Dataset`, `MaskRCNN`, utility functions, signatures, graph-building constraints, and environment diagnostics.
- **Dataset preparation and mask formats**: read [data-preparation](sub-skills/data-preparation/SKILL.md) for `utils.Dataset` subclassing, `load_image()`, `load_mask()`, `prepare()`, VIA/COCO/nucleus layouts, Shapes fixtures, resize modes, and mini-masks.
- **Training and fine-tuning**: read [training](sub-skills/training/SKILL.md) for `MaskRCNN(mode="training")`, pretrained weights, layer selection (`heads`, `4+`, `all`), schedules, logs/checkpoints, augmentation, and GPU cautions.
- **Inference, visualization, and evaluation**: read [inference-evaluation](sub-skills/inference-evaluation/SKILL.md) for `MaskRCNN(mode="inference")`, `detect()` outputs, display helpers, color splash, COCO AP conversion, and nucleus RLE output.

## Common workflow skeleton

1. Install a compatible TensorFlow/Keras stack and verify imports with [scripts/check_env.py](scripts/check_env.py).
2. Create a `Config` subclass with `NAME`, `NUM_CLASSES`, image resize dimensions, `GPU_COUNT`, and `IMAGES_PER_GPU` appropriate to the workflow.
3. For training, create dataset subclasses derived from `mrcnn.utils.Dataset`; implement `load_*`, `load_mask`, and optionally `image_reference`; call `prepare()` before training.
4. Create `modellib.MaskRCNN(mode="training"|"inference", config=config, model_dir=...)`.
5. Load weights. For a new class count from COCO weights, load by name and exclude `mrcnn_class_logits`, `mrcnn_bbox_fc`, `mrcnn_bbox`, and `mrcnn_mask`.
6. Train with selected layers or run `detect([image])`; inspect returned `rois`, `class_ids`, `scores`, and `masks`.
7. Use the nearest sub-skill scripts for layout validation, fixture generation, color splash, RLE helpers, or API inspection.

## Read when refreshing

Read [repo-provenance.md](references/repo-provenance.md) before deciding whether this skill matches a different checkout or package release. If the commit, package version, source paths, or public APIs changed, run `refresh-repo-skill` rather than editing this skill ad hoc.

Structured router metadata lives in [repo-routing-metadata.json](references/repo-routing-metadata.json).
