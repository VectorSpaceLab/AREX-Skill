---
name: core-ocr-and-kie
description: "Run docTR end-to-end OCR and KIE inference with predictor APIs,
  rotation/layout/table options, batching, devices, and output checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# core-ocr-and-kie

Use this sub-skill when the task is to run or debug docTR's Python end-to-end inference pipelines:

- `doctr.io.DocumentFile` or a list of RGB NumPy pages -> `doctr.models.ocr_predictor(...)` -> `Document`.
- `doctr.io.DocumentFile` or a list of RGB NumPy pages -> `doctr.models.kie_predictor(...)` -> `KIEDocument`.
- Predictor-level flags for rotated/skewed pages, orientation/language detection, layout detection, table detection, ignored layout regions, batching, and device movement.
- Sanity-checking output object shapes, page counts, geometry conventions, and the no-download/random-weight caveat.

Do **not** use this sub-skill for raw file loading/export format details, model zoo catalogs/custom weights/ONNX export, CLI wrappers, training, datasets, or evaluation scripts. Route those tasks to sibling sub-skills:

- Document loading and result export/render details: [document-io-and-exports](../document-io-and-exports/SKILL.md)
- Architecture catalogs, custom models, optimization, export, vocab whitelisting: [models-and-customization](../models-and-customization/SKILL.md)
- `doctr-cli` and bundled command-line helpers: [cli-and-scripts](../cli-and-scripts/SKILL.md)
- Datasets, training, metrics, and evaluation: [datasets-training-and-evaluation](../datasets-training-and-evaluation/SKILL.md)

## Read first

1. For API recipes and option interactions, read [references/ocr-kie-workflows.md](references/ocr-kie-workflows.md).
2. For failure diagnosis, read [references/troubleshooting.md](references/troubleshooting.md).
3. For a safe import/factory/optional-forward smoke check, run or adapt [scripts/ocr_api_smoke.py](scripts/ocr_api_smoke.py).

## Operating rules

- Prefer explicit `det_arch`, `reco_arch`, `pretrained`, `pretrained_backbone`, `assume_straight_pages`, and batch-size choices when reproducibility matters.
- Treat `pretrained=False` as an API/shape smoke mode only; randomly initialized detection and recognition models do not produce useful OCR.
- Be explicit about network/cache behavior: pretrained model weights and some orientation helpers may download on first use unless already cached or disabled.
- Validate outputs before downstream use: `Document.pages` for OCR, `KIEDocument.pages[*].predictions` for KIE, optional `page.layout`, optional `page.tables`, and relative geometries.
