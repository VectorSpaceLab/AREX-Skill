# Cross-cutting TLLib Troubleshooting

Use this before debugging a specific algorithm. Route to the nearest sub-skill troubleshooting page after the package, dependency, data, and backend basics are stable.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `AttributeError: module 'numpy' has no attribute 'float'` | TLLib 0.4 uses deprecated NumPy aliases removed in NumPy 1.24. | Use `numpy<1.24` for TLLib 0.4, for example `numpy==1.23.5`, or patch the user's project deliberately. Re-run the root install check. |
| `ImportError: cannot import name 'model_urls' from torchvision.models.resnet` | Modern TorchVision removed APIs expected by TLLib 0.4 model factories. | Use an older compatible Torch/TorchVision pair for TLLib model APIs, or patch TLLib imports in the user's project. Do not treat this as a dataset or algorithm error. |
| `ModuleNotFoundError: torchvision.models.utils` | Same modern TorchVision compatibility problem, often triggered by segmentation model imports. | Use a TLLib-era TorchVision stack before running segmentation/keypoint/model factory workflows. |
| `ModuleNotFoundError: detectron2`, `mmcv`, `wilds`, `timm`, `higher`, `transformers`, `torch_geometric`, or `ogb` | Optional example dependency not included in the base package. | Install only the optional stack for the selected workflow. Avoid installing all example requirements unless the user explicitly needs them. |
| `pip check` reports dependency conflicts after installing latest packages | TLLib 0.4 is older and has unpinned lower bounds. | Prefer compatible pins over newest packages. A known CPU inspection stack is Python 3.8, PyTorch 1.8.1, TorchVision 0.9.1, and NumPy 1.23.5. |

## Backend and runtime failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| CUDA unavailable but component smoke passes on CPU | The selected check validates public APIs, not benchmark training speed. | It is acceptable for API guidance. For real training, install a CUDA-compatible PyTorch stack and verify `torch.cuda.is_available()` before running long jobs. |
| Out-of-memory or very slow benchmark training | Original examples are research-scale and often assume GPU/data/checkpoints. | Reduce batch size/workers/image size/epochs, validate a tiny dry run, or treat the request as a downstream experiment requiring explicit compute budget. |
| Distributed WILDS/re-id/training launch fails | Multi-GPU launcher, dataset path, or optional dependency mismatch. | First run a single-process smoke or parser check. Confirm dataset roots and optional packages before distributed launch. |
| Detectron2 build or import fails | Detectron2 must match Python, PyTorch, CUDA, compiler, and GPU stack. | Use Detectron2's compatible wheel/build instructions for the user's exact stack; do not install it for non-detection TLLib tasks. |

## Dataset and download failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Dataset URL is broken or download stalls | TLLib documents broken dataset-link issues; many datasets are externally hosted. | Prefer user-provided local datasets. Read `vision-data-models` data-format guidance and validate paths with `validate_imagelist.py`. |
| `FileNotFoundError` for image paths | `ImageList` paths are relative to the dataset root or the list file has wrong separators. | Validate the list with `sub-skills/vision-data-models/scripts/validate_imagelist.py --root <root> --list-file <list>`. |
| Label index out of range | Class list and list-file labels disagree. | Provide explicit class names in label order or regenerate the list file. Check that labels are zero-based integers. |
| Dataset works in one example but not another | Example families use different dataset wrappers/domains/splits. | Route dataset/model questions to `vision-data-models` and algorithm-specific CLI choices to the owning workflow sub-skill. |

## Workflow misuse patterns

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Source/target tensor shape mismatch in losses | Domain adaptation losses need matching feature dimensions and compatible batch assumptions. | Run the domain-adaptation smoke, inspect feature shapes, and route to `domain-adaptation` API guidance. |
| Classifier head output dimension mismatch | `num_classes`, partial/open-set label space, or pretrained checkpoint head does not match target classes. | Route to `vision-data-models` for model/head setup and to the workflow sub-skill for algorithm-specific label-space handling. |
| Ranking metrics return NaN/inf or contradictory scores | Features/predictions/labels have wrong shape, singular covariance, unnormalized probabilities, or too few samples per class. | Route to `model-selection` and run its ranking smoke on a tiny fixture before user data. |
| Self-training selects no pseudo labels | Confidence threshold too high, logits/probabilities wrong, or weak/strong predictions swapped. | Route to `self-training` troubleshooting and lower the threshold only after checking tensor shapes and probability conventions. |
| Checkpoint conversion/fine-tuning loads but training is unstable | Pretrained backbone, classifier head, optimizer groups, or regularizer weight is mismatched. | Route to `task-generalization` checkpoint and regularization guidance. |

## Safe validation order

1. Run `scripts/check_tllib_install.py`.
2. Route to the owning sub-skill and run its bundled smoke script.
3. Validate dataset paths/list files before launching any training.
4. Install optional dependencies only for the chosen workflow.
5. Treat full benchmark reproduction as a separate, explicitly budgeted downstream task.
