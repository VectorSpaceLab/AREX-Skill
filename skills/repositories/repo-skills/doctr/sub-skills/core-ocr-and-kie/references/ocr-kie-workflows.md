# OCR and KIE workflow reference

This reference covers docTR's end-to-end Python inference surfaces. It assumes the package is importable in the active Python environment and focuses on runtime decisions, not on raw document loading/export, model catalogs, CLI wrappers, or training.

## Core mental model

- OCR is a two-stage pipeline: text detection localizes word boxes, then recognition transcribes the word crops.
- `ocr_predictor(...)` builds an `OCRPredictor` and returns a `Document` when called.
- `kie_predictor(...)` builds a `KIEPredictor` and returns a `KIEDocument` when called. KIE keeps predictions grouped by detection class instead of organizing all text into blocks/lines.
- Both predictors accept either a `DocumentFile` result or a plain list of RGB `np.ndarray` pages. Each page must be a 3-D image array shaped `(height, width, channels)`; do not pass a 4-D batch tensor.
- The current factory defaults are `det_arch="fast_base"`, `reco_arch="crnn_vgg16_bn"`, `pretrained=False`, `assume_straight_pages=True`, `preserve_aspect_ratio=True`, and `symmetric_pad=True`. Older snippets may explicitly use `db_resnet50`; pass `det_arch` yourself when the exact architecture matters.

## Minimal OCR workflow

```python
from doctr.io import DocumentFile
from doctr.models import ocr_predictor

pages = DocumentFile.from_images(["page1.png", "page2.png"])
predictor = ocr_predictor(
    det_arch="fast_base",
    reco_arch="crnn_vgg16_bn",
    pretrained=True,
)
result = predictor(pages)

assert len(result.pages) == len(pages)
print(result.render())
structured = result.export()
```

Use this path when the desired output is the full document text hierarchy: `Document -> Page -> Block -> Line -> Word`, with optional `page.layout` and `page.tables`.

### Basic output checks

After OCR, verify:

- `len(result.pages)` equals the number of input pages.
- Every page has `page_idx`, `dimensions`, `orientation`, `language`, `blocks`, `layout`, and `tables` fields in `page.export()`.
- Word geometries are relative to the page size. Straight boxes have two points `((xmin, ymin), (xmax, ymax))`; rotated boxes are four-point polygons.
- `Word.value`, `Word.confidence`, `Word.objectness_score`, and `Word.crop_orientation` are present before sending results to downstream business logic.
- If `detect_tables=True`, table words are moved into `page.tables`; they are intentionally removed from regular `page.blocks` to avoid duplicate text.

For detailed export formats (`render`, JSON, hOCR/XML, Markdown, HTML, table grids), route to `../document-io-and-exports/SKILL.md`.

## Minimal KIE workflow

```python
from doctr.io import DocumentFile
from doctr.models import kie_predictor

pages = DocumentFile.from_pdf("form.pdf")
predictor = kie_predictor(
    det_arch="fast_base",
    reco_arch="crnn_vgg16_bn",
    pretrained=True,
)
result = predictor(pages)

page0 = result.pages[0]
for class_name, predictions in page0.predictions.items():
    for pred in predictions:
        print(class_name, pred.value, pred.confidence, pred.geometry)
```

Use KIE when the detection model may emit multiple semantic classes and you need predictions grouped by class. A standard text detector commonly produces one text class, but a custom or fine-tuned detector can expose class keys such as dates, totals, addresses, or other field types.

### KIE output checks

After KIE, verify:

- The object is a `KIEDocument` and contains one `KIEPage` per input page.
- `page.predictions` is a dictionary: `{class_name: list[Prediction]}`.
- Each `Prediction` has `value`, `confidence`, `geometry`, `objectness_score`, and `crop_orientation`.
- `page.layout` is available only when `detect_layout=True` and is otherwise an empty list.
- `detect_tables` is an OCR factory flag, not a KIE factory flag. Use OCR with `detect_tables=True` for structured table extraction.

## Pretrained and download caveats

- `pretrained=True` loads trained detector/recognizer weights and is required for useful out-of-the-box OCR/KIE.
- `pretrained=False` builds randomly initialized models. Use it only to validate imports, signatures, device movement, and result shapes.
- `pretrained_backbone=True` can still request backbone weights even when the task head is not pretrained. For offline smoke tests, set both `pretrained=False` and `pretrained_backbone=False`.
- Non-straight-page handling can instantiate pretrained orientation helpers. To avoid orientation-helper model loading in smoke tests, keep `assume_straight_pages=True` or explicitly pass `disable_page_orientation=True` / `disable_crop_orientation=True` when using non-straight or straightening modes.
- If a machine has no internet access, prepare the model cache ahead of time or run only no-pretrained, no-pretrained-backbone smoke checks.

## Page rotation and geometry choices

Choose the rotation strategy before interpreting geometries:

| Situation | Recommended predictor flags | Output behavior |
| --- | --- | --- |
| Straight pages with horizontal text | `assume_straight_pages=True` | Fastest path; detector fits and returns straight boxes. |
| Rotated/skewed words or mixed orientations | `assume_straight_pages=False` | Detector can return rotated polygons; crop orientation classification may rectify crops before recognition. |
| Need straight boxes even when the detector emits polygons | `assume_straight_pages=False, export_as_straight_boxes=True` | Final export fits polygons into axis-aligned boxes. |
| Page-uniform skew/rotation should be corrected before detection | `assume_straight_pages=False, straighten_pages=True` | Predictor estimates orientation, rotates/straightens pages, runs detection again, then builds the result. |
| Need output boxes in the original image coordinate space after straightening | `straighten_pages=True, preserve_original_coords=True` | Word/KIE/layout/table geometries are remapped to the original page; useful for annotation/redaction. |
| Only small rotations and latency is critical | Consider `disable_page_orientation=True` or `disable_crop_orientation=True` only after verifying quality | Disables helper classifiers in affected modes; may reduce robustness on rotated inputs. |

Do not assume a geometry has the same dimensionality across configurations. Validate geometry shape before drawing boxes, computing IoU, or passing locations to an external system.

## Orientation and language flags

```python
predictor = ocr_predictor(
    pretrained=True,
    detect_orientation=True,
    detect_language=True,
)
result = predictor(pages)
print(result.pages[0].orientation)  # {"value": angle_or_None, "confidence": ...}
print(result.pages[0].language)     # {"value": lang_or_None, "confidence": ...}
```

- `detect_orientation=True` adds page orientation metadata. It can increase latency because it consumes detection maps and page-orientation logic.
- `straighten_pages=True` also needs orientation estimation, even when `detect_orientation=False`.
- `detect_language=True` infers language from the recognized text and attaches it to each page. It is not a language-specific OCR model selector.
- Empty or low-quality recognition can produce empty/uncertain language results; never treat language metadata as proof that OCR succeeded.

## Layout and ignored regions

```python
predictor = ocr_predictor(
    pretrained=True,
    detect_layout=True,
    layout_arch="lw_detr_s",
    ignore_regions=["Picture", "Formula"],
)
result = predictor(pages)
for region in result.pages[0].layout:
    print(region.type, region.confidence, region.geometry)
```

- `detect_layout=True` runs a layout detector and attaches `LayoutElement` objects to `page.layout`.
- `layout_arch` can be an architecture name such as `"lw_detr_s"` / `"lw_detr_m"` or a compatible layout model instance. Use `../models-and-customization/SKILL.md` for custom model construction.
- `ignore_regions` masks detected layout regions whose class names match the list before OCR/KIE detection and recognition. It is useful for excluding pictures, formulas, or other layout classes.
- In the factory path, `ignore_regions` does not by itself create a layout predictor. Pair it with `detect_layout=True` for OCR/KIE, or with `detect_tables=True` for OCR, so there are layout regions to mask.
- If no layout predictor is present, ignored regions are effectively a no-op.

## Table-aware OCR

```python
predictor = ocr_predictor(pretrained=True, detect_tables=True)
result = predictor(pages)

for table in result.pages[0].tables:
    grid = table.to_grid()
    print(table.num_rows, table.num_cols, grid)
```

- `detect_tables=True` is available on `ocr_predictor`.
- It automatically enables a layout predictor because table regions are found by layout detection.
- Each detected `Table` region is cropped, passed to the table-structure predictor, remapped to page coordinates, and attached as `page.tables`.
- Words whose centers fall inside recognized table cells are regrouped into structured `TableCell` objects and removed from `page.blocks` to prevent duplicate text.
- If a user reports that table text "disappeared" from normal text output, first check `page.tables` and `page.export()["tables"]` before changing detector thresholds.

Route detailed table export/grid handling to `../document-io-and-exports/SKILL.md`; route standalone table predictor or table model customization to `../models-and-customization/SKILL.md`.

## Batch sizes and devices

```python
from doctr.models import ocr_predictor

predictor = ocr_predictor(
    pretrained=True,
    det_bs=4,      # detection and layout batch size
    reco_bs=256,   # recognition crop batch size
)

# PyTorch device movement
import torch
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
predictor = predictor.to(device)
result = predictor(pages)
```

- `det_bs` controls detector batching and is also used for the layout model when layout/table detection is enabled. Default is `2`.
- `reco_bs` controls recognition crop batching. Default is `128`.
- Increase `reco_bs` only when memory headroom is available; recognition receives one crop per detected word, so dense pages can create large batches.
- Predictors are PyTorch modules and can be moved with `.to(device)` or `.cuda()`. Inputs remain NumPy page arrays; the predictor handles tensor conversion internally.
- If using Apple Silicon, choose an MPS device only after `torch.backends.mps.is_available()` is true.
- For half precision or compiled/custom model optimizations, route to `../models-and-customization/SKILL.md`.

## Builder and output-shape options

The predictor factory forwards additional keyword arguments to the document builder:

```python
predictor = ocr_predictor(
    pretrained=True,
    resolve_lines=True,
    resolve_blocks=False,
    paragraph_break=0.035,
    keep_reading_order=True,
)
```

- `resolve_lines=True` groups words into lines.
- `resolve_blocks=True` further clusters lines into blocks; default is false.
- `paragraph_break` controls the minimum relative horizontal spacing used to split sub-lines/paragraphs.
- `keep_reading_order=True` reorders blocks in reading order and uses layout regions when available.
- `export_as_straight_boxes=True` is a builder option exposed by the factory; it changes final geometry shape for rotated detections.

When a downstream system depends on a stable schema, document these builder flags next to the OCR output contract.

## Hooks for advanced location filtering

Both OCR and KIE predictors support `add_hook(callable)` before recognition. Hooks receive localization predictions and must return the same structural shape:

```python
class ClampHook:
    def __call__(self, loc_preds):
        # Keep the same nested structure and coordinate convention.
        return loc_preds

predictor = ocr_predictor(pretrained=True)
predictor.add_hook(ClampHook())
```

Use hooks only for bounded geometric post-processing. Do not mutate predictions into absolute pixel coordinates, remove required class keys from KIE dictionaries, or return coordinates outside `[0, 1]`.

## Decision checklist

Before running a production OCR/KIE job, answer:

1. Are inputs valid RGB page arrays or loaded through `DocumentFile`? If not, route to document IO.
2. Is network/cache access available for pretrained weights? If not, use cached models or set no-pretrained flags for smoke checks only.
3. Are pages guaranteed straight? If no, choose between polygon output, straightened pages, or straight-box export.
4. Is layout needed only for metadata, region masking, or table extraction? Enable `detect_layout`, `ignore_regions`, or `detect_tables` accordingly.
5. Is the expected output OCR text hierarchy or class-grouped KIE predictions?
6. Are batch sizes and device choices consistent with available memory?
7. Do downstream consumers expect table text in `blocks`, or can they read `page.tables`?
8. Have page count, result type, optional layout/table fields, and geometry ranges been checked?
