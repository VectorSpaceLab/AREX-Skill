# LayoutParser API Reference Overview

This file is the root map for LayoutParser's public surface. Read the owning
sub-skill reference for real signatures, edge cases, and examples.

## Top-level exports

| Symbol | Owner | Notes |
| --- | --- | --- |
| `Interval`, `Rectangle`, `Quadrilateral`, `TextBlock`, `Layout` | `layout-objects` | Coordinate primitives, layout containers, conversions, and shape operations. |
| `load_json`, `load_dict`, `load_csv`, `load_dataframe`, `load_pdf` | `layout-io` | Layout serialization and document/PDF loading. |
| `draw_box`, `draw_text` | `visualization` | Box/text rendering on PIL or NumPy images. |
| `AutoLayoutModel` | `layout-models` | Chooses an available layout-detection backend from an `lp://` config. |
| `Detectron2LayoutModel` | `layout-models` | Only available when Detectron2 is installed. |
| `EfficientDetLayoutModel` | `layout-models` | Requires `torch`, `torchvision`, and `effdet`. |
| `PaddleDetectionLayoutModel` | `layout-models` | Only available when PaddleDetection is installed. |
| `TesseractAgent`, `TesseractFeatureType` | `ocr` | Tesseract OCR wrapper and aggregation levels. |
| `GCVAgent`, `GCVFeatureType` | `ocr` | Google Cloud Vision OCR wrapper and aggregation levels. |
| `generalized_connected_component_analysis_1d`, `simple_line_detection`, `group_textblocks_based_on_category` | `layout-objects` | Layout-analysis helpers built on `Layout`/`TextBlock`. |
| `is_*_available`, `requires_backends` | root troubleshooting + `layout-models`/`ocr` | Backend probes live in `layoutparser.file_utils`; use them when diagnosing optional imports. |

## Quick reminders

- `layoutparser` uses lazy imports. Optional backend classes appear only when
  their dependency is installed.
- `lp://` model paths are parsed in `layout-models`; the exact backend and
  dataset are decided there.
- `TextBlock` wraps a shape-specific block, so most geometry methods are
  delegated to the underlying `Interval`, `Rectangle`, or `Quadrilateral`.
- Layout serialization is shape-aware: `Layout.to_dict()` and
  `load_dict()` preserve page data and nested block types.

## Read next

- `../sub-skills/layout-objects/references/guide.md`
- `../sub-skills/layout-io/references/guide.md`
- `../sub-skills/visualization/references/guide.md`
- `../sub-skills/layout-models/references/guide.md`
- `../sub-skills/ocr/references/guide.md`
- `troubleshooting.md`
