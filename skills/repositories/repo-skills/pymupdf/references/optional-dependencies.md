# Optional Dependencies and Capability Boundaries

PyMuPDF's base wheel covers the core `pymupdf` APIs for opening supported documents, extracting text/tables/images, rendering pages, and editing PDFs. The components below are optional and must be verified in the active runtime before a workflow claims them.

| Component | Enables | Verify before use | Boundary |
| --- | --- | --- | --- |
| Tesseract OCR binary plus language data | `Page.get_textpage_ocr()`, Pixmap OCR PDF helpers | `tesseract --version`, language data, and a small OCR `TextPage` probe | External program, not part of the base wheel. |
| PyMuPDF4LLM (`pymupdf4llm`) | RAG-oriented `to_markdown`, `to_json`, `to_text`, page chunks | `python -c "import pymupdf4llm"` plus a tiny conversion | Separate package; guard imports. |
| PyMuPDF Pro (`pymupdf.pro`) | Office/Hangul formats such as DOCX/XLSX/PPTX/HWP | Verify package import and license/unlock flow | Separate package/license; core PyMuPDF does not imply Office support. |
| Pillow | `Pixmap.pil_save()` and `Pixmap.pil_tobytes()` | `python -c "import PIL"` | Direct `Pixmap.save()`/`tobytes()` work for common image output without Pillow. |
| fontTools / `pymupdf-fonts` | Font subsetting and additional fonts | Import the package or run the specific font workflow | Optional for ordinary extraction/rendering. |
| pandas / tabulate | `Table.to_pandas()` and DataFrame Markdown | `python -c "import pandas, tabulate"` | `Table.extract()` and PyMuPDF `Table.to_markdown()` do not require pandas. |
| pytest/dev/build tooling | Maintainer tests/source builds | Install only for focused maintainer verification | Not needed for ordinary package use. |

Use published wheels whenever possible. Source builds can require a C/C++ toolchain, MuPDF source download/build, platform-specific compilers, and environment variables such as `PYMUPDF_SETUP_MUPDF_BUILD`. Do not run source-build, sudo, Docker, release, or system-install workflows implicitly.
