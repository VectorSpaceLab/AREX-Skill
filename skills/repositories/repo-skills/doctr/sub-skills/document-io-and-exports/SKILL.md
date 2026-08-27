---
name: document-io-and-exports
description: "Load docTR inputs and interpret or export Document, Page, KIE,
  table, and reading-order outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# document-io-and-exports

Use this sub-skill when a task is about docTR document inputs, page arrays, result-object structure, or output conversion after OCR/KIE inference.

## Route here for

- Loading PDFs, image files, image bytes, URL-rendered web pages, or already-decoded NumPy page arrays.
- Explaining `DocumentFile.from_pdf`, `DocumentFile.from_images`, `DocumentFile.from_url`, `read_pdf`, `read_img_as_numpy`, `read_img_as_tensor`, `decode_img_as_tensor`, or `read_html`.
- Interpreting `Document`, `Page`, `KIEDocument`, `KIEPage`, `Block`, `Line`, `Word`, `Prediction`, `Artefact`, `LayoutElement`, `Table`, and `TableCell` outputs.
- Exporting result objects as plain text, JSON/dicts, XML/hOCR, Markdown, AsciiDoc, or HTML with reading-order behavior.
- Diagnosing page array shape/channel/dtype, missing `html` or `viz` extras, `show()` dependencies, unsupported export formats, or hOCR limitations.

## Do not handle here

- Creating or configuring `ocr_predictor` / `kie_predictor`, model architectures, device placement, or batch sizing; route to [`../core-ocr-and-kie/SKILL.md`](../core-ocr-and-kie/SKILL.md).
- Advanced model factory, Hugging Face Hub, custom weights, ONNX export, or optimization decisions; route to [`../models-and-customization/SKILL.md`](../models-and-customization/SKILL.md).
- CLI command usage or batch helper scripts; route to [`../cli-and-scripts/SKILL.md`](../cli-and-scripts/SKILL.md).

## Operating references

1. Read [`references/io-and-export-reference.md`](references/io-and-export-reference.md) for input APIs, expected page array contracts, object schema, reading-order semantics, and export workflows.
2. Read [`references/troubleshooting.md`](references/troubleshooting.md) when loading, visualization, JSON/XML, KIE, table, or format-dispatch behavior is surprising.
3. Use [`scripts/inspect_document_export.py`](scripts/inspect_document_export.py) for a safe local smoke inspection of DocumentFile loading and synthetic Document/KIEDocument exports. The script does not run predictors or download model weights.

## Quick rules

- `DocumentFile.*` returns a list of pages; each page is normally a NumPy `uint8` array with shape `(H, W, 3)` in RGB order.
- `DocumentFile.from_pdf(...)` rasterizes every PDF page; page index in the result corresponds to the input page order.
- `DocumentFile.from_url(...)` needs the `html` extra because it uses WeasyPrint to render a URL to PDF before rasterization.
- `show()` on `Document`, `Page`, `KIEDocument`, and `KIEPage` needs the `viz` extra because it uses visualization dependencies.
- `render()`, `export()`, `export_as_xml()`, Markdown, AsciiDoc, HTML, and `export_as(...)` share reading-order linearization by default.
- Tables are structured objects (`Table`/`TableCell`) as well as exportable text grids; table text is not duplicated in regular page blocks when table detection is used.
- OCR and KIE outputs differ: OCR pages group content spatially as `blocks -> lines -> words`, while KIE pages group predictions by semantic class name.
