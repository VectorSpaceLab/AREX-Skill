# Rendering/Image API Reference

```python
Page.get_pixmap(matrix=pymupdf.Identity, dpi=None, colorspace=None, clip=None, alpha=False, annots=True)
Pixmap.save(filename, output=None, jpg_quality=95)
Pixmap.tobytes(output="png", jpg_quality=95)
Page.get_images(full=False)
Document.extract_image(xref)
Page.get_image_info(hashes=False, xrefs=False)
Page.insert_image(rect, filename=None, stream=None, pixmap=None, xref=0, rotate=0, keep_proportion=True, overlay=True)
Page.get_drawings(extended=False)
Page.get_svg_image(matrix=pymupdf.Identity, text_as_path=True)
Page.draw_rect(rect, color=(0,), fill=None, width=1, ...)
Page.insert_htmlbox(rect, text, css=None, ...)
```
