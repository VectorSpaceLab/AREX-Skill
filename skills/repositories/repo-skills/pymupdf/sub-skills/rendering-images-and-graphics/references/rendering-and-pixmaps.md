# Rendering and Pixmaps

Use `page.get_pixmap(dpi=150, clip=rect, annots=False, alpha=False)` for ordinary previews. `dpi` is easier than `matrix` and preserves DPI metadata; use `matrix` for zoom/rotate/shear/mirror transforms. `colorspace` can be RGB, gray, or CMYK. Keep `alpha=False` unless transparency is required.

Use `DisplayList` when repeatedly rendering the same page. Use `Pixmap.save(path)` or `Pixmap.tobytes(format)` for output. Pillow is needed only for `pil_*` helpers.
