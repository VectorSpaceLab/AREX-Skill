# IO and export troubleshooting

Use this guide when docTR inputs load incorrectly, result objects look different than expected, or export output surprises the user.

## Loading PDFs, images, URLs, and arrays

### `DocumentFile.from_pdf` returns pages, not text

Symptom: the user expects `from_pdf` to perform OCR.

Resolution:

1. Explain that `DocumentFile.from_pdf(...)` rasterizes each PDF page into an image array.
2. Route predictor construction/inference to `../core-ocr-and-kie/SKILL.md`.
3. After inference, use this sub-skill to inspect `Document`/`KIEDocument` outputs and exports.

### Invalid image or file-not-found errors

Common causes:

- The path does not exist or points to a directory.
- The bytes are not an image supported by the image backend.
- A PDF was accidentally passed to `from_images` / `read_img_as_numpy`.
- The task passed a Python object type other than a path, bytes, or sequence of those.

Suggested checks:

```python
from pathlib import Path
from doctr.io import DocumentFile

path = Path("page.png")
assert path.is_file(), f"Missing input file: {path}"
pages = DocumentFile.from_images(path)
print(pages[0].shape, pages[0].dtype)
```

### Grayscale, alpha, BGR, CHW, or float arrays

DocTR's normal page contract is `np.uint8` arrays shaped `(H, W, 3)` in RGB order.

Fix before sending arrays to a predictor:

```python
import numpy as np

page = np.asarray(page)
if page.ndim == 2:                       # grayscale H x W
    page = np.repeat(page[..., None], 3, axis=2)
elif page.ndim == 3 and page.shape[-1] == 4:  # RGBA
    page = page[..., :3]
if page.ndim == 3 and page.shape[0] == 3 and page.shape[-1] != 3:
    page = np.moveaxis(page, 0, -1)       # CHW -> HWC
if page.dtype != np.uint8:
    page = np.clip(page, 0, 255).astype(np.uint8)
```

If the array came from OpenCV in BGR order, convert to RGB before prediction.

### URL loading fails

Likely causes:

- The `html` extra is not installed, so WeasyPrint is missing.
- The environment lacks native libraries required by the HTML renderer.
- Network access, TLS, redirects, or site-level bot protections block the URL.

Resolution:

- Install docTR with the `html` extra for URL support.
- If native-renderer issues persist, save the page as a PDF or image outside docTR and use `from_pdf` or `from_images`.
- Avoid URL loading in offline/reproducibility-critical runs; store a fixed input artifact instead.

### PDF output is huge or slow

`from_pdf` rasterizes pages. Higher `scale` increases pixel dimensions, memory use, and downstream predictor cost.

Actions:

- Use a lower `scale` when high-resolution OCR is unnecessary.
- Process long documents in chunks if later predictor inference exceeds memory.
- Confirm that every returned page has reasonable dimensions before inference.

## Result-object interpretation

### `export()` lacks the original page image

`export()` is meant for JSON-like structure and omits the raw page image. If rebuilding objects from JSON and then visualizing/synthesizing, pass page images back explicitly:

```python
restored = Document.from_dict(exported, pages=original_pages)
```

Without images, restored pages use a placeholder image and are still useful for text/dict exports.

### OCR output has tables outside `blocks`

When table recognition is enabled upstream, table text is represented under `page.tables` and removed from `page.blocks` to avoid duplicate text.

Use:

```python
for table in page.tables:
    print(table.to_grid())
    print(table.render())
```

Exports include tables in reading order; raw block iteration alone does not.

### KIE output has no `blocks`

KIE pages group recognized values by semantic class:

```python
for class_name, predictions in kie_page.predictions.items():
    for pred in predictions:
        print(class_name, pred.value)
```

Use `KIEPage`/`KIEDocument` exports, not OCR block/line/word traversal, for KIE tasks.

### Page order and page indices disagree

`DocumentFile.from_pdf` and `DocumentFile.from_images([...])` preserve input page order. `page.page_idx` is the original page index. If pages were manually reordered before prediction, the list position can differ from `page_idx`; rely on the field appropriate to the task.

## Export behavior

### Text or Markdown appears reordered

By default, docTR exports are reading-order-aware. They may reorder stored blocks/lines to handle multi-column, RTL, vertical, or layout-aware pages.

Actions:

- Use `page.items_in_reading_order()` to inspect the effective order.
- Use `export(reading_order=False)` to preserve stored block order in JSON/dict output.
- Use `export_as_xml(reading_order=False)` when hOCR must preserve stored block/table order.
- Pass `direction="ltr"`, `"rtl"`, `"ttb-ltr"`, or `"ttb-rtl"` when automatic direction inference is wrong.

### Headers, footers, or footnotes should be removed

For text, Markdown, AsciiDoc, and HTML exports, use:

```python
clean_text = page.render(include_furniture=False)
clean_md = document.export_as_markdown(include_furniture=False)
```

This depends on layout regions being present and correctly labeled upstream. If no layout regions are attached, furniture cannot be identified reliably by the exporters.

### Unsupported export format

`export_as(...)` accepts these canonical formats and aliases:

- `markdown`, `md`
- `asciidoc`, `adoc`
- `html`
- `text`, `txt`
- `json`, `dict`
- `xml`, `hocr`

Anything else raises `ValueError`. Map user requests such as CSV, DOCX, or YAML to an explicit conversion step from JSON/text/table grids rather than passing those names to `export_as`.

### JSON serialization fails after custom mutation

Native docTR `export()` normalizes NumPy scalars/arrays. If serialization fails, custom code likely inserted a non-serializable object into an element field.

Actions:

- Re-run `json.dumps(result.export())` before custom mutation to isolate the issue.
- Convert custom values to strings, numbers, lists, tuples, or dictionaries.
- Avoid attaching tensors, images, file handles, or model objects to result elements.

### hOCR/XML export raises `TypeError`

XML/hOCR export currently supports straight two-corner bounding boxes only. It can raise `TypeError` for rotated/polygon block, table, or KIE prediction geometries.

Options:

- Re-run upstream inference with straight-box export options when hOCR is required.
- Use JSON, text, Markdown, AsciiDoc, or HTML exports when rotated geometries must be preserved.
- Use `reading_order=False` only to change ordering; it does not make rotated boxes valid for hOCR.

### HTML output is a fragment

`export_as_html()` emits semantic fragments such as `<p>`, `<h1>`, `<ul>`, `<table>`, and document-level `<hr>` separators. It does not include a doctype, `<html>`, `<head>`, or charset metadata. Wrap it yourself if a complete HTML document is required.

### Escaping changes text

Markdown and AsciiDoc exporters escape structural characters by default so raw OCR text does not accidentally become markup. HTML text is escaped by default. If preserving raw markup characters matters, use format-specific escape controls only for trusted output and document why the output is safe.

## Visualization

### `show()` fails with missing visualization packages

`show()` requires the `viz` extra (`matplotlib` and `mplcursors`). Without it, use text/JSON exports or install the extra before visualization.

### `show()` displays stretched overlays

If the upstream predictor preserved aspect ratio or padded/resized pages, pass `preserve_aspect_ratio=True` consistently to visualization calls when appropriate.

```python
result.pages[0].show(preserve_aspect_ratio=True)
```

Use `display_layout=False`, `display_artefacts=False`, or `words_only=True` when overlays are too dense.

## Bundled inspection script

Run the helper without inputs to inspect synthetic OCR/KIE exports:

```bash
python scripts/inspect_document_export.py --demo-format all
```

Run it with inputs to validate page arrays without predictor inference:

```bash
python scripts/inspect_document_export.py --input page.png --kind image
python scripts/inspect_document_export.py --input document.pdf --kind pdf
```

If the script validates loading but a later OCR task fails, route to the core OCR/KIE sub-skill for predictor-specific diagnosis.
