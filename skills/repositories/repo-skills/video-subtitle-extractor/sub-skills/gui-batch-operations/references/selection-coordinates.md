# Selection Coordinates

The GUI stores preview selections as normalized ratios in `ymin,ymax,xmin,xmax`
order. Values are relative to the displayed preview after accounting for video
scaling and black bars. Before extraction, VSE converts selections to source
video pixel coordinates.

## Default saved selection

The default config value is approximately:

```text
0.78,0.99,0.05,0.95
```

That means a bottom subtitle band spanning most of the width.

## Pixel conversion concept

Given preview rectangle ratios, video frame size, preview size, and black-bar
fractions, VSE adjusts the rectangle by black bars, scales it to frame width and
height, rounds, clamps, and normalizes coordinate order.

Use the bundled helper:

```bash
python sub-skills/gui-batch-operations/scripts/selection_coordinate_helper.py \
  --frame-width 1920 --frame-height 1080 --preview-width 960 --preview-height 540 \
  --rect 0.78 0.99 0.05 0.95
```

The helper prints `ymin ymax xmin xmax` for the source CLI prompt.
