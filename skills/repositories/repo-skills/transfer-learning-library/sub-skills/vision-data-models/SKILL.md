---
name: vision-data-models
description: "Operate TLLib vision datasets, ImageList formats, transforms,
  model factories, re-id metrics, and shared utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Vision Data and Models

Use this sub-skill when a task needs TLLib's vision data/model layer rather than an algorithm-specific training recipe. It covers dataset classes, local image-list formats, classification/segmentation/keypoint/re-id/object-detection model surfaces, transforms, metrics, data iterators, and logging helpers.

## Route here for

- Building or validating a local `ImageList` dataset for domain adaptation, domain generalization, task adaptation, or semi-supervised learning workflows.
- Choosing a TLLib dataset wrapper such as Office31, OfficeHome, DomainNet, VisDA2017, PACS, digit datasets, natural object recognition datasets, segmentation datasets, keypoint datasets, regression datasets, or re-identification datasets.
- Instantiating no-download model factories such as `resnet18`/`resnet50`, `lenet`, `dtn`, `deeplabv2_resnet101`, `pose_resnet101`, and re-id ResNet/ReIdentifier components.
- Using TLLib transforms, meters, `ForeverDataIterator`, `CombineDataset`, classification/segmentation accuracy helpers, confusion matrices, keypoint metrics, or re-id CMC/mAP utilities.
- Diagnosing data-list, class-index, image-size/channel, pretrained-weight, Torch/TorchVision, object-detection, or re-id dependency failures.

## Do not use this sub-skill for

- DANN/CDAN/MK-MMD/MDD/CORAL/OSBP/MCC or other domain-adaptation losses and workflows; route to `domain-adaptation` after data/model setup.
- MixStyle/StochNorm/IBN/L2-SP/DELTA/BSS/GroupDRO/domain-generalization/fine-tuning workflows; route to `task-generalization` after data/model setup.
- Pseudo-label, Mean Teacher, UDA, FixMatch, FlexMatch, or other self-training losses; route to `self-training` after data/model setup.
- Transferability ranking metrics such as H-score, LEEP, NCE, LogME, or TransRate; route to `model-selection`.
- CycleGAN/FDA/SPGAN/CyCADA image translation internals; route to `translation`.

## Operating sequence

1. Identify the task family and whether the user has local data, external data to obtain under its own license, or only a synthetic/smoke fixture.
2. For local classification-style data, validate the image-list file with `scripts/validate_imagelist.py` before wiring it into a training command.
3. Choose data transforms and model factories from `references/vision-data-and-models.md`; avoid pretrained downloads unless the user explicitly allows network/cache use.
4. For re-identification, use `references/reid-and-metrics.md` for dataset tuple conventions, model/loss surfaces, and CMC/mAP behavior.
5. For failures, start with `references/troubleshooting.md` before changing dependencies or dataset layout.
6. For an import/model/data smoke check in an installed environment, run `scripts/tllib_vision_smoke.py`.

## Bundled references

- `references/datasets-and-formats.md` - dataset classes, no-download policy, ImageList/MultipleDomainsDataset/SegmentationList/re-id/keypoint/regression format contracts.
- `references/vision-data-and-models.md` - transforms, model factories, task-specific model surfaces, utilities, meters, loggers, metrics.
- `references/reid-and-metrics.md` - person re-id datasets, samplers, models, losses, CMC/mAP/re-ranking, validation conventions.
- `references/troubleshooting.md` - broken links, licenses, path/label mistakes, TorchVision compatibility, pretrained downloads, image shape/channel issues, optional dependency problems.

## Bundled scripts

- `scripts/validate_imagelist.py`: safe local `ImageList` format validator. It does not download data and can create a TLLib `ImageList` object from an installed `tllib` package.
- `scripts/tllib_vision_smoke.py`: no-network CPU smoke for installed `tllib` vision datasets, transforms, models, metrics, and utility imports. Object-detection imports are reported as optional if Detectron2 is unavailable.
