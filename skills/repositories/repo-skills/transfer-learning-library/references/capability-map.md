# TLLib Capability Map

Use this when a user names an algorithm, module, dataset, metric, or example family and you need to route to the right sub-skill.

## Algorithm and module routes

| Signal | TLLib package area | Owning sub-skill | Notes |
| --- | --- | --- | --- |
| DANN, CDAN, ADDA, domain discriminator, gradient reversal | `tllib.alignment.dann`, `cdan`, `adda`, `tllib.modules.domain_discriminator`, `tllib.modules.grl` | `domain-adaptation` | CPU-smokeable losses; full benchmarks need source/target data and usually GPU. |
| DAN, JAN, MK-MMD, JMMD, Gaussian kernels | `tllib.alignment.dan`, `jan`, `tllib.modules.kernels` | `domain-adaptation` | Ensure source/target feature tensors have compatible dimensions. |
| MDD, MCD, RSD, RegDA, OSBP, BSP, AFN, MCC | `tllib.alignment.*`, `tllib.normalization.afn`, `tllib.self_training.mcc` | `domain-adaptation` | MCC can also be SSL regularization; route by task intent. |
| Partial DA weights, IWAN, PADA | `tllib.reweight.iwan`, `tllib.reweight.pada` | `domain-adaptation` | Needs classifier/discriminator outputs over source/target label spaces. |
| D-adapt object detection | `tllib.alignment.d_adapt`, `tllib.vision.models.object_detection` | `domain-adaptation` + `vision-data-models` | Optional Detectron2/MMCV stack; not part of minimum install. |
| Office31, OfficeHome, DomainNet, VisDA, PACS, ImageList, MultipleDomainsDataset | `tllib.vision.datasets` | `vision-data-models` | Use local data when downloads fail; validate `ImageList` files first. |
| ResNet, LeNet, DTN, DeeplabV2, PoseResNet, re-id ResNet | `tllib.vision.models` | `vision-data-models` | TLLib 0.4 model imports are sensitive to TorchVision versions. |
| Re-id metrics and losses | `tllib.utils.metric.reid`, `tllib.vision.models.reid` | `vision-data-models` | Full re-id training examples are data/GPU-heavy. |
| MixStyle, IBN, StochNorm, CORAL for DG, GroupDRO | `tllib.normalization`, `tllib.alignment.coral`, `tllib.reweight.groupdro` | `task-generalization` | Route target-domain adaptation with unlabeled target data back to `domain-adaptation`. |
| L2-SP, DELTA, BSS, Co-Tuning, LwF, Bi-Tuning | `tllib.regularization` | `task-generalization` | Fine-tuning workflows require pretrained checkpoints and labeled target data. |
| Pseudo Label, Pi Model, Mean Teacher, UDA, FixMatch/FlexMatch, Self-Tuning, DST, Noisy Student | `tllib.self_training` | `self-training` | Focus on labeled/unlabeled loaders, threshold schedules, teacher updates, and consistency losses. |
| H-score, regularized H-score, LEEP, NCE, LogME, TransRate | `tllib.ranking` | `model-selection` | CPU-friendly metrics over features, labels, or source-model prediction probabilities. |
| CycleGAN, FDA, CyCADA, SPGAN | `tllib.translation` | `translation` | Component APIs are CPU-smokeable; full training/translation pipelines are data/GPU-heavy. |

## Example family routes

| Example family | Owning route | Optional dependencies to check |
| --- | --- | --- |
| `domain_adaptation/image_classification`, `partial_domain_adaptation`, `openset_domain_adaptation`, `image_regression`, `keypoint_detection`, `semantic_segmentation`, `re_identification` | `domain-adaptation` | Often `timm`, OpenCV, datasets, CUDA. |
| `domain_adaptation/object_detection` and `d_adapt` | `domain-adaptation` plus `vision-data-models` | Detectron2, MMCV, Pascal VOC writer, CUDA-compatible Torch. |
| `domain_adaptation/wilds_*` | `domain-adaptation` | WILDS, TensorFlow/TensorBoard, Transformers, PyG/OGB for text/molecule variants. |
| `domain_generalization/*` | `task-generalization` | `timm`, `wilds`, `higher`, datasets, CUDA for practical training. |
| `task_adaptation/image_classification` | `task-generalization` | `timm`, pretrained checkpoints, labeled target datasets. |
| `semi_supervised_learning/image_classification` | `self-training` | `timm`, labeled/unlabeled splits, optional MoCo checkpoints. |
| `model_selection` | `model-selection` | `timm` only for example feature extraction; ranking metrics themselves are CPU-friendly. |

## Validation routes

- Install/import compatibility: root `scripts/check_tllib_install.py`.
- Domain adaptation API smoke: `sub-skills/domain-adaptation/scripts/tllib_domain_adaptation_smoke.py`.
- Dataset/model utility checks: `sub-skills/vision-data-models/scripts/tllib_vision_smoke.py` and `validate_imagelist.py`.
- Task/DG/fine-tuning component smoke: `sub-skills/task-generalization/scripts/tllib_task_generalization_smoke.py`.
- Self-training component smoke: `sub-skills/self-training/scripts/tllib_self_training_smoke.py`.
- Ranking metric smoke: `sub-skills/model-selection/scripts/tllib_ranking_smoke.py`.
- Translation component smoke: `sub-skills/translation/scripts/tllib_translation_smoke.py`.
