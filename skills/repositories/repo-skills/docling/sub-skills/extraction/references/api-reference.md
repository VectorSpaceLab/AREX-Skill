# Extraction API Reference

Docling structured extraction is centered on `docling.document_extractor.DocumentExtractor`. It is separate from `DocumentConverter`: extraction produces page-level structured results, while conversion produces `DoclingDocument` objects for downstream export and chunking.

## Core Imports

```python
from pathlib import Path
from pydantic import BaseModel, Field

from docling.datamodel.base_models import InputFormat
from docling.document_extractor import DocumentExtractor
```

## `DocumentExtractor`

Constructor:

```python
DocumentExtractor(
    allowed_formats: list[InputFormat] | None = None,
    extraction_format_options: dict[InputFormat, ExtractionFormatOption] | None = None,
)
```

Important behavior:

- `allowed_formats=None` technically means all `InputFormat` values, but default extraction options are only configured for `InputFormat.IMAGE` and `InputFormat.PDF`; passing every format can fail when a default extraction backend is unavailable.
- Prefer `DocumentExtractor(allowed_formats=[InputFormat.IMAGE, InputFormat.PDF])` for normal local extraction.
- Default extraction uses `ExtractionVlmPipeline` with image/PDF backends and VLM extraction pipeline options.
- `extract(...)` returns one `ExtractionResult`; `extract_all(...)` iterates over several sources.

`extract` signature essentials:

```python
result = extractor.extract(
    source=Path("fixture.pdf"),
    template={"invoice_id": "string", "total": "number"},
    headers=None,
    raises_on_error=True,
    max_num_pages=1,
    max_file_size=20_000_000,
    page_range=(1, 1),
)
```

`source` can be a local `Path`, string path, or `DocumentStream`. Keep network/header use for controlled environments.

## Templates

`ExtractionTemplateType` accepts:

- `str`: often a JSON-like schema prompt such as `'{"bill_no": "string", "total": "number"}'`.
- `dict[str, Any]`: a lightweight schema object, serialized to JSON before model prompting.
- `BaseModel` instance: useful when defaults or context values should be included in the prompt.
- `type[BaseModel]`: Docling builds an example instance from defaults and `Field(examples=...)` before prompting.

Pydantic class templates can be nested:

```python
class Seller(BaseModel):
    name: str | None = Field(default=None, examples=["Example LLC"])
    tax_id: str | None = Field(default=None, examples=["123456789"])

class InvoiceFields(BaseModel):
    invoice_number: str = Field(examples=["INV-001"])
    total: float = Field(default=0.0, examples=[123.45])
    seller: Seller = Field(default_factory=Seller)
```

After extraction, validate model output explicitly:

```python
fields = InvoiceFields.model_validate(result.pages[0].extracted_data)
```

## Results

`ExtractionResult` contains:

- `input`: the `InputDocument` that was processed.
- `status`: a `ConversionStatus` value such as `SUCCESS`, `PARTIAL_SUCCESS`, or `FAILURE`.
- `errors`: extraction-level `ErrorItem` entries.
- `pages`: list of `ExtractedPageData`.

Each `ExtractedPageData` contains:

- `page_no`: 1-indexed page number, respecting `page_range`.
- `extracted_data`: parsed JSON object when the VLM response is valid JSON; otherwise `None`.
- `raw_text`: raw model text, always worth inspecting when `extracted_data` is empty.
- `errors`: page-specific errors.

Treat `PARTIAL_SUCCESS` as review-required. It can occur when a VLM stop reason indicates truncation or stop-sequence behavior.

## Extraction Pipeline Boundaries

The default VLM extraction pipeline renders each selected PDF page as an image, prompts a VLM with the serialized template, tries to parse JSON, and stores both parsed data and raw text per page.

Keep these boundaries clear:

- Extraction does not replace conversion; use conversion for `DoclingDocument` structure, reading order, exports, and chunking.
- Extraction is model-backed and can trigger artifact/model needs on first use.
- Advanced VLM backend setup, accelerator choices, remote services, and model cache strategy belong in `advanced-pipelines`.
- Serialization of final documents belongs in `document-outputs`; this sub-skill only covers extraction result handling.
