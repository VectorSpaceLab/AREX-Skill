# docTR IO and export reference

This reference covers docTR's public IO and result-object APIs. It assumes a predictor has already produced a `Document` or `KIEDocument`; for predictor construction, route to the core OCR/KIE sub-skill.

## Input loading APIs

Import surface:

```python
from doctr.io import DocumentFile, read_pdf, read_img_as_numpy, read_img_as_tensor, decode_img_as_tensor, read_html
```

### `DocumentFile.from_pdf(file, **kwargs)`

- Accepts a PDF path, `Path`, bytes, or a binary stream supported by the PDF backend.
- Returns one NumPy array per page, in PDF page order.
- Default rendering uses `scale=2`, `rgb_mode=True`; extra keyword arguments are forwarded to the PDF page renderer.
- Use `password=...` for encrypted PDFs.
- Return pages are image arrays, not PDF objects. `result.pages[i]` corresponds to the `i`-th rasterized page once passed through a predictor.

```python
pages = DocumentFile.from_pdf("invoice.pdf", scale=2)
assert isinstance(pages, list)
assert pages[0].dtype == "uint8" or pages[0].dtype.name == "uint8"
```

### `DocumentFile.from_images(files, **kwargs)`

- Accepts one image path/`Path`/bytes object or a sequence of paths/bytes.
- A single path is wrapped as a one-page list.
- Returns one NumPy array per input image, preserving the input sequence order.
- Keyword arguments are forwarded to `read_img_as_numpy`, notably:
  - `output_size=(height, width)` to resize decoded images.
  - `rgb_output=True` by default; pass `False` only when you intentionally need BGR arrays.

```python
one_page = DocumentFile.from_images("page.png")
many_pages = DocumentFile.from_images(["page-1.png", "page-2.png"])
```

### `DocumentFile.from_url(url, **kwargs)` and `read_html(url, **kwargs)`

- `from_url` renders a web page to a PDF byte stream, then calls `from_pdf`.
- It requires the `html` extra (`weasyprint`). Without it, the call fails before loading the page.
- `read_html` returns PDF bytes from the URL-rendered page; it does not return HTML text.
- Use URL loading only when the execution environment allows outbound network access and has the native libraries required by the HTML renderer.

```python
pages = DocumentFile.from_url("https://example.com")
```

### Already-decoded arrays

Predictors accept a list of page arrays, so custom array loaders can bypass `DocumentFile` if they honor docTR's page contract:

- Shape: `(height, width, 3)` (HWC, not CHW).
- Dtype: `np.uint8` for image-like pages.
- Channel order: RGB for normal docTR predictor input.
- Grayscale, alpha, float, tensor, or BGR data should be converted before prediction.

```python
import numpy as np

page = np.asarray(page, dtype=np.uint8)
if page.ndim == 2:
    page = np.repeat(page[..., None], 3, axis=2)
if page.shape[-1] == 4:
    page = page[..., :3]
pages = [page]
```

### Lower-level image readers

- `read_img_as_numpy(path_or_bytes, output_size=None, rgb_output=True)` returns an HWC NumPy array in `uint8`.
- `read_img_as_tensor(path, dtype=torch.float32)` and `decode_img_as_tensor(bytes, dtype=torch.float32)` return PyTorch tensors in CHW layout; float dtypes are scaled by 255. These are useful for lower-level model utilities, not as the normal `DocumentFile` output.

## Result-object model

Common OCR result hierarchy:

```text
Document
└── pages: list[Page]
    ├── page: original page image array
    ├── page_idx: input page index
    ├── dimensions: (height, width)
    ├── orientation: {"value": angle_or_none, "confidence": score_or_none}
    ├── language: {"value": language_or_none, "confidence": score_or_none}
    ├── layout: list[LayoutElement]
    ├── tables: list[Table]
    └── blocks: list[Block]
        └── lines: list[Line]
            └── words: list[Word]
```

KIE result hierarchy:

```text
KIEDocument
└── pages: list[KIEPage]
    ├── predictions: dict[str, list[Prediction]]
    ├── layout: list[LayoutElement]
    ├── page/page_idx/dimensions/orientation/language
    └── export/render/show methods analogous to Page
```

Element fields to rely on:

| Object | Important fields | Rendering/export notes |
| --- | --- | --- |
| `Word` | `value`, `confidence`, `geometry`, `objectness_score`, `crop_orientation` | `render()` returns `value`. |
| `Prediction` | Same as `Word` | Used in KIE class buckets. |
| `Line` | `words`, `geometry`, `objectness_score` | `render()` joins word values with spaces. |
| `Block` | `lines`, `artefacts`, `geometry`, `objectness_score` | `render()` joins lines with newlines. |
| `Artefact` | `type`, `confidence`, `geometry` | Renders as a bracketed tag such as `<[QR_CODE]>`. |
| `LayoutElement` | `type`, `confidence`, `geometry` | Layout labels can drive headings, list items, furniture filtering, and table placement in exporters. |
| `TableCell` | `value`, `confidence`, `geometry`, row/column start/end indices | `row_span` and `col_span` are derived from the inclusive indices. |
| `Table` | `cells`, `num_rows`, `num_cols`, `geometry`, `confidence` | `to_grid()` returns a dense string grid; `render()` emits tab-separated rows. |
| `Page` | `blocks`, `layout`, `tables`, metadata, image | OCR page export surface. |
| `KIEPage` | `predictions`, `layout`, metadata, image | KIE export surface grouped by semantic class. |
| `Document` / `KIEDocument` | `pages` | Document-level methods dispatch per page and join page outputs. |

The page image is not included in `export()`. If you rebuild objects from dictionaries with `Page.from_dict`, `KIEPage.from_dict`, `Document.from_dict`, or `KIEDocument.from_dict`, pass the original page image(s) explicitly when downstream visualization or synthesis needs them; otherwise a placeholder image is used.

## Export API matrix

All four primary result scopes (`Page`, `KIEPage`, `Document`, `KIEDocument`) support the dispatcher:

```python
result.export_as("markdown")  # alias: "md"
result.export_as("asciidoc")  # alias: "adoc"
result.export_as("html")
result.export_as("text")      # alias: "txt"; same as render()
result.export_as("json")      # alias: "dict"; same as export()
result.export_as("xml")       # alias: "hocr"; same as export_as_xml()
```

Unsupported formats raise `ValueError` with the supported-format list.

### Plain text: `render(...)`

- `Page.render(block_break="\n\n", direction="auto", include_furniture=True)` returns reading-order text for a page.
- `KIEPage.render(prediction_break="\n\n", direction="auto")` returns one `class: value` line per prediction.
- `Document.render(page_break="\n\n\n\n", **page_kwargs)` joins each page render.
- `KIEDocument.render(...)` inherits document behavior and forwards arguments to each KIE page.

### JSON/dict: `export(reading_order=True)`

- Returns nested Python containers that are JSON-serializable.
- NumPy scalars and arrays in geometry/confidence metadata are converted to built-in Python types/tuples.
- With `reading_order=True`, page blocks or KIE predictions are linearized; with `False`, stored order is preserved.
- Tables remain under the page-level `tables` key and table cells under each table's `cells` key.

```python
import json
payload = document.export()
json_text = json.dumps(payload, ensure_ascii=False, indent=2)
```

### XML/hOCR: `export_as_xml(...)`

- `Page.export_as_xml(...)` and `KIEPage.export_as_xml(...)` return `(xml_bytes, element_tree)`.
- `Document.export_as_xml(...)` and `KIEDocument.export_as_xml(...)` return a list of `(xml_bytes, element_tree)`, one tuple per page.
- Keyword arguments include `file_title`, `direction`, and `reading_order`.
- The hOCR root language uses the page language when available, otherwise falls back to `en`.
- hOCR uses absolute pixel `bbox` values derived from each page's `(height, width)` dimensions.
- XML export currently requires straight two-corner bounding boxes. Rotated/polygon geometries for blocks, tables, or KIE predictions raise `TypeError`.

### Markdown

- `export_as_markdown(direction="auto", escape=True, include_furniture=True)` emits reading-order Markdown.
- `Document.export_as_markdown(page_break="\n\n---\n\n", **kwargs)` uses a thematic break by default.
- Layout labels can render titles as `#`, section headers as `##`, list regions as bullets, and tables as GitHub-flavored Markdown tables.
- Markdown structural characters and dangerous line markers are escaped by default. Use `escape=False` only when preserving raw OCR syntax is more important than valid Markdown structure.

### AsciiDoc

- `export_as_asciidoc(direction="auto", escape=True, include_furniture=True)` emits reading-order AsciiDoc.
- `Document.export_as_asciidoc(page_break="\n\n<<<\n\n", **kwargs)` uses an AsciiDoc page break by default.
- Layout titles/section headers become `==` / `===`; list items use `*`; tables use AsciiDoc table syntax.

### HTML

- `export_as_html(direction="auto", include_furniture=True)` emits an HTML fragment, not a full HTML document.
- `Document.export_as_html(page_break="<hr>", **kwargs)` joins page fragments with an `<hr>` by default.
- Layout labels can render headings, lists, paragraphs, and tables.
- Recognized text is HTML-escaped by default in the exporter. Only use direct exporter escape overrides for trusted output that will never be rendered in a browser.

## Reading-order behavior

Reading-order-aware paths include `render()`, `export()`, `export_as_xml()`, Markdown, AsciiDoc, HTML, and `export_as(...)` by default.

Key points:

- `direction="auto"` infers left-to-right, right-to-left, or vertical direction using recognized text and page language.
- Explicit directions include `"ltr"`, `"rtl"`, `"ttb-rtl"`, and `"ttb-ltr"`.
- Multi-column pages are sorted by reading segments rather than raw storage order.
- Layout regions can group wrapped list items into one bullet and identify headers, footers, and footnotes.
- `include_furniture=False` drops layout-labeled page headers, page footers, and footnotes from text, Markdown, AsciiDoc, and HTML exports.
- A page-level reading-order result is memoized; exporting one page to several formats does not recompute the order every time unless the page content changes.
- `items_in_reading_order(direction="auto")` returns the ordered `Block` and `Table` objects for a page when code needs to inspect ordering before choosing an export format.

## Table outputs

When table recognition is enabled upstream, table text is represented as `Table` objects and removed from regular page blocks to avoid duplicate text.

```python
page = document.pages[0]
for table in page.tables:
    grid = table.to_grid()
    # grid is loadable into pandas: pd.DataFrame(grid)
    print(table.render())
```

Table details:

- `Table.to_grid()` returns a dense `num_rows x num_cols` list of string rows.
- Spanning cells place the value at the top-left cell of the span; other spanned positions are empty strings.
- Markdown, AsciiDoc, HTML, plain text, and hOCR exporters include recognized tables in reading order.
- Empty table grids contribute an empty string and are skipped by page-level text/Markdown/HTML exports.

## KIE outputs

KIE pages group predictions by semantic detection class instead of spatial `blocks -> lines -> words`.

```python
kie_doc = kie_model(pages)
for page in kie_doc.pages:
    for class_name, predictions in page.predictions.items():
        for pred in predictions:
            print(class_name, pred.value, pred.confidence, pred.geometry)
```

Export behavior:

- `KIEPage.export()` returns `{"predictions": {class_name: [prediction_dict, ...]}, ...}`.
- KIE predictions are sorted in reading order per class by default.
- Empty classes are skipped by text/Markdown/AsciiDoc/HTML exporters.
- `KIEPage.render()` emits `class: value` sections; Markdown/AsciiDoc/HTML exporters emit one section per class.
- `KIEDocument` uses the same document-level dispatcher as `Document`, but its pages are `KIEPage` objects.

## Visualization and reconstruction

- `Page.show(...)`, `KIEPage.show(...)`, `Document.show(...)`, and `KIEDocument.show(...)` overlay predictions on page images and require the `viz` extra (`matplotlib` and `mplcursors`).
- Useful `show()` keyword arguments include `interactive`, `preserve_aspect_ratio`, `words_only`, `display_artefacts`, and `display_layout`.
- `synthesize()` rebuilds page images from exported predictions; it relies on the stored page image and geometry metadata.

## Safe inspection helper

Use the bundled script for quick checks:

```bash
python scripts/inspect_document_export.py --demo-format all
python scripts/inspect_document_export.py --input page.png --kind image --demo-format markdown
python scripts/inspect_document_export.py --input document.pdf --kind pdf --write-dir out_exports
```

The helper can validate input page shapes and demonstrate export surfaces with synthetic OCR/KIE objects. It intentionally does not run `ocr_predictor` or `kie_predictor`.
