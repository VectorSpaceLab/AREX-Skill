---
name: classification-workflows
description: "Use ImageAI ImageNet and custom image classification inference
  workflows with PyTorch model weights."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Classification Workflows

Use this sub-skill when the task is to classify still images with ImageAI's PyTorch classification APIs:

- ImageNet classification with `ImageClassification` and built-in ImageNet class labels.
- Custom classification inference with `CustomImageClassification`, an ImageAI-trained `.pt`/`.pth` model, and the matching JSON class mapping.
- CPU-forced classification, `result_count` selection, file/numpy/PIL image inputs, and the returned label/probability arrays.

Do not use this sub-skill for custom model training or dataset preparation; route those requests to [custom-training-and-data](../custom-training-and-data/SKILL.md). Do not use it for object detection or video detection; route those to the detection sub-skills.

## Runtime references

- [API reference](references/api-reference.md): verified class names, call order, method signatures, model type mapping, input forms, return shapes, and model extension behavior.
- [Workflows](references/workflows.md): ImageNet and custom classification recipes, asset prerequisites, CPU-only commands, validation steps, and in-process examples.
- [Troubleshooting](references/troubleshooting.md): classification-specific recovery for missing dependencies, TensorFlow `.h5` files, mismatched model type/weights, bad JSON mappings, image input errors, and warning noise.
- [Helper script](scripts/classify_image.py): parameterized CLI wrapper around `ImageClassification` and `CustomImageClassification` that prints JSON and never downloads weights.

For package-wide installation, backend, and model-asset policy, also check the root skill's [installation and model assets](../../references/installation-and-model-assets.md) notes.

## Quick routing checklist

1. Ask whether the user has ImageNet release weights or a custom ImageAI-trained classifier. ImageNet mode needs only the model file; custom mode also needs the JSON class mapping produced during training.
2. Match `--model-type` or the setter method to the architecture used by the weights: `mobilenetv2`, `resnet50`, `inceptionv3`, or `densenet121`.
3. Reject TensorFlow-era `.h5` weights for ImageAI 3.x. Use `.pt` or `.pth`; for `.h5`, explain the ImageAI 2.1.6-or-earlier compatibility path instead of trying to load it.
4. Call the model type setter, `setModelPath(...)`, custom `setJsonPath(...)` when needed, optional `useCPU()`, then `loadModel()` before `classifyImage(...)`.
5. Treat outputs as two parallel arrays: `labels: list[str]` and `probabilities: list[float]` in descending score order.

## Safe helper use

Use the bundled helper for command-line classification when the user supplies local asset paths:

```bash
python scripts/classify_image.py \
  --mode imagenet \
  --model-type resnet50 \
  --model-path /path/to/resnet50-weights.pth \
  --image /path/to/image.jpg \
  --result-count 5 \
  --cpu
```

For custom classification, add `--json-path /path/to/model_classes.json` and keep `--model-type` aligned with the architecture used during training. The helper accepts image files only; in-process API usage can pass `str` paths, `numpy.ndarray`, or `PIL.Image.Image` objects as described in the API reference.
