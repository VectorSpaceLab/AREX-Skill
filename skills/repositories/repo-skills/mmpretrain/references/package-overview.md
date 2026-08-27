# MMPreTrain package overview

MMPreTrain is an OpenMMLab PyTorch toolbox for image classification, self-supervised pretraining, retrieval, and multi-modal vision-language tasks. Use this overview to orient routing before opening a focused sub-skill.

## Main surfaces

| Surface | Use | Skill route |
| --- | --- | --- |
| Model zoo and APIs | `list_models`, `get_model`, `inference_model`, task inferencers, feature extraction | `sub-skills/model-zoo-inference/SKILL.md` |
| Config-driven experiments | Python config inheritance, train/test commands, resume/AMP/TTA, distributed/Slurm planning | `sub-skills/training-and-evaluation/SKILL.md` |
| Datasets and registries | `CustomDataset`, ImageNet, OpenMMLab 2.0 annotations, pipelines, custom model/metric/dataset classes | `sub-skills/datasets-and-customization/SKILL.md` |
| Analysis and deployment utilities | JSON logs, metrics, confusion matrix, FLOPs, CAM, t-SNE, checkpoint conversion/publishing, TorchServe | `sub-skills/tools-analysis-and-deployment/SKILL.md` |

## Public API entry points

Common imports:

```python
from mmpretrain import list_models, get_model, inference_model
from mmpretrain import ImageClassificationInferencer, FeatureExtractor
```

Model construction defaults are important:

- `get_model(..., pretrained=False)` does not download weights by default.
- Inferencer classes default to `pretrained=True`; pass `pretrained=False` for architecture-only or offline smoke checks.
- `device='cpu'` is valid for package inspection and small CPU runs. Use `device='cuda'` only after the environment has a compatible PyTorch/MMCV backend.

## Config families

MMPreTrain ships many config families covering classic CNNs, transformers, self-supervised methods, retrieval, and multi-modal models. Configs inherit from `_base_` components for model, dataset, schedule, and runtime. Use the training sub-skill to inspect a merged config before changing nested fields.

## Optional capabilities

| Capability | Extra requirement | Notes |
| --- | --- | --- |
| Multi-modal models | `mmpretrain[multimodal]` or equivalent dependencies such as Transformers/PyCOCOTools | Needed for captioning, VQA, grounding, and some retrieval tasks. |
| CAM visualization | `grad-cam` compatible with the installed PyTorch | Route to tools sub-skill; choose target layers carefully for ViT-like models. |
| t-SNE and some analysis utilities | `scikit-learn`, plotting dependencies | Avoid interactive display in headless sessions. |
| TorchServe packaging | TorchServe, Java/service runtime, model archiver | Reference-only unless the user explicitly wants service setup. |
| CUDA/distributed training | CUDA-capable PyTorch/MMCV, driver, GPUs, NCCL/network | CPU import does not prove CUDA readiness. |

## Validation hierarchy

1. Run `scripts/check_mmpretrain_env.py` for import, dependency, backend, model-zoo, and no-download model-build checks.
2. Use focused sub-skill scripts to inspect model names, configs, datasets, logs, or checkpoints.
3. Only then run package-level train/test/inference commands that may download weights, read datasets, allocate GPUs, or write work directories.
