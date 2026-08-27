# Conversion Reference

## Label vocabulary and ids

Example converters use this convention:

```text
__ignore__     -> -1 (written as 255 in uint8 label PNGs)
_background_   -> 0
first class    -> 1
second class   -> 2
```

The labels file should list `__ignore__` first and `_background_` second. Do not
silently reorder labels after a model or evaluation pipeline has been trained.

## Shape support

| Output | Shape behavior |
| --- | --- |
| Single-file label PNG | Polygon, rectangle, circle, line, linestrip, point, points, oriented rectangle; Mask Shapes are placed from bbox-local patches. |
| VOC segmentation | All rasterizable Shapes; `group_id` controls instance ids when object output is enabled. |
| VOC bbox | Rectangle Shapes only; non-rectangles are skipped. |
| COCO | Polygon/rectangle/circle geometry becomes polygon segmentation; masks are rasterized to canvas for area/bbox; `(label, group_id)` forms an instance. |

## Generated layouts

VOC segmentation:

```text
voc_dataset/
  JPEGImages/
  SegmentationClass/
  SegmentationClassNpy/                 # unless --nonpy
  SegmentationClassVisualization/       # unless --noviz
  SegmentationObject/                   # unless --noobject
  SegmentationObjectNpy/                # unless --noobject/--nonpy
  SegmentationObjectVisualization/      # unless --noobject/--noviz
  class_names.txt
```

VOC bbox:

```text
bbox_voc/
  JPEGImages/
  Annotations/
  AnnotationsVisualization/             # unless --noviz
  class_names.txt
```

COCO:

```text
coco_dataset/
  JPEGImages/
  Visualization/                         # unless --noviz
  annotations.json
```

## Optional dependencies

- Single-file export needs NumPy and Pillow for `img.png`, raw `label.png`, and
  `label_names.txt`; `imgviz` is needed for source-style `lblsave` output and
  `label_viz.png`. Without `imgviz`, the bundled helper writes a raw label PNG
  and warns.
- VOC segmentation export needs `imgviz` in addition to NumPy and Pillow.
- VOC bbox export needs `imgviz` and `lxml`.
- COCO export needs `imgviz` and `pycocotools`; some platforms may need a
  compatible wheel or compiler.
- None of these converters needs Qt or a display unless a separate visualization
  viewer is used; the bundled scripts write images headlessly.
