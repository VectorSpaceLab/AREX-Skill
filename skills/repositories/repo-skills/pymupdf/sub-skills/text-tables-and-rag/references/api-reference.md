# Text/Table API Reference

```python
Page.get_text(option="text", clip=None, flags=None, textpage=None, sort=False, delimiters=None)
Page.get_textpage(clip=None, flags=3)
Page.search_for(needle, *, clip=None, quads=False, flags=None, textpage=None)
Page.find_tables(clip=None, strategy=None, vertical_strategy=None, horizontal_strategy=None, add_lines=None, add_boxes=None, paths=None, use_layout=True, ...)
Page.get_textpage_ocr(flags=3, language="eng", dpi=72, full=False, tessdata=None)
```

Use `pymupdf.recover_quad()` and `recover_line_quad()` for span/line quads from dict extraction. Table objects provide `extract()`, `to_markdown()`, `to_pandas()`, `header`, `rows`, `cells`, and `bbox`.
