---
name: rendering-images-and-graphics
description: "Render pages, work with Pixmaps/images, extract or insert embedded
  images, and handle vector graphics/layout helpers in PyMuPDF."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Rendering, Images, and Graphics

Use this sub-skill for visual workflows: page rasterization, Pixmap/image bytes, embedded image extraction or insertion, vector drawing inspection/replay, SVG output, and coordinate-aware graphics/layout helpers.

## Read or run

- [references/rendering-and-pixmaps.md](references/rendering-and-pixmaps.md) covers `Page.get_pixmap()`, DPI, Matrix, clip, alpha, annotations, colorspaces, and DisplayList.
- [references/images-and-xrefs.md](references/images-and-xrefs.md) covers original embedded images, xrefs, soft masks, `extract_image`, `Pixmap(doc,xref)`, and image blocks.
- [references/drawing-and-layout.md](references/drawing-and-layout.md) covers `get_drawings`, `get_svg_image`, `draw_*`, Shape, Story, and TextWriter.
- [references/troubleshooting.md](references/troubleshooting.md) covers visual-output failures.
- Run [scripts/render_page_preview.py](scripts/render_page_preview.py) or [scripts/draw_grid_sample.py](scripts/draw_grid_sample.py) for safe smokes.

## Default decisions

Use `Page.get_pixmap()` for screenshot-like page output. Use xref/image APIs when the user wants original embedded images. Use `dpi=` for ordinary resolution; use `matrix=` for transforms. Keep `alpha=False` and `annots=False` unless those appearances are explicitly needed.

