# Document Backend Matrix

| Backend/tool | Used for | Requirement | Notes |
| --- | --- | --- | --- |
| Traditional PDF extraction | fallback PDF translation/summary | base Python packages such as PyMuPDF | fastest, weakest for complex formulas/layout |
| GROBID | scholarly PDF structure extraction | public or private GROBID service | good for standard papers; public service can be slow or blocked |
| DOC2X | high-fidelity PDF parsing and layout | `DOC2X_API_KEY` and network | best layout/formula retention; optional credential service |
| NOUGAT | formula-heavy PDF-to-Markdown parsing | `nougat-ocr`, large Hugging Face model download, GPU recommended | optional heavy path; CPU possible but slow |
| LaTeX tools | rebuild translated/proofread PDFs and diff highlights | `pdflatex`, `latexdiff` on `PATH` | required only for compiled outputs |
| Word parsing | `.docx` summaries | `python-docx` | `.doc` is legacy; convert to `.docx` unless Windows/pywin32 path is available |
| LlamaIndex readers | batch file query and RAG-like document ingestion | LlamaIndex reader packages and embedding provider | embedding credentials may be separate from chat model credentials |
| Mathpix | OCR/formula parsing in some flows | Mathpix app id/key | optional service, not part of minimum scope |

Use root `scripts/check_doc_backends.py --repo-root <checkout>` for local import and executable checks. It does not call credentialed services or parse documents.
