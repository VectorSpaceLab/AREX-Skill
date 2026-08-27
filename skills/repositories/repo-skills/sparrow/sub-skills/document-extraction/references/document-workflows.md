# Document extraction workflows

Use this reference to construct Sparrow Parse document flows before invoking an actual backend.

## 1. Query forms

### Schema extraction

Sparrow's pipeline expects the user query to be valid JSON. The JSON is an example schema, not a JSON Schema document.

Examples:

```json
{"invoice_number":"str","date":"str","total":0.0}
```

```json
[{"instrument_name":"str","valuation":"int","currency":"str or null"}]
```

Supported validation tokens include primitive examples (`0`, `0.0`) and strings such as `"str"`, `"int"`, `"float"`, `"str or null"`, `"int or null"`, `"float or null"`, `"0 or null"`, and `"0.0 or null"`. Nested objects and arrays of objects are supported by the pipeline validator.

The pipeline transforms a schema query into this instruction pattern:

```text
retrieve data based on provided JSON schema. return response in JSON format, by strictly following this JSON schema: <schema>. If a field is not visible or cannot be found in the document, return null. Do not guess, infer, or generate values for missing fields.<optional hints>
```

Use `scripts/parse_request_builder.py` to produce the exact prepared prompt and backend config without running a model.

### Wildcard all-data extraction

Use query `"*"` when the user wants all visible data and does not require schema validation. The extractor's `generic_query=True` path replaces the text input with:

```text
retrieve document data. return response in JSON format
```

Wildcard output is unconstrained by a schema; diagnose it as a VLM extraction quality issue rather than a schema-validation issue.

### Page-type detection

Use query `"*"` plus one or more page-type labels when the task is classification rather than data extraction. The pipeline prompt is:

```text
detect page type based on this list of types - invoice, table, receipt. return response in JSON format
```

Page-type mode turns validation off. For multi-page PDFs, expect one JSON-like result per page after PDF splitting; the pipeline adds `"page"` fields in normal multi-page output handling.

### Hints file

`hints_file_path` is optional and is read only when it ends in `.json` and contains valid JSON. Its JSON content is appended under `Additional Hints:` in schema and markdown extraction prompts. Invalid or unreadable hints are silently ignored by the pipeline, so validate hints with the request builder when the task depends on them.

Use hints for:

- field disambiguation such as supplier versus recipient;
- date and number normalization;
- prioritizing footer or fine-print fields;
- telling the model how to handle ambiguous table names.

## 2. Direct `VLLMExtractor` flow

Direct package calls are the smallest surface for code-level extraction.

```python
from sparrow_parse.extractors.vllm_extractor import VLLMExtractor
from sparrow_parse.vlmb.inference_factory import InferenceFactory

config = {"method": "ollama", "model_name": "mistral-small3.2:24b-instruct-2506-q8_0"}
model = InferenceFactory(config).get_inference_instance()
input_data = [{
    "file_path": "document.png",                 # image path, PDF path, or None for text-only
    "text_input": "retrieve data based on provided JSON schema. return response in JSON format, by strictly following this JSON schema: {\"invoice_number\":\"str\",\"total\":0.0}"
}]
results, num_pages = VLLMExtractor().run_inference(model, input_data, debug=False)
```

Important distinction: direct `run_inference` returns raw backend responses. It does not add `valid`, does not add `page`, and does not validate output against the schema. Add your own JSON parsing/validation when using the package directly, or use the pipeline layer when those fields matter.

## 3. Image, PDF, and page handling

- Image files (`.png`, `.jpg`, `.jpeg`) go through `_process_non_pdf`.
- PDFs go through `PDFOptimizer.split_pdf_to_pages(..., convert_to_images=True)` and are converted to 300-DPI JPEG page images before inference.
- Non-table PDF pages are sent as a list of image files in a single `input_data[0]["file_path"]` list.
- Table-only PDF pages are processed page by page, and table crops are inferred one crop at a time.
- Text-only inference is selected when `file_path` is missing or `None`; it returns `num_pages == 0`.

### PDF helper

```python
from sparrow_parse.helpers.pdf_optimizer import PDFOptimizer
num_pages, output_files, temp_dir = PDFOptimizer().split_pdf_to_pages(
    "document.pdf",
    debug_dir="debug",
    convert_to_images=True,
)
```

`convert_to_images=True` requires poppler. Use `debug_dir` only when the user wants intermediate page images retained for inspection.

### Image crop helper

```python
from sparrow_parse.helpers.image_optimizer import ImageOptimizer
cropped_path = ImageOptimizer().crop_image_borders(
    "scan.jpg",
    temp_dir="tmp",
    debug_dir="debug",
    crop_size=60,
)
```

`crop_size` removes that many pixels from all four borders. If the crop would remove the entire image, the helper raises an error. Cropping often improves invoices/scans with noisy borders, but it can also remove header/footer fields.

## 4. Table flows

### `tables_only` package flow

Set `tables_only=True` in `run_inference`, or include `tables_only` in pipeline backend options.

Behavior:

1. `TableDetector` loads `microsoft/table-transformer-detection`.
2. It detects table boxes and crops them with padding.
3. Each table crop is passed to the selected VLM backend.
4. Results are returned under a `page_tables` wrapper.
5. If no tables are found, the extractor returns:

```json
{"message":"No tables detected in the document","status":"empty"}
```

Use this for simple table-only extraction from pages or scans. It downloads/loads a separate detection model, so first run may be slow.

### Markdown/table-template flow

Sparrow's engine also has table and markdown workflows that are not just `VLLMExtractor.run_inference` flags:

- `--markdown` first converts the document to markdown with a DeepSeek OCR-style prompt, then asks the instructor pipeline to extract schema-shaped JSON from the markdown.
- `--table --table-template <name>` is for template-driven table extraction, often with dots.ocr HTML intermediate output for large or complex tables.

Use these when direct VLM JSON extraction is unstable on dense tables. If the user asks for REST/curl form construction for these flags, route that part to `api-engine-and-cli`.

## 5. Annotation flow

`apply_annotation` requests value/bbox/confidence style output where the backend supports it.

- Pipeline option: include `apply_annotation` after backend and model.
- Direct package: pass `apply_annotation=True` to `run_inference`.
- Validation is forced off by the pipeline when annotations are requested.
- The MLX Qwen path transforms the schema so each field asks for `value`, `bbox`, and `confidence`; it rescales bbox coordinates back to the original image size when the image was resized.
- Ollama and vLLM implementations explicitly disable annotations.

Use annotation only when the user needs coordinates for extracted fields. If annotation output is not valid JSON, first retry with a smaller schema and a Qwen-compatible model before treating it as an image issue.

## 6. Multi-page invoice extraction with page types

Difficult case: an invoice PDF contains a cover page, invoice body pages, and a terms/table page. A robust sequence is:

1. Run page-type detection with `query="*"` and page types such as `invoice_cover`, `invoice_body`, `invoice_items_table`, `terms`.
2. Inspect per-page labels and decide which schema applies to each page type.
3. Run schema extraction for invoice body pages:

```json
{
  "invoice_number": "str",
  "issue_date": "str",
  "seller": {"name": "str", "tax_id": "str or null"},
  "buyer": {"name": "str", "tax_id": "str or null"},
  "total_gross": 0.0,
  "currency": "str or null"
}
```

4. Run table extraction or a line-item schema for item pages:

```json
{
  "items": [{"description": "str", "quantity": 0.0, "unit_price": 0.0, "gross_amount": 0.0}],
  "summary": {"subtotal": 0.0, "tax": 0.0, "total": 0.0}
}
```

5. Preserve page numbers from the pipeline output when merging results.
6. Use hints to disambiguate repeated seller/buyer fields and footer totals.

## 7. Invalid JSON output/schema diagnosis

Difficult case: the query schema is valid JSON, but the VLM returns markdown, prose, or malformed JSON.

Diagnosis order:

1. Validate the query with `json.loads` before inference. If it fails, fix the user query; do not run a backend.
2. Build a smaller schema with one or two fields and no nesting.
3. Keep validation on unless using wildcard, markdown, page-type, instruction, validation-query, or annotation flow.
4. If pipeline output is `{"message":"Invalid JSON format in LLM output", ...}`, the backend response was not parseable as JSON. Retry with an explicit `return only raw JSON` hint, lower output complexity, or use markdown-first extraction for table-heavy documents.
5. If output is JSON but `valid` contains a schema validation error, compare actual types against the example schema. Replace overly strict numeric fields with nullable/string-compatible fields when source values include currency symbols, thousands separators, or missing values.

## 8. Request builder helper

The bundled helper prints a no-inference plan:

```bash
python ../scripts/parse_request_builder.py \
  --query '{"invoice_number":"str","total":0.0}' \
  --file-path invoice.pdf \
  --backend mlx \
  --model mlx-community/Qwen3.6-35B-A3B-8bit \
  --crop-size 60 \
  --hints-file-path hints.json
```

The output includes backend config, `input_data`, `run_inference` keyword arguments, validation behavior, and warnings. It does not call a VLM backend.
