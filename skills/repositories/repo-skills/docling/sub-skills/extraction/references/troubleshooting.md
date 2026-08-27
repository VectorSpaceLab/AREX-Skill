# Extraction Troubleshooting

## Unsupported Input Format

Symptoms:

- Extraction fails before model inference.
- Error mentions no default extraction backend for a format.
- No recognizable format is found or the file is not in `allowed_formats`.

Fixes:

- Use `DocumentExtractor(allowed_formats=[InputFormat.IMAGE, InputFormat.PDF])` for default extraction.
- Route DOCX, PPTX, HTML, Markdown, CSV, XLSX, XML, audio, EPUB, email, LaTeX, and other conversion tasks to the conversion sub-skill unless a custom extraction backend is explicitly configured.
- Check `max_file_size`, `max_num_pages`, and `page_range` for overly strict limits.

## Missing Model or Backend Extras

Symptoms:

- Import or runtime errors involving VLM, transformers, model foundation packages, image/PDF backends, accelerator devices, or missing artifacts.
- First run is slow because model artifacts are downloaded.
- Extraction works in one environment but fails in a slim or minimal installation.

Fixes:

- Install a Docling variant with VLM support for local extraction, for example a public package install that includes the VLM extra when available.
- Prepare model artifacts before offline or production runs.
- Keep ASR and audio tasks separate; ASR needs the ASR extra and `ffmpeg` and is not the same path as PDF/image extraction.
- For GPU, MLX, API-backed models, or advanced backends, use the `advanced-pipelines` sub-skill.

## Template Mismatch

Symptoms:

- `extracted_data` is `None` but `raw_text` contains text.
- Pydantic validation fails because fields are missing, wrong type, or nested differently.
- A template object raises `Unsupported template type`.

Fixes:

- Pass only supported template types: `str`, `dict`, Pydantic model instance, or Pydantic model class.
- For Pydantic class templates, include `Field(examples=[...])` and defaults where helpful; Docling uses these to build a representative prompt instance.
- Validate `result.pages[*].extracted_data` with the same model and show validation errors to refine the template.
- If raw output is not JSON, make the template or string prompt explicitly request JSON matching the schema.

## Extraction Result Validation

Symptoms:

- Overall `result.status` is `PARTIAL_SUCCESS`.
- Some pages have data and other pages have page-level errors.
- Stop reason indicates length or stop-sequence truncation.

Fixes:

- Treat `PARTIAL_SUCCESS` as incomplete and inspect every `ExtractedPageData` item.
- Reduce `page_range`, simplify the schema, or split extraction into smaller page groups.
- Log `raw_text` for failed pages, but avoid storing sensitive document content in shared artifacts.

## Remote Service Opt-In

Symptoms:

- Remote model/service configuration appears ignored.
- Pipeline internals reject remote service use.
- CLI or service client calls fail with missing URL or authentication.

Fixes:

- Remote services require explicit opt-in such as `enable_remote_services` in the relevant pipeline options; do not assume local extraction will call remote endpoints.
- Remote service clients and remote CLI flows need a service URL and optional API key supplied by the environment owner.
- Do not embed API keys, local service URLs, or machine-specific paths in reusable skill content or scripts.
