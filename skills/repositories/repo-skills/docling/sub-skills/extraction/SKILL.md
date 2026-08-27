---
name: extraction
description: "Use Docling structured extraction with DocumentExtractor, VLM
  extraction templates, and safe local fixtures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Docling Structured Extraction

Use this sub-skill when the user wants structured field extraction from PDF or image documents with `DocumentExtractor`, extraction templates, and page-level extraction results.

Route elsewhere when the task is primarily:
- General document conversion, parsing, or `DoclingDocument` creation: use the `conversion` sub-skill.
- Output serialization to Markdown, JSON, YAML, HTML, text, doctags, VTT, or Docling JSON: use the `document-outputs` sub-skill.
- VLM backend selection, accelerator configuration, remote service wiring, or model/download strategy: use the `advanced-pipelines` sub-skill.

## Quick Use

- Install an extraction-capable Docling package variant before runtime extraction; VLM extraction needs model/backend dependencies beyond a minimal import-only install.
- Start with `DocumentExtractor(allowed_formats=[InputFormat.IMAGE, InputFormat.PDF])` because default extraction backends are configured for images and PDFs.
- Pass a template as a JSON-like string, `dict`, Pydantic model instance, or Pydantic model class.
- Validate `result.pages[*].extracted_data` with your own Pydantic model before trusting fields downstream.
- Keep fixture runs explicit and local; do not assume model artifacts are already downloaded unless the environment owner has prepared them.

## References

- `references/api-reference.md` covers `DocumentExtractor`, extraction options, template types, and result models.
- `references/workflows.md` provides recipes for small field extraction, Pydantic validation, and safe fixture runs.
- `references/troubleshooting.md` lists common failures including unsupported formats, missing model extras, template mismatches, and remote opt-in.
- `scripts/extract_fixture.py` is a safe helper for local image/PDF fixture extraction; it prints help and never downloads by default.
