---
name: training
description: "Guides Mask_RCNN training, fine-tuning, weights, checkpoints,
  layer selection, schedules, callbacks, and backend constraints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Training and Fine-tuning

Use this sub-skill when a task asks to train, fine-tune, resume, configure, or troubleshoot Matterport Mask_RCNN training on COCO, Balloon/VIA, Nucleus, Shapes, or a custom instance segmentation dataset.

## Read first by need

- Read [training-workflows.md](references/training-workflows.md) for the API training sequence, sample schedules, layer selections, and augmentation notes.
- Read [weights-and-checkpoints.md](references/weights-and-checkpoints.md) for COCO/ImageNet/last/custom weight loading and checkpoint behavior.
- Read [troubleshooting.md](references/troubleshooting.md) for class-head mismatch, batch-size, memory, empty masks, and slow training issues.
- Use [scripts/plan_training.py](scripts/plan_training.py) to generate a safe training plan summary without running training.
- Adapt [scripts/minimal_training_template.py](scripts/minimal_training_template.py) when writing a project-specific training script that does not depend on original sample files.

## Training workflow

1. Prepare training and validation datasets with [data-preparation](../data-preparation/SKILL.md). Both datasets must be loaded and `prepare()` must be called.
2. Define a training `Config` with the correct `NUM_CLASSES`, image sizes, `STEPS_PER_EPOCH`, `VALIDATION_STEPS`, and memory-aware `GPU_COUNT`/`IMAGES_PER_GPU`.
3. Build the model:

   ```python
   from mrcnn import model as modellib
   model = modellib.MaskRCNN(mode="training", config=config, model_dir="logs")
   ```

4. Load initial weights. For COCO-to-custom transfer, exclude class-specific heads.
5. Train heads first, then optionally deeper ResNet/FPN layers:

   ```python
   model.train(dataset_train, dataset_val,
               learning_rate=config.LEARNING_RATE,
               epochs=30,
               layers="heads")
   model.train(dataset_train, dataset_val,
               learning_rate=config.LEARNING_RATE / 10,
               epochs=60,
               layers="all")
   ```

6. Validate by building an inference config and routing detection/evaluation to [inference-evaluation](../inference-evaluation/SKILL.md).

## Decision points

- **New class count?** Set `NUM_CLASSES = 1 + foreground_count` and exclude final heads when loading COCO weights.
- **Small dataset?** Start with `layers="heads"`; use augmentation carefully; freeze batch norm unless you have large batches.
- **CPU-only?** Treat training as a code/data smoke test, not a practical run.
- **Multi-GPU?** Verify exact TensorFlow/CUDA/Keras compatibility before using `GPU_COUNT > 1`.
- **No original sample script?** Use the bundled training template and references; this skill is self-contained.
