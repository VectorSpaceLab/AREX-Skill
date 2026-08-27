# Model Family Overview

## Purpose

Read this when you need a more detailed view of the families behind `cvnets.get_model` and the kinds of inputs or heads each family expects.

## Family notes

| Family | Typical names | Inputs and compatibility notes | Common failure mode |
| --- | --- | --- | --- |
| Classification backbones | ResNet, MobileNet, MobileViT, ViT, EfficientNet, RegNet, Swin | Standard image tensors; often reused as encoders by other tasks. | Wrong pretrained head or an unsupported `__base__` name. |
| Detection models | SSD, SSDLite, Mask R-CNN | Backbone plus detection head, anchors, and matcher settings. | Class-count mismatch or encoder/head mismatch after loading pretrained weights. |
| Segmentation models | DeepLabv3, PSPNet | Image encoder plus segmentation decoder/head. | `model.segmentation.n-classes` does not match the checkpoint or dataset. |
| Multimodal models | CLIP, zero-shot image-text paths, text encoders, image projection heads | Image features plus tokenizer/prompt files and image-text dataset inputs. | Missing tokenizer files or a prompt/dataset format mismatch. |
| ByteFormer variants | Image byte encodings and audio byte encodings | Requires byte-encoding settings in the augmentation and collate pipeline. | Byte padding or encoding settings do not match the recipe. |
| Audio classification | Speech Commands and related audio-only flows | Audio transforms and audio-aware collate behavior. | Audio path or sample-length mismatch. |

## Registry and pretrained behavior

- `cvnets.get_model` builds the selected family after resolving the category and family name from the config.
- If `model.<category>.pretrained` is set, the loader resolves the weight path first and then loads it into the model.
- The repo keeps the registry split by task category, so the same family name may mean different things in different categories.
- Some families expose an exportable variant for the CoreML path; others only support the normal training/evaluation path.

## What to verify before building a model

1. The category matches the intended task.
2. The family name exists in the registry and is not `__base__`.
3. The checkpoint belongs to the same task and class count.
4. Any tokenizer, byte-encoding, or prompt files are available if the family needs them.
5. The model can print info or build a tiny smoke without requiring a missing optional backend.

## How to use the bundled helper

`scripts/check_model_build.py` loads a config, strips pretrained loading unless you explicitly allow it, and reports the model class plus an optional smoke. Use it when a registry or shape problem is more informative than a full training run.

## Read next

- `../../../references/model-overview.md` for the repo-wide family map.
- `references/troubleshooting.md` for family-specific error patterns.
- `../../../references/configuration.md` for the keys that select the family.
