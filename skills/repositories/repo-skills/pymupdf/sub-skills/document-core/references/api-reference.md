# Document-Core API Reference

Key facts: distribution `pymupdf`, public import `pymupdf`, deprecated compatibility import `fitz`, Requires-Python `>=3.10`, target version `1.28.2`.

Core signatures:

```python
pymupdf.open(filename=None, stream=None, filetype=None, rect=None, width=0, height=0, fontsize=11, archive=None)
Document.save(filename, garbage=0, clean=0, deflate=0, deflate_images=0, deflate_fonts=0, incremental=0, ascii=0, expand=0, linear=0, no_new_id=0, appearance=0, pretty=0, encryption=1, permissions=4095, owner_pw=None, user_pw=None, preserve_metadata=1, use_objstms=0, compression_effort=0, raise_on_repair=False, reproducible=False)
Document.convert_to_pdf(from_page=0, to_page=-1, rotate=0)
Document.get_toc(simple=True)
Document.set_toc(toc, collapse=1)
```

`Document` owns pages and PDF objects. `Page` and child objects become orphaned after closing the document or some page-tree edits. Geometry uses top-left page origin in points; use `Rect`, `Point`, `Matrix`, and `Quad` for clips, placement, transforms, and rotated text.
