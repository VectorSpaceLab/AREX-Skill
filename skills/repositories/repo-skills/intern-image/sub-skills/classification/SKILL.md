---
name: classification
description: "Image classification workflows for InternImage backbones: data
  layouts, configs, train/eval/throughput, DeepSpeed/Accelerate, feature
  extraction, Hugging Face, and export routing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# InternImage classification

Use this sub-skill when the user is working with InternImage image classification: ImageNet or iNaturalist data layout, model/config selection, evaluation, training, throughput checks, DeepSpeed or Accelerate launch planning, intermediate feature extraction, or Hugging Face Transformers inference/conversion.

## Routing

- For standard classification runs, first gather: task (`eval`, `train`, `throughput`, `extract features`, `Transformers`), InternImage checkout location, config label, checkpoint or pretrained weight, data root, GPU count, launcher style, output directory, and any YACS overrides.
- Use the bundled command builder instead of rewriting upstream shell scripts by hand:
  `python scripts/build_classification_command.py --help`
- Put long command recipes, data layouts, and feature-extraction details in `references/workflows.md`.
- Put YACS config defaults, config-family selection, model-builder arguments, and override keys in `references/configuration.md`.
- Put Transformers model IDs, `trust_remote_code` usage, and conversion notes in `references/huggingface.md`.
- Put classification-specific failure handling in `references/troubleshooting.md` before recommending a rerun.

## Boundaries

- Stay in this sub-skill for image-classification commands and classification-specific Hugging Face usage.
- Route DCNv3 CUDA-extension build diagnosis, TensorRT custom-op setup, and ONNX/TensorRT export execution to the sibling deployment sub-skill. Keep only the classification model name, config, and checkpoint selection here.
- Do not claim that full training, evaluation, throughput, feature extraction, Hugging Face downloads, DCNv3 CUDA builds, or TensorRT export were verified by this generated skill. The selected verification scope covered self-contained helper checks and static source distillation; dataset/GPU/network-heavy runs remain user-approved runtime actions.

## Quick command-builder examples

```bash
# Build a one-GPU ImageNet evaluation template.
python scripts/build_classification_command.py \
  --mode eval \
  --config configs/internimage_b_1k_224.yaml \
  --checkpoint CHANGE_ME/internimage_b_1k_224.pth \
  --data-path CHANGE_ME/imagenet \
  --gpus 1

# Build an intermediate-feature extraction template.
python scripts/build_classification_command.py \
  --mode extract-features \
  --config configs/internimage_t_1k_224.yaml \
  --checkpoint CHANGE_ME/internimage_t_1k_224.pth \
  --image CHANGE_ME/image.png \
  --keys patch_embed levels.0.downsample \
  --save-features

# Build a Hugging Face Transformers inference template.
python scripts/build_classification_command.py \
  --mode hf-transformers \
  --hf-model OpenGVLab/internimage_t_1k_224 \
  --hf-task both \
  --image CHANGE_ME/image.png
```
