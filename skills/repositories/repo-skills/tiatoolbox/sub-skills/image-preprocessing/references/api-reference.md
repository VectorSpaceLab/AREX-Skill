# Image Preprocessing API Reference

This reference covers TIAToolbox preprocessing APIs that operate before model inference. Keep WSI reading, metadata, and coordinate-space internals with `wsi-io`; keep predictor and segmentation engines with `model-inference`.

## Tissue Masking

### Shared Contract

`TissueMasker` is the abstract base class. Concrete maskers follow a scikit-learn-like pattern:

```python
masker.fit(images)
masks = masker.transform(images)
# or
masks = masker.fit_transform(images)
```

`images` must be shaped as a batch, usually `(N, height, width, channels)`. RGB `uint8` arrays are the common input. Outputs are boolean-like masks shaped `(N, height, width)`.

### `OtsuTissueMasker()`

Use this when a fast global threshold is enough.

- Fits a grayscale threshold across all pixels in the batch.
- Requires `fit` before `transform`; calling `transform` first raises an error.
- Works well for thumbnails or small regions where tissue/background contrast is clear.
- Can be used indirectly by passing `input_mask="otsu"` to sliding-window patch extraction for non-virtual WSI inputs.

### `MorphologicalMasker(mpp=None, power=None, kernel_size=None, min_region_size=None)`

Use this when a threshold needs cleanup by small-region removal and dilation.

- Accepts only one of `mpp`, `power`, or `kernel_size`.
- If `mpp` is given, kernel scale is derived from microns-per-pixel.
- If `power` is given, objective power is converted to mpp first.
- If `kernel_size` is given, it controls the elliptical morphology kernel directly.
- If none of `mpp`, `power`, and `kernel_size` is set, the kernel defaults to a minimal size.
- `min_region_size` removes connected tissue regions smaller than the chosen pixel area; if omitted, it defaults around the kernel area.
- Can be used indirectly by passing `input_mask="morphological"` to sliding-window patch extraction for non-virtual WSI inputs.

Decision rule: prefer `kernel_size` for array-level experiments or when the thumbnail scale is already fixed; prefer `mpp` or `power` when deriving a mask from a WSI thumbnail with known physical scale.

## Stain Normalization

### `get_normalizer(method_name, stain_matrix=None)`

Factory for stain normalizers. `method_name` is case-insensitive and must be one of:

- `"reinhard"`: LAB color transfer; fast and often stable on tiny or low-texture images.
- `"ruifrok"`: fixed H&E color deconvolution matrix.
- `"macenko"`: estimates H&E stain vectors from tissue pixels.
- `"vahadane"`: dictionary-learning-based stain separation; can be slower and more sensitive to package versions and tissue content.
- `"custom"`: uses a user-provided stain matrix.

Typical call:

```python
from tiatoolbox.tools.stainnorm import get_normalizer

normalizer = get_normalizer("reinhard")
normalizer.fit(target_image)
result = normalizer.transform(source_image)
```

`target_image` and `source_image` should be RGB `uint8` arrays. Always call `fit(target_image)` before `transform(source_image)`.

### Custom Stain Matrices

For `method_name="custom"`, pass `stain_matrix` as a NumPy array or a path to a `.npy` or headerless `.csv` file. The loaded matrix must have shape `(2, 3)` or `(3, 3)`.

```python
import numpy as np
from tiatoolbox.tools.stainnorm import get_normalizer

stain_matrix = np.array([
    [0.65, 0.70, 0.29],
    [0.07, 0.99, 0.11],
])
normalizer = get_normalizer("custom", stain_matrix=stain_matrix)
normalizer.fit(target_image)
normalized = normalizer.transform(source_image)
```

Do not pass `stain_matrix` with non-custom methods; TIAToolbox rejects that combination. Do not use a CSV with column headers; the matrix loader expects numeric values only.

## Stain Extraction

Use stain extractors when a workflow needs stain matrices rather than fully normalized images.

- `CustomExtractor(stain_matrix)` returns the supplied `(2, 3)` or `(3, 3)` matrix.
- `RuifrokExtractor()` returns a fixed H&E matrix.
- `MacenkoExtractor(luminosity_threshold=0.8, angular_percentile=99)` estimates stain vectors from optical density values over tissue pixels.
- `VahadaneExtractor(luminosity_threshold=0.8, regularizer=...)` estimates stain vectors with dictionary learning.

All expose `get_stain_matrix(img)`. Inputs should be RGB `uint8` arrays. Macenko and Vahadane need enough non-background tissue pixels; blank or tiny images may fail or produce unstable vectors.

## Stain Augmentation

`StainAugmentor(method="vahadane", stain_matrix=None, sigma1=0.4, sigma2=0.2, p=0.5, augment_background=False, always_apply=False)` can run standalone or inside an Albumentations pipeline.

- `method` must be `"vahadane"` or `"macenko"`.
- `stain_matrix` is optional; provide it to avoid extracting the matrix every time.
- `sigma1` scales stain concentrations using values sampled from `[1 - sigma1, 1 + sigma1]`.
- `sigma2` shifts stain concentrations using values sampled from `[-sigma2, sigma2]`.
- `augment_background=False` restricts augmentation to tissue-like pixels based on a luminosity mask.
- Standalone usage is `augmentor.fit(image)` followed by repeated `augmentor.augment()` calls.
- Albumentations usage calls `apply`, which fits and augments one image.

```python
from tiatoolbox.tools.stainaugment import StainAugmentor

augmentor = StainAugmentor(method="macenko", sigma1=0.25, sigma2=0.1)
augmentor.fit(source_image)
augmented_image = augmentor.augment()
```

## Patch Extraction

### Factory

`get_patch_extractor(method_name, **kwargs)` returns either `PointsPatchExtractor` or `SlidingWindowPatchExtractor`.

- `method_name="point"`: extracts centered patches around supplied locations.
- `method_name="slidingwindow"`: tiles an image or WSI on a grid.
- Unknown methods raise a method-not-supported error.

### Shared Patch Arguments

Common arguments:

- `input_img`: path, NumPy array, or `WSIReader`-like object.
- `patch_size`: int or `(width, height)` tuple; an int expands to a square patch.
- `resolution`: numeric resolution, default `0`.
- `units`: resolution units, default `"level"`; common WSI units include `"level"`, `"mpp"`, `"power"`, and `"baseline"` depending on reader support.
- `pad_mode`: NumPy-style padding mode, default `"constant"`.
- `pad_constant_values`: value for constant padding, default `0`.
- `within_bound`: if `False`, border patches may be padded; if `True`, patches whose requested bounds exceed image limits are skipped.

Patch shapes are specified as `(width, height)`, while NumPy arrays report shape as `(height, width, channels)`. This is the most common source of width/height confusion.

### `SlidingWindowPatchExtractor`

Constructor:

```python
SlidingWindowPatchExtractor(
    input_img,
    patch_size,
    input_mask=None,
    resolution=0,
    units="level",
    stride=None,
    pad_mode="constant",
    pad_constant_values=0,
    min_mask_ratio=0,
    store_filter=None,
    within_bound=False,
)
```

Behavior:

- If `stride=None`, stride defaults to `patch_size`.
- Smaller stride than patch size creates overlap.
- Larger stride skips space between candidate patches.
- `input_mask` may be a NumPy array, mask path, `VirtualWSIReader`, annotation store, or the strings `"otsu"` and `"morphological"` for automatic WSI masks.
- `min_mask_ratio` keeps only patches whose positive mask area exceeds the threshold; it must be between `0` and `1`.
- `store_filter` applies only when the mask is an annotation store.
- The extractor is iterable, indexable, and has `len(extractor)`.

### `PointsPatchExtractor`

Constructor:

```python
PointsPatchExtractor(
    input_img,
    locations_list,
    patch_size=(224, 224),
    resolution=0,
    units="level",
    pad_mode="constant",
    pad_constant_values=0,
    within_bound=False,
)
```

Behavior:

- `locations_list` may be a NumPy array, pandas DataFrame, or supported table path such as CSV/NPY/JSON.
- Coordinates are interpreted at the requested `resolution` and `units`, not automatically at baseline unless those are the requested units.
- The provided point is treated as a center; internal top-left coordinates are shifted by half the patch size.
- Include a third column or class label when downstream saving or grouping depends on class.

### Coordinate Helpers

`PatchExtractor.get_coordinates(...)` computes tiling coordinates without reading image pixels. Use it to debug grid size, stride, and boundary behavior.

Key inputs:

- `image_shape=(width, height)`.
- `patch_input_shape=(width, height)`.
- `stride_shape=(x_stride, y_stride)`.
- `input_within_bound=True` excludes patches whose read window crosses the image boundary.
- `output_within_bound=True` applies boundary checks to `patch_output_shape` when it is supplied.

`PatchExtractor.filter_coordinates(mask_reader, coordinates_list, wsi_shape, min_mask_ratio=0, func=None)` filters `[x_start, y_start, x_end, y_end]` coordinates against a `VirtualWSIReader` mask. It rescales coordinates to the mask array shape based on `wsi_shape`, so mismatched `wsi_shape`, mask resolution, or coordinate resolution can silently remove expected patches.

## Tile Pyramids

### `TilePyramidGenerator(wsi, tile_size=256, downsample=2, overlap=0)`

Generic pyramid helper for WSI-like readers that implement `read_rect` and expose slide dimensions in `info`.

Important methods and properties:

- `level_count`: number of generated tile levels, with level `0` as the lowest-resolution pyramid tile level.
- `level_downsample(level)`: downsample relative to baseline.
- `level_dimensions(level)`: dimensions for a generated tile level.
- `tile_grid_size(level)`: number of tiles in `(x, y)` at that generated level.
- `get_thumb_tile()`: returns a Pillow thumbnail image.
- `get_tile(level, x, y, res=1, pad_mode="constant", interpolation="optimise", transparent_value=None)`: returns a Pillow tile.
- `dump(path, container=None, compression=None)`: writes every tile to a directory, zip, or tar archive.

Levels in `TilePyramidGenerator` are reversed relative to `WSIReader` levels: generated level `0` is the lowest-resolution tile level, while WSI level `0` is the baseline/max-resolution level.

### `ZoomifyGenerator`

`ZoomifyGenerator` extends `TilePyramidGenerator` and implements Zoomify-style tile paths:

- `tile_group(level, x, y)` returns the Zoomify `TileGroup` index.
- `tile_path(level, x, y)` returns paths like `TileGroup0/0-0-0.jpg`.

### `AnnotationTileGenerator`

Use `AnnotationTileGenerator(info, store, renderer=None, tile_size=256, downsample=2, overlap=0)` to render annotation tiles from an annotation store. It does not read image pixels; it renders annotations using slide metadata, an annotation store, and an annotation renderer.

## Preprocessing CLIs

Two preprocessing command groups are provided by the `tiatoolbox` console entry point.

### `tissue-mask`

Generates a tissue mask for image or WSI inputs.

Conceptual options:

- input path or directory
- output path
- method, commonly Otsu or morphological
- resolution and units for thumbnailing, using `mpp` or `power`
- output mode, typically show or save
- optional morphological kernel size

Route exact command syntax and shared file-discovery flags to `cli-and-configuration`.

### `stain-norm`

Stain-normalizes source image files and writes outputs.

Conceptual options:

- source image or directory
- output path
- method: `reinhard`, `custom`, `ruifrok`, `macenko`, or `vahadane`
- target image path
- optional stain matrix for `custom`
- image file type glob

Route exact command syntax and shared CLI behavior to `cli-and-configuration`.
