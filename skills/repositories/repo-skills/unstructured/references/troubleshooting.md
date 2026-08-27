# Troubleshooting

Use this reference for cross-cutting Unstructured install, import, CLI, optional dependency, and workflow failures. For workflow-specific errors, also read the nearest sub-skill troubleshooting reference.

## Install and Import

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: unstructured` | Package is not installed in the active Python | Install with `pip install unstructured` or use the environment where the package is installed. |
| Import works but a format fails | Optional extra for that document family is missing | Run `unstructured doctor --for TYPE`, then install the named extra such as `unstructured[pdf]`, `unstructured[docx]`, or `unstructured[xlsx]`. |
| `python-magic` or MIME detection warning | Libmagic library/module missing or not loadable | Install the OS libmagic package and `python-magic`; use `content_type` or `metadata_filename` when detection needs help. |
| Very slow install or large dependency graph | Broad extras such as `all-docs`, `image`, `local-inference`, `huggingface`, or `ingest` | Install only extras required for selected formats/providers. |
| Python version conflict | Package requires Python `>=3.11,<3.14` for this snapshot | Use a supported Python version and reinstall dependencies. |

## Doctor Diagnostics

Use doctor before guessing dependencies:

```bash
unstructured doctor
unstructured doctor --for pdf
unstructured doctor --for image
unstructured doctor --for docx
unstructured doctor --file report.pdf
```

Doctor reports Python dependency readiness and common system tools. Missing tools are not always blockers for every workflow; for example, text/HTML workflows may work without OCR tools.

## System Tools

| Tool | Needed for | Notes |
| --- | --- | --- |
| `libmagic` | Better MIME detection | Fallback detection can still work for many paths, but ambiguous files need help. |
| `tesseract` | OCR for images/scanned PDFs | Install language packs that match `languages`. |
| `poppler-utils` | PDF/image conversion workflows | Often needed with OCR or page rendering. |
| `soffice` | Legacy `.doc` and `.ppt` conversion | Comes from LibreOffice. |
| `pandoc` | Some pypandoc-backed formats | The Python binary package may provide it, but PATH issues can still happen. |
| `ffmpeg` | Audio transcription | Required by Whisper audio decoding. |

## API and Network Workflows

- URL partitioning uses HTTP requests; always set `request_timeout` for unreliable endpoints.
- API partitioning needs endpoint configuration, credentials, and network access. Do not hardcode keys in scripts or examples.
- Provider embeddings need SDK packages and credentials. Use the `embeddings` sub-skill checker to verify presence without printing secrets.
- Annotation or staging integrations can require external service schemas or credentials; keep local staging transformations separate from upload/sync steps.

## Runtime Hangs or Slow Processing

- Large PDFs, OCR, layout inference, image extraction, and audio transcription can be slow or download models.
- Prefer `strategy="fast"` for extractable PDFs when layout/OCR/table image extraction is unnecessary.
- Use `strategy="ocr_only"` for scanned documents when text is enough.
- Avoid `all-docs` or `local-inference` unless the user explicitly wants broad local format coverage.
- Set explicit timeouts for URL workflows and avoid running provider/network calls without approval.

## Data and Output Shape

- `partition()` accepts exactly one of `filename`, `file`, or `url`; document-specific functions may accept `text` instead.
- Element JSON is a list of dictionaries with sparse `metadata`. Missing keys often mean unset fields, not failed serialization.
- Table fidelity usually depends on `metadata.text_as_html` and sometimes `metadata.table_as_cells`; preserve both when evaluating or converting tables.
- `metadata.orig_elements` can make chunk JSON large. Disable it when downstream systems do not need original element recovery.
