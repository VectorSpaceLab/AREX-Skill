# Extraction Workflows

## Small Structured Field Extraction

Use this recipe when the user wants a compact structured extraction from a local PDF or image and does not need a full converted `DoclingDocument`.

```python
from pathlib import Path
from pydantic import BaseModel, Field

from docling.datamodel.base_models import InputFormat
from docling.document_extractor import DocumentExtractor

class ReceiptFields(BaseModel):
    merchant: str | None = Field(default=None, examples=["Example Store"])
    receipt_id: str | None = Field(default=None, examples=["R-1001"])
    total: float | None = Field(default=None, examples=[42.50])
    currency: str | None = Field(default=None, examples=["USD"])

extractor = DocumentExtractor(allowed_formats=[InputFormat.IMAGE, InputFormat.PDF])
result = extractor.extract(
    source=Path("receipt.pdf"),
    template=ReceiptFields,
    max_num_pages=1,
    page_range=(1, 1),
)

if result.errors:
    raise RuntimeError(result.errors)

first_page = result.pages[0]
if first_page.errors:
    raise RuntimeError(first_page.errors)

fields = ReceiptFields.model_validate(first_page.extracted_data)
print(fields.model_dump())
```

Why this works:

- Restricts extraction to PDF/image formats with default extraction backends.
- Limits to the first page for cost and latency.
- Uses a Pydantic class template for clear expected fields.
- Revalidates `extracted_data` before downstream use.

## Template Choice

Choose the smallest template that communicates the schema:

- Use a `dict` for quick one-off extraction: `{"bill_no": "string", "total": "number"}`.
- Use a Pydantic class when the caller needs validation, nested structures, examples, defaults, or reusable field definitions.
- Use a Pydantic instance when caller-provided context or defaults should influence the prompt.
- Use a string only when you need a custom free-form prompt; make it explicit that JSON output is required.

## Multi-Page Extraction

For small multi-page documents, widen `page_range` deliberately:

```python
result = extractor.extract(
    source=Path("statement.pdf"),
    template={"account": "string", "ending_balance": "number"},
    max_num_pages=3,
    page_range=(1, 3),
)

for page in result.pages:
    print(page.page_no, page.extracted_data or page.raw_text, page.errors)
```

Do not silently process unbounded PDFs. Pass `max_num_pages`, `max_file_size`, and `page_range` according to the user's fixture and budget.

## Safe Fixture Script

The bundled `scripts/extract_fixture.py` helper provides a safe local entry point:

```bash
python scripts/extract_fixture.py --help
python scripts/extract_fixture.py \
  --source ./fixture.pdf \
  --template-json '{"invoice_number":"string","total":"number"}' \
  --max-pages 1
```

The script only processes explicit local files. It does not fetch remote files, predownload model artifacts, mutate project files, or configure remote services.

## Validating Results

Always inspect both structured and raw outputs:

```python
for page in result.pages:
    if page.errors:
        print("page errors", page.page_no, page.errors)
    elif page.extracted_data is None:
        print("raw model output", page.page_no, page.raw_text)
    else:
        print("parsed JSON", page.page_no, page.extracted_data)
```

Use Pydantic validation for application contracts. If validation fails, refine the template with field examples, defaults, nested models, or stricter prompt wording, then rerun on a small page range.
