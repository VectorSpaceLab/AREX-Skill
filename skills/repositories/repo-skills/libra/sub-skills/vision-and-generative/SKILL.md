---
name: vision-and-generative
description: "Use Libra for image classification, GANs, read-mode inspection,
  pretrained/custom CNN export, and feature-map/debug workflows on image
  datasets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Vision and Generative Workflows with Libra

Load this sub-skill when a task uses Libra image workflows: CNN classification, image read-mode selection, image preprocessing, pretrained/custom CNN architectures, feature-map visualization, TensorFlowJS/TFLite export, or DCGAN image generation.

## What this sub-skill owns
- `convolutional_query(...)` for image classification
- `gan_query(...)` for DCGAN generation from a single class of images
- image data layouts: `setwise`, `classwise`, `csvwise`, and already-processed directories
- `pretrained`, `custom_arch`, `show_feature_map`, `save_as_tfjs`, and `save_as_tflite` constraints
- image preprocessing side effects such as `proc_training_set`, `proc_testing_set`, `tfjsmodel`, `model.tflite`, and `generated_images`

## Trigger phrases
Use this route when a user asks to:
- train a CNN from folders of images
- decide which `read_mode` or `image_column` to pass
- use VGG, ResNet, MobileNet, DenseNet, or a custom Keras JSON architecture
- export a trained image classifier to TFJS/TFLite
- view feature maps after CNN training
- generate images with Libra's GAN path
- diagnose image folder/class count/path issues

## Bundled references
- `references/api-reference.md` for method parameters and model keys
- `references/workflows.md` for image classification and GAN recipes
- `references/data-formats.md` for image dataset layouts
- `references/export-and-preprocessing.md` for preprocessing/export side effects
- `references/troubleshooting.md` for read-mode, pretrained/custom architecture, GPU, and TFJS failures

## Bundled scripts
- `scripts/inspect_image_dataset.py` inspects a folder or CSV and suggests a safe `read_mode`/`image_column` direction.
- `scripts/smoke_cnn_layout.py` creates a tiny synthetic image tree and verifies that the layout helper sees a classwise dataset. It does not train a CNN.

## Operating notes
1. Treat image training as potentially expensive. Start with layout inspection and a tiny epoch count before full runs.
2. `custom_arch` requires `preprocess=False`; the source raises if both `custom_arch` and preprocessing are requested.
3. Pretrained models require 224x224 inputs when using ImageNet weights.
4. `save_as_tfjs=True` writes `tfjsmodel`; `save_as_tflite=True` writes `model.tflite` in the current working directory.
5. GAN output is written under `generated_images` relative to the image data path in the inspected code.
6. Image captioning uses image files but is routed through `sub-skills/nlp-and-generation` because the public client methods live there. Use this sub-skill only for image path/layout debugging around captioning.

## Cross-links
- Use the root skill for install/import compatibility and TensorFlowJS/JAX version notes.
- Route text-only generation and image captioning model calls to `sub-skills/nlp-and-generation`.
- Route tabular `analyze()`, recommendation, and dashboard tasks to `sub-skills/tabular-modeling` unless the model key is `convolutional_NN`.
