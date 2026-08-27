# Forms, Links, Outlines, Embedded Files, and Optional Content

Create forms with `pymupdf.Widget`, `Page.add_widget()`, `page.widgets()`, and `Widget.update()`. Handle duplicate form field names deliberately when merging.

Links use dictionaries with link kinds such as URI, GoTo, named, launch, or remote. Use explicit schemes for URI links. TOC uses `get_toc()`/`set_toc()` and 1-based page numbers.

Document embedded files use `embfile_add`, `embfile_get`, `embfile_del`, `embfile_upd`, `embfile_names`, and `embfile_info`. Sanitize extracted filenames and use explicit output paths.
