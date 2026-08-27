# Image Preprocessing Workflows

Use these recipes to prepare pathology images and WSIs before model inference. They are intentionally self-contained and describe TIAToolbox patterns without depending on source checkout files.

## Tissue Masks

### Array or Thumbnail Mask

Use `OtsuTissueMasker` for a fast foreground/background split and `MorphologicalMasker` when the mask needs connected-region cleanup or dilation.

```python
import numpy as np
from tiatoolbox.tools.tissuemask import MorphologicalMasker, OtsuTissueMasker

thumbnail = np.asarray(thumbnail_rgb, dtype=np.uint8)
batch = thumbnail[np.newaxis, ...]

mask = OtsuTissueMasker().fit_transform(batch)[0]
clean_mask = MorphologicalMasker(kernel_size=5, min_region_size=30).fit_transform(batch)[0]
```

Guidance:

- Maskers expect batch shape `(N, height, width, channels)`; add `np.newaxis` for one thumbnail.
- `OtsuTissueMasker` is best for high-contrast thumbnails or quick checks.
- `MorphologicalMasker` accepts only one of `mpp`, `power`, or `kernel_size`.
- Use `kernel_size` when the input array scale is already known; use `mpp` or `power` when the thumbnail scale came from a WSI reader.
- Increase `min_region_size` to remove small speckles; decrease it if small tissue fragments disappear.

### WSI-Derived Mask

When the task starts with a WSI path or reader, route opening, metadata, dimensions, and thumbnail bounds to `wsi-io`. Once a thumbnail is available, mask it as above. For automatic patch filtering, pass `input_mask="otsu"` or `input_mask="morphological"` to `SlidingWindowPatchExtractor`; TIAToolbox will generate a low-resolution tissue mask for non-virtual WSI inputs.

```python
from tiatoolbox.tools.patchextraction import SlidingWindowPatchExtractor

extractor = SlidingWindowPatchExtractor(
    input_img=wsi_or_path,
    patch_size=(512, 512),
    stride=(512, 512),
    input_mask="otsu",
    min_mask_ratio=0.5,
    resolution=0,
    units="level",
)
```

Use `references/troubleshooting.md` if this produces zero patches; the most common causes are a mask/image coordinate mismatch or a `min_mask_ratio` that is too strict.

### CLI Masking

The `tissue-mask` CLI generates masks for image or WSI inputs and supports Otsu or morphological behavior, output save/show modes, resolution units, and optional kernel size. Keep exact option spelling, shared file discovery, logging, and command orchestration in `cli-and-configuration`; use this sub-skill for method choice and parameter interpretation.

## Stain Normalization, Extraction, and Augmentation

### Choose a Normalizer

Use `get_normalizer(method_name, stain_matrix=None)` for routine stain normalization. Always call `fit(target_image)` before `transform(source_image)`.

```python
from tiatoolbox.tools.stainnorm import get_normalizer

normalizer = get_normalizer("reinhard")
normalizer.fit(target_image)
normalized = normalizer.transform(source_image)
```

Decision guide:

- `reinhard`: fast LAB color transfer; a good default for small checks or broad color harmonization.
- `ruifrok`: fixed H&E deconvolution matrix; useful when deterministic fixed stain vectors are desired.
- `macenko`: estimates stain vectors from tissue; common H&E normalization choice but needs enough tissue pixels.
- `vahadane`: dictionary-learning stain separation; useful for H&E normalization but slower and more dependency-sensitive.
- `custom`: use when the user supplies a trusted `(2, 3)` or `(3, 3)` stain matrix.

### Custom Matrix Plus Target Image

When a user provides both a custom stain matrix file and a target image, use `custom` only for the matrix and still fit the normalizer on the target image before transforming sources.

```python
from tiatoolbox.tools.stainnorm import get_normalizer
from tiatoolbox.utils import imread

normalizer = get_normalizer("custom", stain_matrix="stain_matrix.csv")
normalizer.fit(imread("target.png"))
normalized = normalizer.transform(imread("source.png"))
```

Validation checklist:

- Matrix files must be numeric `.npy` or headerless `.csv` data.
- Matrix shape must be `(2, 3)` or `(3, 3)`.
- Do not pass `stain_matrix` to `reinhard`, `ruifrok`, `macenko`, or `vahadane`.
- Do not skip the target image; the CLI and API normalizers need target stain information from `fit`.

### Extract Stain Matrices

Use extractors when the next step needs stain vectors rather than a normalized image:

```python
from tiatoolbox.tools.stainextract import MacenkoExtractor, RuifrokExtractor, VahadaneExtractor

matrix = MacenkoExtractor().get_stain_matrix(source_image)
fixed = RuifrokExtractor().get_stain_matrix(source_image)
learned = VahadaneExtractor().get_stain_matrix(source_image)
```

Macenko and Vahadane are tissue-content sensitive; blank patches, tiny images, or mostly background inputs can fail or produce unstable matrices. Prefer a representative target image or a pre-extracted matrix for production pipelines.

### Stain Augmentation

Use `StainAugmentor` for on-the-fly stain variation. Provide a `stain_matrix` when available to avoid extracting it for every image.

```python
from tiatoolbox.tools.stainaugment import StainAugmentor

augmentor = StainAugmentor(
    method="macenko",
    stain_matrix=target_stain_matrix,
    sigma1=0.25,
    sigma2=0.10,
    augment_background=False,
)
augmentor.fit(source_image)
augmented = augmentor.augment()
```

Guidance:

- `method` must be `"macenko"` or `"vahadane"`.
- `sigma1` scales stain concentrations; `sigma2` shifts them.
- Keep `augment_background=False` unless background color variation is intentional.
- In Albumentations pipelines, `apply` fits and augments one image.

### CLI Stain Normalization

The `stain-norm` CLI normalizes source images to a target image and supports `reinhard`, `custom`, `ruifrok`, `macenko`, and `vahadane`. It accepts an optional custom matrix only for `custom`. Route exact command syntax, file globbing, and shared CLI behavior to `cli-and-configuration`.

## Patch Extraction

### Sliding Windows Over Arrays or WSIs

Use `SlidingWindowPatchExtractor` for fixed-grid tiling. `patch_size` and `stride` are `(width, height)`, while returned NumPy patch arrays are `(height, width, channels)`.

```python
from tiatoolbox.tools.patchextraction import SlidingWindowPatchExtractor

extractor = SlidingWindowPatchExtractor(
    input_img=image_or_wsi,
    patch_size=(256, 256),
    stride=(128, 128),
    input_mask=mask_or_reader_or_none,
    min_mask_ratio=0.25,
    within_bound=True,
)

patch_count = len(extractor)
first_patch = extractor[0] if patch_count else None
```

Guidance:

- `stride=None` defaults to `patch_size` and creates non-overlapping tiles.
- Smaller stride creates overlap; larger stride skips regions.
- `within_bound=True` skips border windows that exceed image limits.
- `within_bound=False` allows border patches and pads them according to `pad_mode` and `pad_constant_values`.
- `input_mask` can be an array, mask path, virtual WSI mask, annotation store, or automatic strings `"otsu"`/`"morphological"` for non-virtual WSI inputs.
- `min_mask_ratio` is a fraction from `0` to `1`; start low, inspect counts, then tighten.

### Point-Centered Patches

Use `PointsPatchExtractor` when locations are nuclei, cells, landmarks, or sampled centers.

```python
import numpy as np
from tiatoolbox.tools.patchextraction import PointsPatchExtractor

points = np.array([[128, 128], [256, 256]])
extractor = PointsPatchExtractor(
    input_img=image_or_wsi,
    locations_list=points,
    patch_size=(224, 224),
    resolution=0,
    units="level",
)
patches = [patch for patch in extractor]
```

Guidance:

- The supplied coordinate is treated as a center; internal top-left positions shift by half the patch size.
- Coordinates are interpreted in the requested `resolution` and `units`.
- Include a third column or class field when saving/grouping downstream patches by class.
- Route WSI coordinate-space interpretation and reader bounds to `wsi-io`.

### Debug Coordinates Without Reading Pixels

Use static helpers when patch counts look wrong or reading the slide would be expensive.

```python
from tiatoolbox.tools.patchextraction import PatchExtractor

coords = PatchExtractor.get_coordinates(
    image_shape=(1024, 768),
    patch_input_shape=(256, 256),
    stride_shape=(256, 256),
    input_within_bound=True,
)
```

`PatchExtractor.filter_coordinates(mask_reader, coordinates_list, wsi_shape, min_mask_ratio=...)` checks candidate boxes against a mask reader. Make sure `wsi_shape` describes the same requested resolution as the coordinates; otherwise the internal rescaling can filter out every patch.

## Tile Pyramids

Use pyramid helpers when preprocessing creates tiles for viewing or downstream streaming rather than model inference.

```python
from tiatoolbox.tools.pyramid import TilePyramidGenerator, ZoomifyGenerator

pyramid = ZoomifyGenerator(wsi_reader, tile_size=256, downsample=2, overlap=0)
levels = pyramid.level_count
grid = pyramid.tile_grid_size(level=0)
tile = pyramid.get_tile(level=0, x=0, y=0)
path = pyramid.tile_path(level=0, x=0, y=0)
```

Guidance:

- `TilePyramidGenerator` expects a WSI-like reader with `read_rect` and slide dimensions in `info`.
- Generated pyramid level `0` is the lowest-resolution tile level; WSI reader level `0` is baseline/max-resolution.
- `ZoomifyGenerator.tile_path(...)` returns Zoomify-style paths such as `TileGroup0/0-0-0.jpg`.
- `dump(...)` writes many files; confirm output location and container options before running it.
- Use `AnnotationTileGenerator` to render annotation tiles from an annotation store and slide metadata.

## Preprocessing-to-Inference Validation

Before handing patches to `model-inference`, run a cheap validation pass:

1. Confirm the reader/image dimensions and coordinate units with `wsi-io`.
2. Generate or load the tissue mask at a known scale.
3. Compute candidate coordinates with the intended `patch_size`, `stride`, `resolution`, and `units`.
4. Filter with a conservative `min_mask_ratio`, then log `len(extractor)` and sample a few patch shapes.
5. Fit stain normalizers on representative target images, not on blank background or single tiny patches.
6. Check that normalized/augmented outputs remain `uint8`, RGB, and plausible in color range.
7. Send only validated image arrays, patch iterators, or saved patch sets to `model-inference`.

A minimal preflight for a patch iterator is:

```python
patch_count = len(extractor)
if patch_count == 0:
    raise ValueError("No patches selected; inspect mask alignment and min_mask_ratio")

sample = extractor[0]
if sample.ndim != 3 or sample.shape[-1] != 3:
    raise ValueError(f"Expected RGB patch, got shape {sample.shape}")
```
