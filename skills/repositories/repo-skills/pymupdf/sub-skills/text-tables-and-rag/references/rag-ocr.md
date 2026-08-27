# RAG and OCR

For simple RAG, combine sorted text, page numbers, and `Table.to_markdown()` for tables. Use optional PyMuPDF4LLM when you need integrated document-level Markdown, chunks, richer layout/table/image handling, header/footer controls, or OCR-aware conversion. Guard `import pymupdf4llm`.

OCR requires Tesseract and language data. Use `Page.get_textpage_ocr(language="eng", dpi=...)` only after verifying the external binary/tessdata. OCR is a fallback for image-only/scanned pages; it is not proof that native text extraction failed unless you inspect text/words/dict output first.
