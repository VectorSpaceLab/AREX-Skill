# Drawing and Layout

Use `Page.get_drawings()` / `get_cdrawings()` to inspect vector paths, and `Page.get_svg_image()` for SVG output. For new graphics, use page convenience methods such as `draw_line`, `draw_rect`, `draw_circle`, or create a `Shape`, call drawing/text methods, `finish()`, then `commit()`.

Use `Page.insert_text`, `insert_textbox`, `insert_htmlbox`, `Story`, and `TextWriter` for visual text/layout. `insert_htmlbox` can use HTML/CSS and returns spare height/scale.
