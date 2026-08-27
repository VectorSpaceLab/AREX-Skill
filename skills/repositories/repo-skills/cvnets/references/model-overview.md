# CVNets Model Overview

## Purpose

Read this when the user is choosing a model family, trying to understand how the registry is organized, or debugging a mismatch between the dataset category and the selected model.

## Registry behavior

- `cvnets.get_model` looks up the model by `dataset.category` and `model.<category>.name` unless those values are passed explicitly.
- The selected model may load pretrained weights from `model.<category>.pretrained` before being frozen according to the options.
- The task-specific base names such as `__base__` are reserved for registry plumbing and are not valid final model names.
- `model.info()` is printed on the master process in the main training/evaluation paths.
- Some models expose `get_exportable_model()` so the CoreML path can switch into an export-friendly representation.

## Major task families

| Family | Representative names or subfamilies | Key config signals | Notes |
| --- | --- | --- | --- |
| Classification | ResNet, MobileNet, MobileViT, ViT, EfficientNet, RegNet, Swin, ByteFormer | `dataset.category=classification`, `model.classification.name` | The repo's main image-classification route. ByteFormer also covers byte-based image and audio variants. |
| Detection | SSD, SSDLite, Mask R-CNN | `dataset.category=detection`, `model.detection.name`, anchor/matcher arguments | Detection encoders are often reused from the classification family. |
| Segmentation | DeepLabv3, PSPNet | `dataset.category=segmentation`, `model.segmentation.name` | Segmentation often reuses a classification encoder and changes the head and class count. |
| Multimodal | CLIP, image-text zero-shot, text encoders, image projection heads | `dataset.category=multi_modal_img_text`, `model.multi_modal_img_text.name`, `text_tokenizer.clip.*` | The model choice is tightly coupled to prompt/tokenizer setup and the image-text dataset layout. |
| Audio / bytes | Speech Commands, audio ByteFormer, byte-encoded image recipes | `dataset.category=audio_classification` or byte-based classification configs | These workflows care about audio transforms, byte encodings, and collate behavior as much as the model itself. |
| Exportable / profiled paths | CoreML export, JIT-friendly benchmarking, exportable modules | `conversion.*`, `benchmark.*` | The model must expose export-friendly behavior for the export path to succeed. |

## Good selection workflow

1. Identify the task category first.
2. Read the matching config section and the model family in `model.<category>.name`.
3. Check whether the task reuses a backbone from another family; detection and segmentation often do.
4. Confirm whether the model needs text, byte, or video-specific inputs in addition to image tensors.
5. Decide whether you need pretrained weights, exportable modules, or just a registry build.

## Common model-level pitfalls

- Choosing `__base__` as a final name instead of a concrete registered family.
- Loading pretrained weights that were trained for a different head or class count.
- Forgetting that CLIP and ByteFormer have extra tokenizer or byte-encoding requirements outside the pure image path.
- Assuming every family can be safely exported without checking the export path or optional dependencies.

## Read next

- `references/configuration.md` for the keys that select the family.
- `sub-skills/models-and-architectures/references/model-overview.md` for deeper model-family notes.
- `sub-skills/models-and-architectures/references/troubleshooting.md` for model registry and shape-mismatch failures.
