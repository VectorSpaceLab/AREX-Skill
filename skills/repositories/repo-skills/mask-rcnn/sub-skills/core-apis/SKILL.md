---
name: core-apis
description: "Routes Mask_RCNN core API, Config, Dataset, MaskRCNN, utility,
  visualization, and TensorFlow/Keras compatibility tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Core APIs

Use this sub-skill when a task asks how to use or debug the installed `mrcnn` package itself: configuration classes, `MaskRCNN` construction, utility functions, visualization signatures, graph-building constraints, or legacy TensorFlow/Keras compatibility.

## Read first by need

- Read [api-reference.md](references/api-reference.md) for verified public signatures and object relationships.
- Read [compatibility.md](references/compatibility.md) before choosing TensorFlow/Keras versions or interpreting modern Keras errors.
- Read [troubleshooting.md](references/troubleshooting.md) when imports, graph construction, image dimensions, or API calls fail.
- Run [scripts/inspect_mask_rcnn_api.py](scripts/inspect_mask_rcnn_api.py) to inspect a user environment without requiring the original checkout.

## Core API workflow

1. Verify the runtime stack and import package:

   ```bash
   python sub-skills/core-apis/scripts/inspect_mask_rcnn_api.py --show-signatures
   ```

2. Define a `Config` subclass. Set at least `NAME`, `NUM_CLASSES`, image size/resize mode, `GPU_COUNT`, and `IMAGES_PER_GPU`. Dimensions that flow into the FPN should be divisible by 64.
3. Construct the model with a mode-specific object:

   ```python
   from mrcnn.config import Config
   from mrcnn import model as modellib

   class MyConfig(Config):
       NAME = "my_project"
       NUM_CLASSES = 1 + 1
       GPU_COUNT = 1
       IMAGES_PER_GPU = 1
       IMAGE_MIN_DIM = 512
       IMAGE_MAX_DIM = 512

   config = MyConfig()
   model = modellib.MaskRCNN(mode="inference", config=config, model_dir="logs")
   ```

4. For training, route to [training](../training/SKILL.md). For dataset subclasses and masks, route to [data-preparation](../data-preparation/SKILL.md). For `detect()` results and visualization, route to [inference-evaluation](../inference-evaluation/SKILL.md).

## Decision points

- **Using modern Keras?** Treat failures as compatibility/porting unless a full graph build and target workflow already pass. The legacy stack is the safer operating default.
- **CPU versus GPU?** CPU can validate imports, shapes, utilities, and tiny graphs. Real training and multi-GPU behavior need backend-specific runtime verification.
- **Weights mismatch?** Core API can explain `load_weights`; training owns the transfer-learning recipes and layer exclusions.
- **Original sample path requested?** Use bundled references/scripts instead. This repo skill is meant to operate without reopening the source checkout.
