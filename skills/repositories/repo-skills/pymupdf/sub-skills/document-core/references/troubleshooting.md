# Document-Core Troubleshooting

- Empty or unknown file: catch `FileNotFoundError`, `EmptyFileError`, `FileDataError`, `ValueError`, and `TypeError`.
- Wrong extension: pass `filetype` for ambiguous text/source/XML/JSON streams.
- Password failure: `authenticate()` returns `0`; do not proceed as if authenticated.
- Incremental save failure: incremental save must target the original file and is incompatible with cleanup, linearization, many encryption changes, and repaired files.
- Orphaned object: reacquire pages, annotations, widgets, links, tables, and textpages after close/reopen or page-tree edits.
- Office support: verify PyMuPDF Pro; core PyMuPDF does not imply DOCX/XLSX/PPTX support.
