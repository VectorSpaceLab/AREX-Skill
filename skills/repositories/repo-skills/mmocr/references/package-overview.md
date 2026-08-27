# MMOCR package overview

MMOCR is an OpenMMLab toolbox for text detection, text recognition, end-to-end OCR/text spotting, and key information extraction (KIE). It is built on PyTorch, MMEngine, MMCV, and MMDetection. Use this overview to choose the right sub-skill and to understand what runtime resources are required.

## Capability map

| User task | Route | Notes |
|---|---|---|
| Run OCR on images, directories, arrays, or save predictions/visualizations | `sub-skills/ocr-inference/` | Covers `MMOCRInferencer` and task-specific inferencers. |
| Train, test, evaluate, inspect configs, choose model families, or debug work directories/checkpoints | `sub-skills/training-evaluation-configs/` | Covers OpenMIM command shapes, config smoke checks, model families, distributed/Slurm notes. |
| Prepare datasets, inspect dataset_zoo-style metadata, validate annotation formats, or debug LMDB/data layouts | `sub-skills/data-preparation/` | Covers textdet/textrecog/textspotting/KIE data workflows and safe dataset preflight. |
| Extend components, registries, DataSamples, transforms, dictionaries, metrics, visualizers, or OpenMMLab projects | `sub-skills/model-api-components/` | Covers component-level APIs and extension patterns. |

## Public install shape

A typical package environment needs Python, PyTorch/torchvision, MMEngine, MMCV, MMDetection, and MMOCR runtime dependencies. The project documentation recommends OpenMIM for OpenMMLab dependencies:

```bash
pip install -U openmim
mim install mmengine
mim install mmcv
mim install mmdet
mim install mmocr
```

For a source or editable install, use the package's documented source workflow and then run the root environment check script from this skill. Do not copy the private inspection environment used during skill generation.

## Minimal checks

```bash
python scripts/check_mmocr_environment.py
python scripts/check_mmocr_environment.py --config CONFIG --require-default-scope mmocr
```

Expected success signals:

- `mmocr`, `mmcv`, `mmengine`, `mmdet`, `torch`, and `cv2` import.
- Public MMOCR inferencers import from `mmocr.apis`.
- Optional config loading reports `default_scope=mmocr` and a plausible `model_type`.
- CUDA is reported honestly as available or unavailable; CPU-only success is not GPU verification.

## Backends and resources

| Resource | Status in this generated skill | Guidance |
|---|---|---|
| CPU | Required for import, config, helper scripts, and CPU-safe native checks | Sufficient for most skill validation and many debugging tasks. |
| CUDA/GPU | Optional for accelerated inference/training/evaluation | Use only when the user's environment has compatible PyTorch/MMCV CUDA wheels and visible devices. |
| Distributed/NCCL | Optional | Required only for multi-GPU/multi-node training/testing. Verify ports and GPU counts. |
| Slurm | Optional service backend | Requires cluster policy, partition, allocation, and scheduler access. |
| Network/model downloads | Optional | Pretrained aliases or dataset preparers may download weights/data; ask before relying on network/cache. |
| GUI/display | Optional | Prefer saved visualizations (`out_dir`, `save_vis`, `show_dir`) on headless servers. |

## Evidence-backed module surfaces

- Inference APIs: `MMOCRInferencer`, `TextDetInferencer`, `TextRecInferencer`, `KIEInferencer`, `TextSpotInferencer`.
- Data samples: `TextDetDataSample`, `TextRecogDataSample`, `KIEDataSample`, `TextSpottingDataSample`.
- Main model families: DBNet, DBNet++, DRRG, FCENet, Mask R-CNN wrapper, PANet, PSENet, TextSnake, ABINet, ASTER, CRNN, MASTER, NRTR, RobustScanner, SAR, SATRN, SVTR, and SDMGR.
- Data tasks: text detection, text recognition, text spotting, KIE; recognition can use LMDB; KIE needs explicit class/relation semantics.

## Source-to-skill adaptation summary

The generated skill does not require future agents to run original repository scripts. Instead it bundles safe helpers:

- `scripts/check_mmocr_environment.py` for import/backend/config checks.
- `sub-skills/ocr-inference/scripts/mmocr_inference_smoke.py` for inference preflight and opt-in execution.
- `sub-skills/training-evaluation-configs/scripts/mmocr_config_smoke.py` for config summaries.
- `sub-skills/data-preparation/scripts/mmocr_dataset_preflight.py` for dataset metadata and tiny annotation checks.
- `sub-skills/model-api-components/scripts/mmocr_component_registry_probe.py` for registry/DataSample/dictionary probes.

Large, networked, GUI, training-scale, distributed, or maintainer-only source workflows are distilled into references with explicit prerequisites and stop conditions.
