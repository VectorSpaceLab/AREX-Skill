# Augmentables data formats

## Read this when

You need to construct or interpret imgaug annotation objects that move with image transforms.

## Verified constructors and methods

- `Keypoint(x, y)`
- `KeypointsOnImage(keypoints, shape)`
- `BoundingBox(x1, y1, x2, y2, label=None)`
- `BoundingBoxesOnImage(bounding_boxes, shape)`
- `Polygon(exterior, label=None)`
- `LineString(coords, label=None)`
- `HeatmapsOnImage(arr, shape, min_value=0.0, max_value=1.0)`
- `SegmentationMapsOnImage(arr, shape, nb_classes=None)`
- `Keypoint.project(from_shape, to_shape)`
- `KeypointsOnImage.on(image)`
- `KeypointsOnImage.draw_on_image(image, color=(0, 255, 0), alpha=1.0, size=3, copy=True, raise_if_out_of_image=False)`
- `BoundingBox.project(from_shape, to_shape)`
- `BoundingBoxesOnImage.on(image)`
- `BoundingBoxesOnImage.clip_out_of_image()`
- `Polygon.clip_out_of_image(image)`
- `LineString.clip_out_of_image(image)`
- `HeatmapsOnImage.resize(sizes, interpolation='cubic')`
- `SegmentationMapsOnImage.resize(sizes, interpolation='nearest')`

## Core rules

### Keypoints

Keypoints are subpixel-accurate `(x, y)` coordinates. A point at `x=0.5, y=0.5` denotes the center of the top-left pixel.

### Bounding boxes

Bounding boxes use `(x1, y1, x2, y2)`. Labels are optional and travel with the object.

### Polygons and line strings

Polygons are closed shapes with an exterior ring. Line strings are open sequences of coordinates. Both can be projected, clipped, and drawn on images.

### Heatmaps

Heatmaps represent continuous dense values, typically in `float32`, and may be smaller than the corresponding image.

### Segmentation maps

Segmentation maps represent categorical labels, typically in integer arrays. Spatial transforms should preserve class boundaries with nearest-neighbor semantics.

## Input layout hints

- `images` commonly has shape `(N, H, W, C)`.
- Annotation groups may be provided as Python lists with one group per image.
- `Batch`/`UnnormalizedBatch` are useful when the loader naturally emits flexible Python structures or mixed metadata.

## Validation checklist

- Images and annotation groups have matching counts.
- Dense maps know the target image shape.
- Annotations are clipped or removed intentionally when they move outside the image plane.
- Heatmaps and segmentation maps are not conflated during resize/warp operations.
