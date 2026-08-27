# Annotations and Redaction

Use `Page.search_for(..., quads=True)` to locate text robustly. Marker annotations highlight/underline/squiggle/strike text but do not remove content. Permanent redaction requires `Page.add_redact_annot(rect_or_quad, ...)`, `Page.apply_redactions()`, a full save with garbage collection, and reopen/search validation.

After annotation updates, reload the page before rendering or reaccessing changed annotation objects.
