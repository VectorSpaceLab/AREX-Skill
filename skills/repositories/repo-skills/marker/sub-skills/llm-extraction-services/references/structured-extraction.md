# Structured Extraction

Use `marker.converters.extraction.ExtractionConverter` when the goal is a JSON object that conforms to a schema, not just markdown/HTML/JSON rendering of document blocks. It is beta behavior and requires an LLM service.

## Contract

- Input document can be parsed normally, or extraction can reuse `existing_markdown` from a previous extraction run.
- `page_schema` is required and should be a JSON-schema-shaped object or JSON string describing the target extraction output.
- `ExtractionConverter` forces `paginate_output=True` and `output_format="markdown"` internally so it can split markdown into pages before extraction.
- Page extraction first asks the LLM for detailed page notes; document extraction then asks the LLM to merge notes into the schema-shaped result.
- The rendered object is `ExtractionOutput` with `analysis`, `document_json`, and `original_markdown` fields.

## Minimal Pydantic schema flow

```python
from pydantic import BaseModel
from marker.config.parser import ConfigParser
from marker.converters.extraction import ExtractionConverter
from marker.models import create_model_dict

class InvoiceLine(BaseModel):
    description: str
    amount: float

class Invoice(BaseModel):
    vendor: str
    invoice_number: str
    lines: list[InvoiceLine]

options = {
    "use_llm": True,
    "page_schema": Invoice.model_json_schema(),
    "gemini_api_key": "...",  # inject outside shared code
}
parser = ConfigParser(options)
converter = ExtractionConverter(
    artifact_dict=create_model_dict(),
    config=parser.generate_config_dict(),
    processor_list=parser.get_processors(),
    renderer=parser.get_renderer(),
    llm_service=parser.get_llm_service(),
)
result = converter("invoice.pdf")
print(result.document_json)
```

## Reuse existing markdown

If a previous extraction returned `original_markdown`, pass it as `existing_markdown` to skip reparsing the source document:

```python
options = {
    "use_llm": True,
    "page_schema": Invoice.model_json_schema(),
    "existing_markdown": previous_result.original_markdown,
    "llm_service": "marker.services.openai.OpenAIService",
    "openai_api_key": "...",
}
```

Keep the original source document path available when calling the converter, even when reusing markdown, because the converter interface still accepts a filepath. Existing markdown must use Marker’s paginated separator format; arbitrary markdown without page separators can produce empty page chunks.

## JSON schema files

A schema file should contain an object at the root:

```json
{
  "title": "Invoice",
  "type": "object",
  "properties": {
    "vendor": {"type": "string"},
    "invoice_number": {"type": "string"},
    "total": {"type": "number"}
  },
  "required": ["vendor", "invoice_number"]
}
```

From this sub-skill directory, validate schema shape before any LLM call:

```bash
python scripts/validate_extraction_schema.py schema.json
```

For Python schemas, define one clear Pydantic `BaseModel` root class, or pass `--root-class`:

```bash
python scripts/validate_extraction_schema.py schema.py --root-class Invoice
```

## Output handling

`document_json` is a string that should contain JSON. Parse and validate it against your own Pydantic model after conversion:

```python
import json
invoice = Invoice.model_validate(json.loads(result.document_json))
```

If validation fails, keep `analysis` for debugging, tighten the schema descriptions, reduce page range, increase retries/timeouts, or switch to a provider/model with better JSON-schema adherence.
