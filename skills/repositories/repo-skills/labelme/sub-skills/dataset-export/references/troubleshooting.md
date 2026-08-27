# Dataset Export Troubleshooting

## Output directory already exists

The VOC and COCO directory exporters refuse to overwrite an existing directory,
matching the source examples' data-safety behavior. Choose a new directory or
remove the old one after confirming it is disposable. The single-file
`export_labelme_json.py` helper follows `examples/tutorial/export_json.py` and
can reuse its output directory, overwriting its standard artifact filenames.

## `shape labels not in the provided labels`

A Shape Label is missing from the labels file or comma list. Add the label to the
vocabulary in the desired class-id position. Do not let a converter invent class
ids after training data has already been consumed.

## `__ignore__` / `_background_` assertion or validation failure

VOC/COCO workflows expect `__ignore__` first and `_background_` second for the
example id convention. Fix the labels file rather than swapping ids in generated
outputs.

## Bbox export skips shapes

VOC detection XML supports rectangles in these helpers. Polygon, circle, mask,
line, and point Shapes are skipped. If the task is segmentation, use the VOC
segmentation or COCO route instead.

## COCO export needs `imgviz` and `pycocotools`

Install only when this format is required:

```bash
python -m pip install imgviz pycocotools
```

If `pycocotools` installation fails, use VOC export or a platform with a working
wheel/compiler. Do not mark COCO conversion verified until the optional
dependencies import and a tiny conversion succeeds.

## Label PNG looks all black

Low class ids can render as nearly black in ordinary image viewers. Inspect with
`inspect_label_png.py` or create a visualization JPEG rather than assuming the
mask is empty.

## Out-of-bounds annotation coordinates

labelme can preserve negative or beyond-image coordinates when that Setting is
enabled. Export rasterization clips to the image canvas; pixels outside the
Image do not exist in the output label arrays.
