# TorchVision Package Overview

TorchVision is organized around public Python modules that complement PyTorch for computer vision.

## Public Module Map

| Module | Main use | Skill route |
| --- | --- | --- |
| `torchvision.models` | Model builders, task subpackages, pretrained weight enums, model lookup, feature extraction | `sub-skills/models-and-weights/` |
| `torchvision.transforms` and `torchvision.transforms.v2` | Image/video/annotation transforms, augmentation, conversion, normalization | `sub-skills/transforms-and-tv-tensors/` |
| `torchvision.tv_tensors` | Tensor subclasses carrying image, video, mask, bounding-box, and keypoint metadata | `sub-skills/transforms-and-tv-tensors/` |
| `torchvision.datasets` | Built-in datasets, base classes, folder datasets, fake data, v2 wrapping | `sub-skills/datasets-io-utils/` |
| `torchvision.io` | Image decoding/encoding and file reads/writes | `sub-skills/datasets-io-utils/` |
| `torchvision.utils` | Grids, bounding-box/mask/keypoint drawing, optical-flow visualization | `sub-skills/datasets-io-utils/` |
| `torchvision.ops` | Boxes, IoU, NMS, ROI ops, FPN helpers, losses, detection layers | `sub-skills/ops-and-detection/` |
| Reference training recipes | Official task training/evaluation command patterns | `sub-skills/training-references/` |

## Installation Assumptions

TorchVision must match the installed PyTorch version and backend. A mismatched pair is the most common cause of custom-op errors such as missing `torchvision::nms`.

For normal package use, install TorchVision through the same PyTorch channel or wheel index used for PyTorch. For source checkouts, build the C++ extension before expecting `torchvision.ops` or detection models to work.

## Release Status Signals

TorchVision docs classify APIs as stable, beta, or prototype. Be conservative with beta/prototype behavior in generated code: include version checks, keep tests narrow, and avoid promising long-term compatibility.

## Network and Cache Behavior

Pretrained model weights can download through PyTorch Hub when a weights enum is used. Dataset constructors can download and extract data when `download=True`. For tests, CI, and offline examples, prefer `weights=None`, tiny fixtures, and `FakeData`.

## Optional or Environment-Sensitive Surfaces

- Image codecs depend on the installed TorchVision binary and linked image libraries.
- Detection/ROI/NMS operators depend on the compiled TorchVision extension.
- Video decoding APIs are no longer the preferred path; use TorchCodec for videos and audio when possible.
- Reference training scripts often require datasets, distributed launch, GPUs, and latest source compatibility.
