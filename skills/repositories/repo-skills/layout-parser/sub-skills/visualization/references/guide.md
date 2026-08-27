# Visualization Guide

This guide covers the page overlay helpers that turn layouts into readable
images.

## Main APIs

| Symbol | Purpose | Important parameters |
| --- | --- | --- |
| `draw_box(canvas, layout, ...)` | Draw layout boxes and optional ids/types | `box_width`, `box_alpha`, `box_color`, `color_map`, `show_element_id`, `show_element_type` |
| `draw_text(canvas, layout, ...)` | Render text next to or around the page canvas | `arrangement`, `font_size`, `font_path`, `text_color`, `text_background_color`, `text_background_alpha`, `vertical_text`, `with_box_on_text`, `with_layout` |

## Canvas rules

- Input can be a PIL image or a NumPy array.
- Non-RGB PIL images are converted to RGB before drawing.
- `draw_text()` can expand the canvas left/right or up/down depending on
  `arrangement`.
- The bundled font is used when no custom font path is given.

## Drawing boxes

- `box_width` and `box_alpha` can be a scalar or one value per block.
- If `box_color` is omitted, `color_map` and then a default palette are used.
- `TextBlock` color handling uses the block's `type` when present.
- `draw_box()` can show ids and types in the upper-left corner of each box.

## Drawing text

- `draw_text()` places text based on each element's coordinates.
- `with_box_on_text=True` adds a box behind each text region on the text canvas.
- `vertical_text=True` switches to the vertical text layout helper.
- `with_layout=True` first draws the layout overlay, then adds the text canvas.

## Typical workflows

### 1) Visualize detected boxes

1. Load or detect a `Layout`.
2. Choose a color map if category-specific colors matter.
3. Call `draw_box()` on the image.
4. If you need region ids or types, enable the corresponding flags.

### 2) Visualize OCR text

1. Build a text-bearing `Layout` from OCR results.
2. Call `draw_text()` with or without a background box.
3. If the page should still show the detected layout, set `with_layout=True`.
4. Use `arrangement='lr'` or `'ud'` depending on the available space.

## Troubleshooting

- `ValueError` about list lengths means `box_width`, `box_alpha`, `box_color`,
  or the corresponding text arguments do not match the layout length.
- Alpha values must be within `[0, 1]`.
- If labels look wrong, confirm the font path or fall back to the bundled font.
- LayoutParser 0.3.4 uses `FreeTypeFont.getsize()` when drawing ids/types.
  Newer Pillow releases can remove this method and raise
  `AttributeError: 'FreeTypeFont' object has no attribute 'getsize'` when
  `show_element_id=True` or `show_element_type=True`. Use a compatible Pillow
  build for that path, avoid id/type labels, or patch the call to use Pillow's
  current text-bounding-box API in a maintained fork.
- If the canvas is an array, it will be converted to a PIL image internally.
- If a text block is empty, `draw_text()` simply skips it.

## Read next

- `../layout-objects/references/guide.md` for block preparation before drawing
- `../ocr/references/guide.md` for OCR layouts that feed the drawing layer
- `../../../references/troubleshooting.md` for font and alpha validation issues
