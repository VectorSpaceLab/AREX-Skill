# Package overview

Read this for cross-cutting docTR package facts before choosing a sub-skill.

## Identity

- Public project: **docTR** (Document Text Recognition).
- Distribution: `python-doctr`.
- Import root: `doctr`.
- Console entry point: `doctr-cli`.
- Python support from package metadata: Python `>=3.11,<4`.
- Core backend: PyTorch through `torch` and `torchvision`.

## Dependency groups

Base install:

```bash
pip install python-doctr
```

Optional extras:

| Extra | Use when |
|---|---|
| `viz` | Calling `Document.show()` / `Page.show()` or using interactive plotting; installs matplotlib-related dependencies. |
| `html` | Loading web pages or HTML through `DocumentFile.from_url`; installs WeasyPrint. |
| `contrib` | Using contrib utilities such as `ArtefactDetector`; installs ONNXRuntime. |
| `testing`, `quality`, `docs`, `dev` | Maintainer/development workflows only; do not install for ordinary OCR use unless explicitly needed. |

## Public module map

| Module | Main use | Owning sub-skill |
|---|---|---|
| `doctr.io` | `DocumentFile`, `Document`, `Page`, `KIEDocument`, reading/export helpers | [document-io-and-exports](../sub-skills/document-io-and-exports/SKILL.md) |
| `doctr.models` | OCR/KIE predictors, standalone detection/recognition/layout/table/classification factories, custom weights, Hub helpers | [core-ocr-and-kie](../sub-skills/core-ocr-and-kie/SKILL.md), [models-and-customization](../sub-skills/models-and-customization/SKILL.md) |
| `doctr.datasets` | Built-in/custom datasets, `VOCABS`, synthetic generators, data encoding/decoding | [datasets-training-and-evaluation](../sub-skills/datasets-training-and-evaluation/SKILL.md) |
| `doctr.transforms` | Image/sample transforms used by datasets and training loops | [datasets-training-and-evaluation](../sub-skills/datasets-training-and-evaluation/SKILL.md) |
| `doctr.utils.metrics` | Text, localization, object detection, OCR, and table metrics | [datasets-training-and-evaluation](../sub-skills/datasets-training-and-evaluation/SKILL.md) |
| `doctr.cli.main` | Installed OCR CLI parser and JSON output command | [cli-and-scripts](../sub-skills/cli-and-scripts/SKILL.md) |
| `doctr.contrib` | Optional artefact detection and contrib helpers | [deployment-and-contrib](../sub-skills/deployment-and-contrib/SKILL.md) |

## Core predictor defaults verified from source/API inspection

- `ocr_predictor(det_arch="fast_base", reco_arch="crnn_vgg16_bn", pretrained=False, ...)` returns an `OCRPredictor`.
- `kie_predictor(det_arch="fast_base", reco_arch="crnn_vgg16_bn", pretrained=False, ...)` returns a `KIEPredictor`.
- `detection_predictor(arch="fast_base", batch_size=2, assume_straight_pages=True, preserve_aspect_ratio=True, symmetric_pad=True)` wraps text detection models.
- `recognition_predictor(arch="crnn_vgg16_bn", batch_size=128, symmetric_pad=False)` wraps text recognition models.
- `layout_predictor(arch="lw_detr_s", batch_size=2)` and `table_predictor(arch="tablecenternet", batch_size=2)` cover layout/table workflows.
- `doctr-cli` differs from the Python factory default: it uses `det_arch="db_resnet50"`, `reco_arch="crnn_vgg16_bn"`, and `pretrained=True`.

## Architecture families

- Detection: DBNet, LinkNet, FAST families (`db_*`, `linknet_*`, `fast_*`).
- Recognition: CRNN, SAR, MASTER, ViTSTR, PARSeq, VIPTR.
- Layout: `lw_detr_s`, `lw_detr_m`.
- Table structure: `tablecenternet`.
- Orientation/classification: crop/page orientation predictors and classification factories.

See [models-and-customization](../sub-skills/models-and-customization/SKILL.md) for exact current architecture names and customization patterns.

## Verification scope used to build this skill

- Required environment scope: CPU package import, CLI help, API signature/object inspection, selected safe native/parser checks, and generated script help/static checks.
- Optional backend evidence: CUDA was visible in the construction environment and PyTorch reported CUDA availability, but CUDA is not required for this skill's selected verification scope.
- Not required: long training, dataset downloads, pretrained weight accuracy checks, Docker builds, service launches, Hub pushes, or GPU benchmarks.

## Source-script treatment

This skill bundles safe replacements for repeated operational tasks:

- Root `scripts/doctr_env_check.py`: package/CLI/backend diagnostics.
- CLI sub-skill helpers: quick OCR, batch OCR, and CLI environment diagnostics.
- IO sub-skill helper: synthetic/file export inspection.
- Core OCR sub-skill helper: API factory smoke.
- Dataset sub-skill helper: local label schema validator.

Heavy training, evaluation, latency, demo, API service, and Hub workflows are distilled into references rather than copied as runnable scripts because they can require long runtimes, network, credentials, services, GPUs, or large datasets.
