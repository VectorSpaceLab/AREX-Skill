# Text Extraction

Use `Page.get_text()` modes deliberately: `text` for plain text, `words` for word boxes, `blocks` for block boxes, `dict`/`rawdict` for spans/fonts/images/characters, and `html`/`xml`/`xhtml`/`json` variants for structured exports. Use `sort=True` for a top-left reading-order heuristic. Use `clip=pymupdf.Rect(...)` for region extraction.

For repeated work on the same page, build `tp = page.get_textpage(flags=...)` and pass `textpage=tp` to extraction/search; later `clip`/`flags` are ignored when a `TextPage` is supplied. `Page.search_for(needle, quads=True)` is preferred for rotated text. PyMuPDF search is not regex search.
