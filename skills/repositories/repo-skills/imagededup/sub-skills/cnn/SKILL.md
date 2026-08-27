---
name: cnn
description: "Find duplicate images with CNN encodings, pretrained backbones, or
  custom PyTorch models in imagededup."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# cnn

Use this sub-skill when the user wants CNN-based encodings, cosine-similarity duplicate search, pretrained backbones, or custom PyTorch models.

## Best-fit tasks

- Encode one image or a directory with `CNN`.
- Find duplicates from CNN feature vectors.
- Use a pretrained `MobilenetV3`, `ViT`, or `EfficientNet` wrapper.
- Build a `CustomModel` around a user-defined PyTorch module.
- Understand CUDA-versus-CPU behavior for the CNN workflow.

## Read this sub-skill first when the request mentions

- `CNN`
- `CustomModel`
- `MobilenetV3`, `ViT`, or `EfficientNet`
- torch or torchvision
- cosine similarity
- `min_similarity_threshold`
- pretrained weights or model configuration
- custom feature extractors

## Workflow overview

1. Decide whether the user wants the default pretrained model or a custom model.
2. Make sure the model returns a feature tensor with shape `(batch, features)`.
3. Encode either a single image or a directory.
4. Search duplicates from the encoding map or directly from the directory.
5. If the user wants a removal list, convert the duplicate map to filenames to remove.

## Common decisions

- Use `CNN()` when the user wants the default MobileNetV3-based workflow.
- Use `CustomModel` when the user wants to plug in a different PyTorch model.
- Use `encode_image` for one file or numpy array.
- Use `encode_images` for a directory.
- Use `find_duplicates` when the user needs the full duplicate map.
- Use `find_duplicates_to_remove` when the user wants a heuristic removal list.

## Helpful facts

- `CNN` uses CUDA automatically when available and otherwise uses CPU.
- The default backbone is `MobilenetV3`.
- Pretrained wrappers for `ViT` and `EfficientNet` are also bundled.
- `scores=True` returns cosine similarities.
- `min_similarity_threshold` is a float in `[-1.0, 1.0]`.
- `num_enc_workers` only parallelizes encoding on Linux.
- `find_duplicates` can accept either `image_dir` or `encoding_map`.

## Model contract

A custom model should:

- be a PyTorch module or call-compatible object
- accept the transform output
- return a tensor whose last dimension is the feature dimension
- be paired with a transform that matches the model's preprocessing needs

The bundled pretrained wrappers already provide matching transforms and names.

## GPU and CPU notes

- The CNN path is the only part of this repo that can benefit from CUDA.
- CPU fallback is supported, so CUDA is optional rather than required.
- If a GPU is available, `CNN()` should report `cuda` as its device.
- First use of the default pretrained backbone may download weights if they are not cached.

## Troubleshooting pointer

Read [`references/troubleshooting.md`](references/troubleshooting.md) for model-config validation, threshold errors, worker-count warnings, CUDA selection, and weight-download issues.

## Script helper

Run [`scripts/cnn_smoke.py`](scripts/cnn_smoke.py) to exercise a synthetic CNN workflow with either a lightweight custom model or the pretrained default path.

## When to escalate elsewhere

- If the task is only about hash methods, switch to the hashing sub-skill.
- If the task is about scoring or plotting a retrieved duplicate map, switch to the evaluation sub-skill.

## Good output expectations

A good CNN-oriented answer should usually include:

- the model choice
- whether the workflow is pretrained or custom
- the expected feature shape or score behavior
- the device behavior on the current host
- any weight-download or worker-count caveat that applies