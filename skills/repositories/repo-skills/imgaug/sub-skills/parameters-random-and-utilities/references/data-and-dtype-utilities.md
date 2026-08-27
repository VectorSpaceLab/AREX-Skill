# Data and dtype utilities

## Read this when

You need sample fixtures, resizing/grid helpers, display alternatives, or dtype/range conversion guidance.

## Verified utility signatures

- `imgaug.data.quokka(size=None, extract=None)`
- `imgaug.data.quokka_square(size=None)`
- `imgaug.data.quokka_heatmap(size=None, extract=None)`
- `imgaug.data.quokka_segmentation_map(size=None, extract=None)`
- `imgaug.data.quokka_keypoints(size=None, extract=None)`
- `imgaug.data.quokka_bounding_boxes(size=None, extract=None)`
- `imgaug.data.quokka_polygons(size=None, extract=None)`
- `imgaug.dtypes.change_dtype_(arr, dtype, clip=True, round=True)`
- `imgaug.imresize_single_image(image, sizes, interpolation=None)`
- `imgaug.draw_grid(images, rows=None, cols=None)`
- `imgaug.imshow(image, backend='matplotlib')`

## Sample data

The `imgaug.data` module bundles small quokka fixtures that are useful for smokes and examples:

```python
import imgaug as ia

image = ia.data.quokka_square(size=(64, 64))
heatmap = ia.data.quokka_heatmap(size=(64, 64))
segmap = ia.data.quokka_segmentation_map(size=(64, 64))
keypoints = ia.data.quokka_keypoints(size=(64, 64))
boxes = ia.data.quokka_bounding_boxes(size=(64, 64))
polygons = ia.data.quokka_polygons(size=(64, 64))
```

These fixtures are package data; they do not require the source repository checkout.

## Dtype guidance

- Common image augmentation examples expect `uint8` arrays with values `0..255`.
- Dtype helpers clip and round by default when converting to integer/bool types.
- Use `change_dtype_(arr, dtype, clip=True, round=True)` deliberately; set `clip=False` or `round=False` only when the workflow has already validated ranges.
- Some geometric/dtype code paths intentionally reject or special-case `uint64`, `int64`, `float128`, and bool arrays.

## Display and grids

- `draw_grid(images, rows=None, cols=None)` returns an array suitable for saving or display.
- `imshow(image, backend='matplotlib')` is convenient locally but not safe to assume on headless servers.
- For CI or agents, write grids to files with `imageio.imwrite` instead of opening a GUI.

## Tiny fixture validation

Use the bundled script in this sub-skill to prove sample data and dtype conversions work without opening a GUI:

```bash
python sub-skills/parameters-random-and-utilities/scripts/smoke_parameters_and_data.py
```
