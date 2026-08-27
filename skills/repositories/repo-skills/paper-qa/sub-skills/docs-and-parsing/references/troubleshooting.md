# Troubleshooting parsing and chunking

This guide focuses on local document parsing, chunking, optional PDF readers,
Office parsing, media extraction, and multimodal enrichment. For LLM/provider
selection details, use the settings sub-skill; for querying failures, use the
agentic RAG sub-skill.

## Quick diagnostic order

1. Run `../scripts/inspect_parsers.py` in the active environment. Confirm
   `paperqa.readers` imports and note which optional parser modules are missing.
2. For text-like files, run `../scripts/parse_text_smoke.py` or the same script
   with `--path your_file.md` to separate core parse/chunk issues from PDF extras.
3. For PDFs, first try a cheap parse-only read:

   ```python
   from paperqa.types import Doc
   from paperqa.readers import read_doc
   from paperqa_pypdf import parse_pdf_to_pages

   parsed = await read_doc(
       "problem.pdf",
       Doc(docname="problem", citation="local", dockey="problem"),
       parsed_text_only=True,
       parse_pdf=parse_pdf_to_pages,
       page_range=(1, 3),
       parse_media=False,
   )
   ```

4. Add media only after text parsing succeeds. Add enrichment only after media
   parsing succeeds and model credentials/budget are intentionally configured.

## Missing default PDF parser

Symptom:

- `ImportError: To parse PDFs we need a parsing function... install either
  paper-qa[pypdf] ... or paper-qa[pymupdf]`.
- `read_doc(...pdf...)` raises `ValueError: When parsing a PDF, a parsing
  function must be provided.`

Likely causes:

- Neither `paperqa_pymupdf` nor `paperqa_pypdf` is importable.
- You called `read_doc` directly for a PDF without passing `parse_pdf`.

Fix:

- Install the lightweight default: `pip install 'paper-qa[pypdf]'` or
  `pip install paper-qa-pypdf`.
- Or install PyMuPDF reader: `pip install 'paper-qa[pymupdf]'` / `paper-qa-pymupdf`,
  after reviewing the AGPL license note below.
- Pass the parser explicitly when using `read_doc` directly.
- Use `Settings(parsing={"parse_pdf": "paperqa_pypdf.parse_pdf_to_pages"})` only
  after the package is installed.

## Corrupt, empty, or non-PDF files

Symptoms:

- `ImpossibleParsingError` mentioning corrupt PDF.
- `ValueError` from `Docs.aadd` saying the document does not look like text.
- Empty chunks or `ImpossibleParsingError: No text was parsed... either empty or
  corrupted`.
- A downloaded `.pdf` is actually an HTML 404 page.

Fix:

- Confirm file exists and has nonzero size before parsing.
- Open the first bytes or use a system `file` utility if available to verify it
  is really a PDF, not HTML or an error page.
- Try `parse_media=False` and a small `page_range` to determine whether text
  extraction works independently of media dependencies.
- If a legitimate image-only PDF yields empty text, use a layout/VLM reader
  (Docling or Nemotron) or an OCR-capable upstream process; pypdf/PyMuPDF text
  extraction cannot invent OCR text by itself.
- If `Docs.aadd` validation blocks a known valid special case, inspect parsed
  text first; only then consider `ParsingSettings(disable_doc_valid_check=True)`
  with explicit citation/title metadata.

## Page size limit failures

Symptom:

- `ImpossibleParsingError` mentions a page being too many characters and
  exceeding `page_size_limit`.

Meaning:

- `page_size_limit` is a guard against runaway/corrupt parses. Default settings
  use `1_280_000` characters per page.

Fix:

- For genuinely huge pages, raise `Settings(parsing={"page_size_limit": ...})`
  or pass `page_size_limit=` directly to the parser.
- For corrupt PDFs that concatenate pages or decode binary as text, do not just
  raise the limit. Try another reader, `page_range`, or `parse_media=False` to
  isolate the bad page.
- For split-line generic parsing, check whether the file should be treated as
  `.txt` rather than line-page content.

## Office and unstructured import errors

Symptom:

- `ImportError: Could not import unstructured dependencies. Please install with
  pip install paper-qa[office].`
- `.docx`, `.xlsx`, or `.pptx` parsing fails before reading content.

Fix:

- Install `paper-qa[office]`, which brings `unstructured[docx,xlsx,pptx]`.
- If using an existing environment, verify the install is allowed before mutating
  it; Office extras can add large transitive dependencies.
- Retry with a simple `.txt` export if only text content is needed and Office
  rendering/table extraction is not essential.
- Forward `unstructured` partition kwargs cautiously through `reader_config` only
  when you know the target partitioner supports them.

## pypdf media, pypdfium2, Pillow, and pdfplumber failures

Symptoms:

- `ImportError` says media parsing requires `pypdfium2`.
- `ImportError` says full-page or figure rendering requires Pillow.
- Tables or clustered figures are absent when using pypdf.
- Individual images parse but no tables or figure clusters appear.

Meaning:

- Base `paper-qa-pypdf` only guarantees pypdf text extraction.
- `paper-qa-pypdf[media]` adds `pypdfium2`, Pillow, and PyPDF image support for
  screenshots and individual image extraction.
- `paper-qa-pypdf[enhanced]` adds `pdfplumber` on top of media support for table
  parsing and image clustering.

Fix:

- If media are not needed, set `multimodal=False` or pass `parse_media=False`.
- For full-page screenshots: install `paper-qa-pypdf[media]`, then pass
  `full_page=True` and optionally `dpi=...`.
- For clustered figures/tables: install `paper-qa-pypdf[enhanced]`.
- If high DPI causes memory or provider image-size issues, lower `dpi`, use
  `parse_media=False`, or parse fewer pages with `page_range`.

## PyMuPDF AGPL/license note

PaperQA's default parser resolver prefers `paperqa_pymupdf` when it is importable.
The PyMuPDF-backed reader package advertises AGPLv3 licensing. Before using it in
proprietary, distributed, or compliance-sensitive workflows:

- Confirm license obligations with the project owner/legal reviewer.
- If AGPL is unacceptable, force pypdf or another allowed reader:

  ```python
  from paperqa import Settings
  from paperqa_pypdf import parse_pdf_to_pages
  settings = Settings(parsing={"parse_pdf": parse_pdf_to_pages})
  ```

- Remember that installing PyMuPDF can silently change the default parser choice
  unless you pin `parse_pdf` explicitly.

## Docling heavy dependency and timeout failures

Symptoms:

- Import fails for `docling`, `docling_core`, or model/backend packages.
- First parse is slow or uses high memory.
- `ImpossibleParsingError` mentions Docling conversion failed or partial status.

Fix:

- Install `paper-qa[docling]` or `paper-qa-docling` only when layout/model-aware
  parsing is required.
- For bounded runs, pass `custom_pipeline_options` such as a document timeout.
- Use `page_range` for a quick diagnostic before parsing a long PDF.
- Fall back to pypdf or PyMuPDF if the document does not need Docling's layout,
  formula, table, or image behavior.

## Nemotron NVIDIA API, SageMaker, and failover parser

Symptoms:

- `KeyError` or provider failure for `NVIDIA_API_KEY`.
- LiteLLM/NVIDIA timeouts, rate limits, bbox validation errors, or length errors.
- SageMaker path fails because `aiobotocore` is missing.
- Large documents exhaust memory or service quotas.

Requirements:

- Hosted NVIDIA API: install `paper-qa[nemotron]` or `paper-qa-nemotron` and set
  `NVIDIA_API_KEY` in the runtime environment.
- SageMaker: install `paper-qa-nemotron[sagemaker]`, have AWS credentials/region
  configured, and pass `api_params={"model_name": "sagemaker/nvidia/nemotron-parse"}`
  plus endpoint parameters as needed.

Fix:

- Reduce `concurrency` and/or `dpi` for memory, payload, or provider-size limits.
- Use `page_range` to diagnose one or two pages first.
- Provide a failover parser for bbox/timeout/length failures:

  ```python
  from paperqa import Settings
  from paperqa_nemotron import parse_pdf_to_pages

  settings = Settings(parsing={
      "parse_pdf": parse_pdf_to_pages,
      "reader_config": {
          "failover_parser": "paperqa_pypdf.parse_pdf_to_pages",
          "concurrency": 8,
          "dpi": 216,
      },
  })
  ```

- If the failure is service credentials or policy, choose pypdf, PyMuPDF, or
  Docling instead of retrying unauthenticated Nemotron calls.

## Media enrichment provider issues

Symptoms:

- Media parsing succeeds, but document addition fails during enrichment.
- Provider rejects an image as too large, corrupt, unsupported, or invalid.
- Enrichment requires API keys for `parsing.enrichment_llm`.
- Retrieved contexts miss figure-only evidence when enrichment is disabled.

Meaning:

- Parsing media is not the same as enriching media. Enrichment uses an LLM at
  document-read time to add descriptions for embeddings. It can cost one or more
  prompts per media item.

Fix:

- If you need media bytes but cannot call an enrichment provider, set
  `parsing.multimodal` to `MultimodalOptions.ON_WITHOUT_ENRICHMENT`.
- If you want text-only parsing, set `multimodal=False`.
- Lower `dpi` or use `full_page=False` to reduce image sizes.
- Configure the enrichment provider and prompt in the settings sub-skill; do not
  mix parser debugging with model-selection changes.
- If media are useful but not necessary, allow text-only fallback at the answer
  workflow level rather than forcing every document read to enrich.

## HTML, Markdown, and code surprises

Symptoms:

- HTML text includes Markdown formatting or links.
- Markdown/source files produce line-range chunk names instead of token-overlap
  text chunk names.
- Binary-ish files produce odd text or empty code chunks.

Fix:

- For HTML, this is expected: `parse_text(html=True)` uses `html2text`.
- For Markdown as prose, call `parse_text(path, split_lines=False)` and then
  `chunk_text` directly if line-based code chunks are not desired.
- For source code, provide explicit citations/docnames because PaperQA cannot
  infer scholarly citations from code.
- Exclude generated/vendor/binary files before `Docs.aadd`; file scanning and
  filters are owned by the CLI/indexing sub-skill.

## Reader-choice decision failures

If a workflow keeps switching readers without improving results, write down the
constraint being optimized:

- License-safe and lightweight: pypdf text-only.
- Figures/tables without services: pypdf enhanced or PyMuPDF, subject to license.
- Better layout/formulas with local heavy deps: Docling.
- Best-effort VLM reading with credentials and cost budget: Nemotron with
  failover parser.

Then run the same `page_range`, `parse_media`, `full_page`, `dpi`, and
`chunk_chars` settings across candidates so differences are attributable to the
reader, not to chunking or media options.
