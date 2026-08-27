---
name: unstructured
description: "Use the Unstructured Python package to partition documents into
  elements, inspect element metadata, chunk outputs for RAG, clean/stage data,
  add embeddings, evaluate extraction quality, and diagnose optional dependency
  readiness."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Unstructured

Use this repo skill when a task involves the `unstructured` Python package for preparing raw documents for downstream ML, RAG, annotation, enrichment, or evaluation workflows.

## Start Here

1. Identify the workflow: partition documents, inspect elements, chunk for RAG, clean/stage outputs, add embeddings, evaluate quality, or debug installation.
2. Install only the extras needed for the requested formats or providers; do not default to `all-docs` or `ingest` unless the user explicitly needs broad coverage.
3. Run `unstructured doctor` or `python -m unstructured.cli doctor` when a format fails because many capabilities depend on optional Python packages and system tools.
4. Keep source documents, generated output JSON, metrics, credentials, and temporary work outside this skill tree.

## Common Install Patterns

```bash
pip install unstructured
pip install "unstructured[docx,pptx,xlsx]"
pip install "unstructured[pdf,image]"
pip install "unstructured[csv,md,rtf,epub]"
```

Base install is enough for text, HTML, XML, JSON/NDJSON, email, and core APIs. Optional extras add document families, OCR/PDF/image support, audio transcription, token chunking, provider embeddings, and external ingest connectors.

Common system tools:

- `libmagic` improves MIME detection through `python-magic`.
- `tesseract` and `poppler-utils` are commonly needed for OCR/PDF/image workflows.
- `soffice` from LibreOffice is needed for legacy `.doc` and `.ppt` conversion.
- `pandoc` is needed by pypandoc-backed formats when the bundled binary is unavailable.
- `ffmpeg` is needed for audio decoding.

## Route by Task

- Use `sub-skills/partitioning/SKILL.md` to turn files, streams, URLs, text, HTML, PDFs/images, Office documents, tabular data, email, JSON, XML, markup, books, or audio into `Element` objects.
- Use `sub-skills/elements-and-metadata/SKILL.md` to inspect `Element` subclasses, metadata, coordinates, data-source metadata, table HTML/cells, JSON/NDJSON, Markdown, text, or HTML staging.
- Use `sub-skills/chunking/SKILL.md` to configure `chunk_elements()`, `chunk_by_title()`, integrated partition chunking, token/character limits, overlap, table behavior, and `orig_elements` retention.
- Use `sub-skills/data-preparation/SKILL.md` to clean extracted text, stage annotation outputs, use lightweight NLP helpers, or prepare local outputs for downstream systems.
- Use `sub-skills/embeddings/SKILL.md` to add embeddings to elements with OpenAI, OctoAI, Mixedbread, VoyageAI, VertexAI, Bedrock, or Hugging Face providers while keeping credentials safe.
- Use `sub-skills/evaluation/SKILL.md` to compare predicted and gold outputs with text extraction, element type, table, and optional object detection metrics.

## Diagnostic Workflow

```bash
python -m unstructured.cli doctor
python -m unstructured.cli doctor --for pdf
python -m unstructured.cli doctor --file report.pdf
```

If the console script is installed, `unstructured doctor` is equivalent. The doctor command reports Python dependency readiness per file type and checks common system tools. Use it before installing broad extras or debugging a partitioning error by trial and error.

For a reusable local diagnostic wrapper, use `sub-skills/partitioning/scripts/partition_diagnostics.py`. For package-level environment snapshots, use `scripts/inspect_unstructured_environment.py`.

## End-to-End Patterns

### Partition, Chunk, and Serialize

```python
from unstructured.partition.auto import partition
from unstructured.staging.base import elements_to_json

chunks = partition(
    filename="report.pdf",
    strategy="auto",
    chunking_strategy="by_title",
    max_characters=1200,
    new_after_n_chars=900,
    include_orig_elements=False,
)
json_text = elements_to_json(chunks, indent=2)
```

Use `partitioning` for format-specific options, `chunking` for sizing/table/orig-elements decisions, and `elements-and-metadata` for JSON/output details.

### Inspect Tables After Partitioning

```bash
python sub-skills/partitioning/scripts/inspect_tables.py elements.json --out-dir tables --index
```

Use this after exporting elements to JSON when table structure or `metadata.text_as_html` must be validated.

### Compare Output to Gold

```bash
python sub-skills/evaluation/scripts/evaluate_elements_pair.py \
  --prediction predicted.json \
  --gold gold.json
```

Use the evaluation sub-skill before running large metric batches so shape and obvious mismatches are caught locally.

## Safety and Boundaries

- Do not store API keys, tokens, provider credentials, or private endpoints in scripts, examples, or logs.
- Do not run network/API, provider embedding, external ingest, OCR/model download, Docker, or benchmark workflows without explicit user approval.
- Do not assume PDF/image/audio/Office extras or system tools are installed; run diagnostics and install the minimum necessary set.
- Do not write review artifacts, native test outputs, or temporary metrics inside this runtime skill directory.

## References

- Read `references/troubleshooting.md` for cross-cutting install/import, optional dependency, system tool, and CLI/API failure modes.
- Read `references/repo-provenance.md` before refreshing this skill against a newer checkout.
- Use `scripts/inspect_unstructured_environment.py` for a credential-safe environment and capability summary.
