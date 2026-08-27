---
name: image-ai
description: "Use ImageAI 3.x PyTorch computer-vision workflows for
  classification, object detection, video detection, and custom training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ImageAI Repo Skill

Use this repo skill when a task involves the ImageAI Python package (`imageai`), especially ImageAI 3.x PyTorch workflows for simple computer-vision applications.

## Start here

1. Confirm the user is using ImageAI 3.x / PyTorch assets (`.pt` or `.pth`). TensorFlow/Keras `.h5` models are legacy ImageAI 2.x artifacts and are not accepted by the current package path.
2. Confirm local model weights, images/videos, datasets, and JSON config files exist. This skill does not bundle pretrained weights or download assets.
3. Choose the closest sub-skill route below.
4. For environment uncertainty, run the bundled smoke checker before loading large weights:

```bash
python scripts/check_imageai_env.py
python scripts/check_imageai_env.py --require-cuda
```

## Route by task

| User task | Read |
| --- | --- |
| Classify a still image with ImageNet weights | [classification-workflows](sub-skills/classification-workflows/SKILL.md) |
| Run custom image classification from a trained `.pt`/`.pth` model and classes JSON | [classification-workflows](sub-skills/classification-workflows/SKILL.md) |
| Detect COCO objects in a still image with RetinaNet, YOLOv3, or TinyYOLOv3 | [object-detection-workflows](sub-skills/object-detection-workflows/SKILL.md) |
| Run custom YOLO/TinyYOLO still-image detection from a trained model and detection JSON | [object-detection-workflows](sub-skills/object-detection-workflows/SKILL.md) |
| Detect objects in videos, camera feeds, or live streams | [video-detection-workflows](sub-skills/video-detection-workflows/SKILL.md) |
| Add per-frame, per-second, per-minute, or whole-video analysis callbacks | [video-detection-workflows](sub-skills/video-detection-workflows/SKILL.md) |
| Prepare datasets, convert Pascal VOC to YOLO, validate layouts, or start custom training | [custom-training-and-data](sub-skills/custom-training-and-data/SKILL.md) |
| Resolve install, backend, or model-asset confusion | [installation and model assets](references/installation-and-model-assets.md) and [troubleshooting](references/troubleshooting.md) |

## Package and install essentials

ImageAI 3.x uses PyTorch. A typical CPU-oriented setup follows the package docs and requirements:

```bash
pip install imageai
pip install cython "pillow>=7.0.0" "numpy>=1.18.1" "opencv-python>=4.1.2" \
  "torch>=1.9.0" "torchvision>=0.10.0" tqdm scipy matplotlib mock
```

Use a PyTorch CUDA wheel only when the runtime has compatible NVIDIA drivers and the task needs acceleration. CUDA is helpful for video and real training, but CPU is enough for import/API checks and small validation helpers. See [installation and model assets](references/installation-and-model-assets.md) for dependency variants, model-weight expectations, and legacy TensorFlow notes.

## Minimal import/API check

```python
from imageai.Classification import ImageClassification
from imageai.Detection import ObjectDetection, VideoObjectDetection
from imageai.Classification.Custom import ClassificationModelTrainer, CustomImageClassification
from imageai.Detection.Custom import DetectionModelTrainer, CustomObjectDetection, CustomVideoObjectDetection

for cls in [
    ImageClassification, ObjectDetection, VideoObjectDetection,
    ClassificationModelTrainer, CustomImageClassification,
    DetectionModelTrainer, CustomObjectDetection, CustomVideoObjectDetection,
]:
    cls()
```

If this fails, do not proceed to weight loading. Use the root troubleshooting reference first.

## Shared operating rules

- Always choose the model-type setter that matches the weight architecture. Filenames are hints, not proof.
- Current ImageAI 3.x model files must be `.pt` or `.pth`; `.h5` triggers a TensorFlow-legacy error.
- Call `useCPU()` before `loadModel()` when forcing CPU.
- Load large weights once and reuse the detector/classifier object for repeated images or frames.
- Treat pretrained weights, custom models, JSON mappings, datasets, videos, and camera streams as caller-supplied assets.
- Do not run full video detection or training as a quick smoke test unless the user supplies bounded assets and compute expectations.

## Provenance and routing metadata

- [repo-provenance.md](references/repo-provenance.md) records the source snapshot and evidence paths used to create this skill.
- [repo-routing-metadata.json](references/repo-routing-metadata.json) records managed repo-skills-router placement for import tooling.
