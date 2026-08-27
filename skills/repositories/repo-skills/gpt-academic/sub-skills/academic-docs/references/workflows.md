# Academic Document Workflows

## PDF translation and QA

For user-owned PDFs, GPT Academic offers standard PDF translation, batch PDF summary, and ChatPDF-like QA. The standard translation path automatically tries parser backends in a quality-oriented order: DOC2X when configured, then GROBID, then traditional text extraction.

Recommended workflow:

1. Confirm the PDF is text-based, not a scanned image. If it is scanned or formula-heavy, consider OCR/NOUGAT and warn about model downloads.
2. Run `scripts/check_doc_backends.py --repo-root <checkout>` and `sub-skills/academic-docs/scripts/check_document_input.py <path>`.
3. Pick the plugin by output: translation document, summary, or question-answering.
4. Reduce `DEFAULT_WORKER_NUM` if the provider rate-limits parallel translation.
5. Save intermediate Markdown/LaTeX outputs when available so a failure can be resumed or manually corrected.

## Arxiv and paper reading

Use Arxiv workflows when the user provides an Arxiv ID or paper URL and wants translation or summary. LaTeX-backed Arxiv translation can preserve equations better when source is available, but it needs network access and sometimes LaTeX binaries.

Use `速读论文` or paper-reading workflows when the user wants a structured high-level interpretation rather than a full translation.

## LaTeX workflows

LaTeX plugins handle proofreading, polishing, translation, and compiled diff/highlight outputs. Verify `pdflatex` and `latexdiff` before promising rebuilt PDFs. If the user only needs text-level feedback, a compiled PDF may be optional.

Always ask before modifying a LaTeX project in place. Prefer operating on a copy or uploaded archive.

## Word, Markdown, and batch files

- Use Word summary for `.docx`; legacy `.doc` may need conversion, especially outside Windows.
- Use Markdown translation when preserving Markdown structure matters.
- Use batch file query for folders/zips and mixed supported files. Confirm total size and supported suffixes before ingestion.

## Academic search and discovery

Google Scholar assistant and academic conversation plugins are network/model-backed. They are useful for paper discovery and recent-work search, but brittle when pages block scraping. Fall back to user-provided URLs, titles, or Arxiv IDs when search fails.
