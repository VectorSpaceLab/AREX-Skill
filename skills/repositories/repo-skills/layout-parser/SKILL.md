---
name: layout-parser
description: "Routes LayoutParser workflows for document layout objects,
  document I/O, visualization, OCR, and layout-detection model wrappers."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# LayoutParser

LayoutParser is a document-image analysis toolkit for layout objects,
page/token loading, OCR parsing, visualization, and layout-detection model
wrappers.

Use this root skill as a router. Read the owning sub-skill for detailed API
notes, workflow steps, and troubleshooting.

## Install and first checks

Base install:

```bash
pip install layoutparser
```

OCR support:

```bash
pip install "layoutparser[ocr]"
```

Layout-model support:

```bash
pip install "layoutparser[layoutmodels]"
pip install "layoutparser[effdet]"
pip install "layoutparser[paddledetection]"
```

Detectron2 still uses its own backend install path:

```bash
pip install layoutparser torchvision
pip install "detectron2@git+https://github.com/facebookresearch/detectron2.git@v0.5#egg=detectron2"
```

For local inspection from a checkout, prefer an isolated environment and an
editable install in that private environment rather than mutating the source
repository.

Minimal import checks:

```bash
python -c "import layoutparser as lp; print(lp.__version__)"
python -c "from layoutparser import Layout, Rectangle; print(Layout([Rectangle(0, 0, 10, 10)]))"
```

If backend availability is uncertain, run the bundled inspector:

```bash
python scripts/inspect_backends.py
```

For a local smoke check that stays inside synthetic data, use:

```bash
python scripts/smoke_layoutparser_core.py
```

## Route map

### `layout-objects`
Read this for:

- `Interval`, `Rectangle`, `Quadrilateral`, `TextBlock`, and `Layout`
- coordinate transforms, padding, shifting, scaling, cropping
- `union`, `intersect`, `relative_to`, `condition_on`, `is_in`
- `Layout` sorting, filtering, serialization, and line/category grouping

### `layout-io`
Read this for:

- `load_json`, `load_dict`, `load_csv`, `load_dataframe`, `load_pdf`
- JSON/CSV/DataFrame round-trips and PDF token extraction
- page metadata, `block_type`, and layout export/import issues
- COCO-style annotation conversion patterns

### `visualization`
Read this for:

- `draw_box` and `draw_text`
- color maps, alpha handling, font settings, vertical text, and layout overlays
- turning detected or loaded layouts into readable page visuals

### `layout-models`
Read this for:

- `AutoLayoutModel`
- `Detectron2LayoutModel`, `EfficientDetLayoutModel`, and `PaddleDetectionLayoutModel`
- `lp://` config parsing, model catalogs, label maps, and backend selection
- model download, cache, and device-selection behavior

### `ocr`
Read this for:

- `TesseractAgent`, `TesseractFeatureType`
- `GCVAgent`, `GCVFeatureType`
- OCR response parsing, saved-response loading, and text aggregation
- credential and binary requirements for live OCR

## Root references

- Read `references/api-reference.md` for the top-level public API map.
- Read `references/workflows.md` for cross-sub-skill document workflows.
- Read `references/repo-provenance.md` before checking staleness or refreshing.
- Read `references/repo-routing-metadata.json` only when verifying managed
  repo-skills-router placement.

## When to jump to troubleshooting

Read `references/troubleshooting.md` when you see any of these:

- missing optional backend imports
- `pkg_resources` / setuptools issues around `google-cloud-vision==1`
- `tesseract` or credential problems
- `pdf2image` / `poppler` problems
- `InvalidShapeError`, `NotSupportedShapeError`, or layout validation errors
- model download, cache, or `lp://` parsing failures

## Notes for future agents

- This skill is public runtime guidance; do not rely on the original checkout
  remaining available.
- Runtime links should stay inside this generated skill tree.
- Use the sub-skill that matches the user’s primary workflow first, then cross-
  reference the others when a task spans multiple layers.
