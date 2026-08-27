# Transform recipes

These recipes are starting points for Albumentations 2.x transform selection. Adjust probabilities and magnitudes after visual inspection on real samples.

## Classification: geometry plus color

Use pixel-only transforms freely because labels do not need geometric updates.

```python
import cv2
import albumentations as A

train_aug = A.Compose([
    A.RandomResizedCrop(size=(224, 224), scale=(0.6, 1.0), ratio=(0.75, 1.3333333333), p=1.0),
    A.HorizontalFlip(p=0.5),
    A.RandomBrightnessContrast(brightness_limit=(-0.15, 0.15), contrast_limit=(-0.2, 0.2), p=0.5),
    A.HueSaturationValue(hue_shift_limit=(-8, 8), sat_shift_limit=(-15, 15), val_shift_limit=(-8, 8), p=0.3),
    A.GaussNoise(p=0.15),
    A.MotionBlur(blur_limit=(3, 5), p=0.1),
    A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225), max_pixel_value=255.0),
])
```

Checks:

- `size=(height, width)` is the Albumentations 2.x form for `RandomResizedCrop`.
- If adding tensor conversion, route to `../framework-integration/`.
- If using non-RGB or multispectral arrays, avoid RGB-specific transforms until verified.

## Segmentation-safe image and mask pipeline

Use spatial transforms that support masks and keep mask labels discrete.

```python
import cv2
import albumentations as A

seg_aug = A.Compose([
    A.PadIfNeeded(
        min_height=512,
        min_width=512,
        border_mode=cv2.BORDER_CONSTANT,
        fill=0,
        fill_mask=255,  # use your dataset's ignore index or background label
        p=1.0,
    ),
    A.RandomCrop(height=512, width=512, p=1.0),
    A.HorizontalFlip(p=0.5),
    A.Affine(
        scale=(0.9, 1.1),
        rotate=(-10, 10),
        translate_percent=(-0.05, 0.05),
        interpolation=cv2.INTER_LINEAR,
        mask_interpolation=cv2.INTER_NEAREST,
        border_mode=cv2.BORDER_CONSTANT,
        fill=0,
        fill_mask=255,
        p=0.5,
    ),
    A.RandomBrightnessContrast(p=0.3),  # image only; mask unchanged
])

out = seg_aug(image=image, mask=mask)
```

Checks:

- `mask_interpolation=cv2.INTER_NEAREST` prevents fractional class labels.
- `fill_mask` must be a class id or ignore value expected by the loss.
- Pixel transforms such as brightness/noise are safe because they do not modify masks.
- Avoid blur/downscale on masks; if a transform exposes `mask_interpolation`, set it explicitly.

## Detection or keypoint spatial augmentation

Coordinate formats and labels belong to `../targets-and-formats/`, but transform choice starts here.

```python
import cv2
import albumentations as A

spatial_aug = A.Compose(
    [
        A.LongestMaxSize(max_size=640, interpolation=cv2.INTER_LINEAR, p=1.0),
        A.PadIfNeeded(
            min_height=640,
            min_width=640,
            border_mode=cv2.BORDER_CONSTANT,
            fill=0,
            fill_mask=0,
            p=1.0,
        ),
        A.HorizontalFlip(p=0.5),
        A.Affine(
            scale=(0.8, 1.2),
            translate_percent=(-0.05, 0.05),
            rotate=(-5, 5),
            interpolation=cv2.INTER_LINEAR,
            mask_interpolation=cv2.INTER_NEAREST,
            fit_output=False,
            p=0.5,
        ),
    ],
    bbox_params=A.BboxParams(format="pascal_voc", label_fields=["labels"], clip=True, filter_invalid_bboxes=True),
)
```

Checks:

- Confirm bbox/keypoint format and label arrays in `../targets-and-formats/`.
- Prefer conservative rotation/perspective magnitudes for boxes and keypoints.
- Use `clip=True` and filtering intentionally; do not hide annotation bugs without review.

## Convert a v1-style dropout/crop pipeline to Albumentations 2.x

Old pattern:

```python
# v1-style names shown only for migration context
A.CoarseDropout(min_holes=2, max_holes=6, min_height=8, max_height=24, min_width=8, max_width=24, mask_value=255)
A.RandomResizedCrop(height=224, width=224, scale=(0.6, 1.0))
A.Rotate(value=0, mask_value=255)
```

Albumentations 2.x pattern:

```python
import cv2
import albumentations as A

aug = A.Compose([
    A.CoarseDropout(
        num_holes_range=(2, 6),
        hole_height_range=(8, 24),
        hole_width_range=(8, 24),
        fill=0,
        fill_mask=255,
        p=0.5,
    ),
    A.RandomResizedCrop(
        size=(224, 224),
        scale=(0.6, 1.0),
        ratio=(0.75, 1.3333333333),
        interpolation=cv2.INTER_LINEAR,
        mask_interpolation=cv2.INTER_NEAREST,
        p=1.0,
    ),
    A.Rotate(
        limit=(-15, 15),
        border_mode=cv2.BORDER_CONSTANT,
        fill=0,
        fill_mask=255,
        mask_interpolation=cv2.INTER_NEAREST,
        p=0.5,
    ),
])
```

Use `scripts/transform_probe.py migrate` to mechanically suggest common name replacements, then check the installed signature.

## Normalize for common model expectations

```python
imagenet_norm = A.Normalize(
    mean=(0.485, 0.456, 0.406),
    std=(0.229, 0.224, 0.225),
    max_pixel_value=255.0,
    normalization="standard",
)

yolo_like_norm = A.Normalize(
    mean=(0, 0, 0),
    std=(1, 1, 1),
    max_pixel_value=255.0,
    normalization="standard",
)

per_image_minmax = A.Normalize(normalization="min_max")
```

Checks:

- `standard` mode requires `mean`, `std`, and `max_pixel_value`.
- Other normalization modes ignore `mean`, `std`, and `max_pixel_value`.
- Place `Normalize` after image-space augmentations and before tensor conversion.

## Domain adaptation with metadata

Prefer per-call metadata over deprecated constructor `reference_images`.

```python
import albumentations as A

hist_aug = A.Compose([
    A.HistogramMatching(blend_ratio=(0.4, 0.8), metadata_key="hm_metadata", p=0.5),
])

out = hist_aug(image=image, hm_metadata=[reference_image_a, reference_image_b])
```

```python
pda_aug = A.Compose([
    A.PixelDistributionAdaptation(
        blend_ratio=(0.25, 0.75),
        transform_type="standard",  # also "pca" or "minmax"
        metadata_key="pda_metadata",
        p=0.5,
    ),
])

out = pda_aug(image=image, pda_metadata=[target_domain_image])
```

Checks:

- Metadata value must be a non-empty sequence of NumPy arrays.
- Use RGB-compatible reference arrays for RGB-style adaptation.
- Keep adaptation probabilities modest until visual inspection passes.

## Mosaic and overlay metadata

```python
import albumentations as A

mosaic_aug = A.Compose([
    A.Mosaic(
        grid_yx=(2, 2),
        target_size=(512, 512),
        cell_shape=(512, 512),
        center_range=(0.3, 0.7),
        fit_mode="cover",
        fill=0,
        fill_mask=0,
        metadata_key="mosaic_metadata",
        p=1.0,
    ),
])

out = mosaic_aug(
    image=base_image,
    mask=base_mask,
    mosaic_metadata=[
        {"image": image_1, "mask": mask_1},
        {"image": image_2, "mask": mask_2},
        {"image": image_3, "mask": mask_3},
    ],
)
```

```python
overlay_aug = A.Compose([A.OverlayElements(metadata_key="overlay_metadata", p=1.0)])

out = overlay_aug(
    image=image,
    mask=mask,
    overlay_metadata=[
        {"image": sticker_image, "mask": sticker_mask, "bbox": [0.1, 0.2, 0.4, 0.6], "mask_id": 3},
    ],
)
```

Checks:

- `Mosaic` needs enough additional samples in metadata for the configured grid.
- `OverlayElements` requires each item to include `image`; optional `bbox` values are normalized `[x_min, y_min, x_max, y_max]`.
- For detection labels or nontrivial coordinates, route to `../targets-and-formats/`.

## Spectrogram augmentation

```python
import albumentations as A

spec_aug = A.Compose([
    A.XYMasking(
        num_masks_x=(1, 2),
        mask_x_length=(0, 40),  # time axis if width is time
        num_masks_y=(1, 2),
        mask_y_length=(0, 24),  # frequency axis if height is frequency
        fill=0,
        fill_mask=None,
        p=0.5,
    ),
    A.HorizontalFlip(p=0.1),  # use only if time reversal is label-preserving
])
```

Checks:

- Axis semantics depend on how the spectrogram image is laid out.
- `TimeMasking` and `FrequencyMasking` are convenience wrappers and may warn that `XYMasking` is more flexible.
- Keep masks within image dimensions; validation raises if a mask length exceeds the current width/height.

## Text rendering onto images

```python
from pathlib import Path
import albumentations as A

text_aug = A.Compose([
    A.TextImage(
        font_path=Path("/path/to/your/font.ttf"),
        stopwords=("the", "is", "in", "at", "of"),
        augmentations=(None, "insertion", "swap", "deletion"),
        fraction_range=(0.5, 1.0),
        font_size_fraction_range=(0.6, 0.9),
        font_color=(0, 0, 0),
        clear_bg=False,
        metadata_key="textimage_metadata",
        p=0.5,
    ),
])

out = text_aug(image=image, textimage_metadata=text_metadata)
```

Checks:

- `font_path` must point to a readable font file in the user's project or environment.
- Provide `textimage_metadata` with the text and bbox information expected by the transform.
- Font rendering depends on Pillow-compatible font support; catch and report font errors separately from augmentation errors.
