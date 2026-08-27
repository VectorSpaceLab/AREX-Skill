# Open, Save, Convert, and Authenticate Workflows

Open a file with `pymupdf.open(path)`. Open bytes with `pymupdf.open(stream=data, filetype="pdf")`. Use explicit `filetype="txt"` for plain text or ambiguous text-like streams. Use `with pymupdf.open(...) as doc:` when handles matter.

For passwords: check `doc.needs_pass`; call `doc.authenticate(password)` and treat return code `0` as failure. For saving, prefer full save to a new output path with options such as `garbage=3` and `deflate=True`. Use incremental save only when appending to the same PDF is intentional and `doc.can_save_incrementally()` passes.

For conversion: open a supported input, call `doc.convert_to_pdf()`, then reopen with `pymupdf.open(stream=pdf_bytes, filetype="pdf")` if you need PDF-only APIs. Office formats require PyMuPDF Pro.
