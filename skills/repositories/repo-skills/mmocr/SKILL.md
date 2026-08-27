---
name: mmocr
description: "Use MMOCR for OCR inference, dataset preparation, config-driven
  training/evaluation, model components, registries, and OpenMMLab OCR
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMOCR

Use this repo skill when a task involves OpenMMLab MMOCR: text detection, text recognition, OCR chains, text spotting, key information extraction (KIE), OCR datasets, config-driven training/evaluation, or MMOCR component extension.

## Start here

1. Read [`references/package-overview.md`](references/package-overview.md) for the package capability map, public install shape, backend expectations, and bundled helper summary.
2. Run [`scripts/check_mmocr_environment.py`](scripts/check_mmocr_environment.py) when you need to verify imports, dependency versions, CUDA visibility, or optional config loading.
3. Use the route map below for workflow details.
4. Read [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting install/import/backend/download/headless-display failures.
5. Check [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill matches a newer checkout or package version.

## Minimal public install and import check

MMOCR depends on PyTorch, MMEngine, MMCV, and MMDetection. The project recommends OpenMIM for OpenMMLab packages:

```bash
pip install -U openmim
mim install mmengine
mim install mmcv
mim install mmdet
mim install mmocr
```

Then verify the environment from any working directory:

```bash
python scripts/check_mmocr_environment.py
```

For config work, verify that the config loads and uses the MMOCR registry scope:

```bash
python scripts/check_mmocr_environment.py --config CONFIG --require-default-scope mmocr
```

A CPU import/config check is not proof of CUDA, distributed, or Slurm readiness. Require real backend checks before claiming those paths work.

## Route map

| User asks for... | Read |
|---|---|
| OCR inference over images/folders/arrays, `MMOCRInferencer`, task inferencers, saved predictions/visualizations, model aliases, KIE chains, or headless inference troubleshooting | [`sub-skills/ocr-inference/SKILL.md`](sub-skills/ocr-inference/SKILL.md) |
| Config inspection, model-family selection, training/testing/evaluation command construction, work directories, checkpoints, AMP, TTA, distributed launch, or Slurm routing | [`sub-skills/training-evaluation-configs/SKILL.md`](sub-skills/training-evaluation-configs/SKILL.md) |
| Dataset preparation, dataset_zoo-style metadata, textdet/textrecog/textspotting/KIE annotation formats, LMDB recognition data, or dataset-layout debugging | [`sub-skills/data-preparation/SKILL.md`](sub-skills/data-preparation/SKILL.md) |
| Registries, DataSamples, transforms, model components, dictionaries, metrics, visualizers, custom modules, or OpenMMLab project extensions | [`sub-skills/model-api-components/SKILL.md`](sub-skills/model-api-components/SKILL.md) |

## Common decisions

- For image prediction, use `ocr-inference`; for dataset evaluation against a checkpoint, use `training-evaluation-configs`.
- For any train/test command, run the config smoke script first and confirm data/checkpoint availability before launching expensive work.
- For private datasets, start with `data-preparation` and validate the annotation/task choice before editing training configs.
- For registry or custom module errors, use `model-api-components` before trying another long run.
- For remote servers, prefer saved visualization files over GUI display.
- For pretrained aliases or dataset preparers, ask before using network downloads or shared caches.

## Backend policy

- CPU is enough for import checks, config smoke, dataset metadata preflight, registry probes, and many troubleshooting tasks.
- CUDA/GPU is optional but required for honest accelerated inference/training/evaluation verification.
- Distributed/NCCL and Slurm are optional operational backends; do not infer them from CPU success.
- Long training, large evaluation, model downloads, dataset downloads, and scheduler jobs need explicit user approval.

## Bundled helpers

- [`scripts/check_mmocr_environment.py`](scripts/check_mmocr_environment.py): root import/version/backend/config smoke.
- [`sub-skills/ocr-inference/scripts/mmocr_inference_smoke.py`](sub-skills/ocr-inference/scripts/mmocr_inference_smoke.py): inference preflight and opt-in execution helper.
- [`sub-skills/training-evaluation-configs/scripts/mmocr_config_smoke.py`](sub-skills/training-evaluation-configs/scripts/mmocr_config_smoke.py): config summary without training.
- [`sub-skills/data-preparation/scripts/mmocr_dataset_preflight.py`](sub-skills/data-preparation/scripts/mmocr_dataset_preflight.py): dataset metadata and tiny annotation checks.
- [`sub-skills/model-api-components/scripts/mmocr_component_registry_probe.py`](sub-skills/model-api-components/scripts/mmocr_component_registry_probe.py): registry, DataSample, and dictionary probe.

## Non-goals

- This skill does not replace MMOCR's package installation or model weights.
- It does not bundle full training/evaluation launchers, pretrained checkpoints, datasets, or GUI assets.
- It does not claim CUDA, distributed, or Slurm readiness unless the caller verifies those backends in their runtime.
