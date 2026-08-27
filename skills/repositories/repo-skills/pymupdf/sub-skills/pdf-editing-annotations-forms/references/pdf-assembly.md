# PDF Assembly and Save Semantics

Use `Document.insert_pdf(src, from_page=..., to_page=..., start_at=..., links=True, annots=True, widgets=True, join_duplicates=False, final=1)` to copy page ranges from another PDF. Use `insert_file()` or `convert_to_pdf()` when supported non-PDF inputs must become PDF pages first.

TOC page numbers are 1-based and often must be rebuilt for merged outputs. Use full saves with `garbage=3`/`4` and `deflate=True` for optimized transformed outputs. Reacquire page/child objects after page-tree edits.
