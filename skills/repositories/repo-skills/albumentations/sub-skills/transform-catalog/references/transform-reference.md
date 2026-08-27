# Albumentations 2.x transform reference

This reference summarizes practical transform selection for Albumentations 2.0.8. It is self-contained: copy examples into your project and adjust image sizes, probabilities, and task-specific parameters.

## Mental model

- `ImageOnlyTransform` changes image pixels only. Use it for classification/color robustness, and do not rely on it to move masks, bboxes, or keypoints.
- `DualTransform` changes spatial targets consistently when used inside `A.Compose(...)` with the needed target parameters. This is the usual choice for segmentation, detection, and keypoints.
- Most geometric transforms support `image`, `mask`, `bboxes`, and `keypoints`; many also support `volume` and `mask3d`. Confirm target contracts in `../targets-and-formats/` when coordinates matter.
- `p` is the per-transform probability. A transform with `p=1.0` can still sample an identity operation if its parameter distribution includes identity, for example `RandomRotate90` includes a 0-degree case.
- Range parameters are normally 2-tuples `(min, max)` in nondecreasing order. A scalar is accepted by some transforms and converted to a symmetric or biased range; use explicit tuples when clarity matters.

## Pixel, color, intensity, noise, and weather

These transforms are image-only unless noted by their class docs. They are safe to combine with masks because they leave masks unchanged.

| Need | Typical transforms | Key parameters and notes |
| --- | --- | --- |
| Brightness/contrast | `A.RandomBrightnessContrast` | `brightness_limit`, `contrast_limit`, `brightness_by_max=True`, `ensure_safe_range=False`, `p=0.5`. Limits accept float or `(low, high)` tuples such as `(-0.2, 0.2)`. |
| Hue/saturation/value | `A.HueSaturationValue` | `hue_shift_limit`, `sat_shift_limit`, `val_shift_limit`; RGB-style color augment for uint8 or float32 images. |
| Normalization | `A.Normalize` | Standard mode uses `mean`, `std`, `max_pixel_value=255.0`. Other modes: `"image"`, `"image_per_channel"`, `"min_max"`, `"min_max_per_channel"`. Put normalization near the end, before tensor conversion. |
| Noise | `A.GaussNoise`, `A.ISONoise`, `A.MultiplicativeNoise`, `A.SaltAndPepper`, `A.ShotNoise`, `A.AdditiveNoise` | Validate range tuple names in your installed version; probe signatures with `scripts/transform_probe.py signature GaussNoise`. |
| Color channel effects | `A.RGBShift`, `A.ChannelShuffle`, `A.ToGray`, `A.ToRGB`, `A.ToSepia`, `A.FancyPCA`, `A.ColorJitter`, `A.PlanckianJitter` | Some transforms expect RGB/grayscale-compatible input; non-RGB images can raise validation errors. |
| Contrast/equalization | `A.CLAHE`, `A.Equalize`, `A.AutoContrast`, `A.RandomGamma`, `A.RandomToneCurve` | Useful for microscopy, documents, low-contrast scenes, and scanner variation. |
| Compression/downscale | `A.ImageCompression`, `A.Downscale`, `A.Posterize`, `A.Solarize`, `A.RingingOvershoot`, `A.Superpixels` | Use for sensor/codec robustness. Some operations are expensive or create non-photorealistic artifacts if overused. |
| Weather/lighting | `A.RandomFog`, `A.RandomRain`, `A.RandomSnow`, `A.RandomShadow`, `A.RandomSunFlare`, `A.RandomGravel`, `A.Spatter`, `A.PlasmaShadow`, `A.PlasmaBrightnessContrast`, `A.Illumination` | Use for outdoor or domain-specific robustness; keep probabilities low and inspect samples. |

Example:

```python
import albumentations as A

color_aug = A.Compose([
    A.RandomBrightnessContrast(brightness_limit=(-0.15, 0.15), contrast_limit=(-0.2, 0.2), p=0.5),
    A.HueSaturationValue(hue_shift_limit=(-10, 10), sat_shift_limit=(-20, 20), val_shift_limit=(-10, 10), p=0.3),
    A.GaussNoise(p=0.2),
])
```

## Blur and sharpening

| Need | Typical transforms | Notes |
| --- | --- | --- |
| Generic blur | `A.Blur`, `A.GaussianBlur`, `A.MedianBlur`, `A.MotionBlur` | Kernel/blur limits are validated; odd kernel constraints can trigger warnings or corrections. |
| Camera/lens blur | `A.Defocus`, `A.GlassBlur`, `A.ZoomBlur`, `A.AdvancedBlur` | Useful for camera quality and focus simulation. |
| Sharpening | `A.Sharpen`, `A.UnsharpMask`, `A.Emboss` | Keep probability and intensity modest for natural images. |

Blur transforms are usually image-only. They should not blur segmentation masks.

## Crop, resize, and pad

| Need | Transform | Representative signature and decisions |
| --- | --- | --- |
| Fixed crop | `A.RandomCrop(height, width, pad_if_needed=False, pad_position="center", border_mode=cv2.BORDER_CONSTANT, fill=0.0, fill_mask=0.0, p=1.0)` | Use `pad_if_needed=True` if input may be smaller than the crop. Choose `fill_mask` as a valid background/ignore label. |
| Center crop | `A.CenterCrop(height, width, pad_if_needed=False, ...)` | Deterministic crop for validation or resize/crop recipes. |
| Random resized crop | `A.RandomResizedCrop(size=(h, w), scale=(0.08, 1.0), ratio=(0.75, 1.3333), interpolation=cv2.INTER_LINEAR, mask_interpolation=cv2.INTER_NEAREST, area_for_downscale=None, p=1.0)` | Albumentations 2.x uses `size=(height, width)`, not separate height/width constructor arguments. |
| Resize | `A.Resize(height, width, interpolation=cv2.INTER_LINEAR, mask_interpolation=cv2.INTER_NEAREST, area_for_downscale=None, p=1)` | Use `area_for_downscale="image"` for quality downscaling images while preserving nearest masks. |
| Aspect preserving | `A.LongestMaxSize`, `A.SmallestMaxSize` | Often pair with `A.PadIfNeeded` for square model inputs. |
| Padding | `A.PadIfNeeded(min_height=..., min_width=..., pad_height_divisor=None, pad_width_divisor=None, position="center", border_mode=cv2.BORDER_CONSTANT, fill=0, fill_mask=0, p=1.0)` | Use `min_*` for fixed shape or `pad_*_divisor` for stride divisibility. |
| Random crop near target | `A.CropNonEmptyMaskIfExists`, `A.RandomCropNearBBox` | Useful when segmentation/detection positives are sparse; coordinate details route to `../targets-and-formats/`. |

Important `fill` behavior:

- `fill` applies to image padding/constant borders and may be a scalar or per-channel tuple.
- `fill_mask` applies to masks. For segmentation, set it to a valid background class or ignore index; do not use random image fills on masks.
- Old v1 names `value` and `mask_value` should be converted to `fill` and `fill_mask`.

## Geometric transforms

| Need | Transform | Notes |
| --- | --- | --- |
| Flips | `A.HorizontalFlip`, `A.VerticalFlip`, `A.Transpose`, `A.D4` | `D4` samples square-image rotations/flips from the dihedral group; useful for microscopy/satellite domains with true orientation symmetry. |
| 90-degree rotations | `A.RandomRotate90(p=1.0)` | Samples 0, 90, 180, or 270 degrees; identity is possible even with `p=1.0`. |
| Arbitrary rotation | `A.Rotate(limit=(-90, 90), interpolation=cv2.INTER_LINEAR, border_mode=cv2.BORDER_CONSTANT, rotate_method="largest_box", crop_border=False, mask_interpolation=cv2.INTER_NEAREST, fill=0, fill_mask=0, p=0.5)` | Use `crop_border=True` only when losing border pixels is acceptable. |
| Safe rotation | `A.SafeRotate` | Preserves whole image content by scaling after rotation; can change object scale. |
| Affine | `A.Affine(scale=(1.0, 1.0), translate_percent=None, translate_px=None, rotate=0.0, shear=(0.0, 0.0), interpolation=cv2.INTER_LINEAR, mask_interpolation=cv2.INTER_NEAREST, fit_output=False, keep_ratio=False, rotate_method="largest_box", balanced_scale=False, border_mode=cv2.BORDER_CONSTANT, fill=0, fill_mask=0, p=0.5)` | Prefer explicit tuples/dicts for scale/translate/shear. `balanced_scale=True` helps avoid biased sampling when scale spans below and above 1. |
| Perspective/distortion | `A.Perspective`, `A.ElasticTransform`, `A.GridDistortion`, `A.OpticalDistortion`, `A.ThinPlateSpline`, `A.PiecewiseAffine` | Use with care for detection/keypoints; verify coordinate support and visual realism. |

OpenCV interpolation guidance:

- Images: `cv2.INTER_LINEAR` is a common default; `cv2.INTER_AREA` is good for downscaling; `cv2.INTER_CUBIC`/`LANCZOS4` can be sharper but slower.
- Masks: use `cv2.INTER_NEAREST` or `cv2.INTER_NEAREST_EXACT` to preserve discrete labels.
- Border modes include `cv2.BORDER_CONSTANT`, `BORDER_REPLICATE`, `BORDER_REFLECT`, `BORDER_WRAP`, and `BORDER_REFLECT_101`. Constant borders use `fill`/`fill_mask`.

## Dropout and occlusion

| Need | Transform | Key parameters and notes |
| --- | --- | --- |
| Rectangular erasing | `A.CoarseDropout(num_holes_range=(1, 2), hole_height_range=(0.1, 0.2), hole_width_range=(0.1, 0.2), fill=0, fill_mask=None, p=0.5)` | Floats in hole ranges are fractions of image size; ints are pixels. Inpainting fills work only for grayscale/RGB images. |
| Grid occlusion | `A.GridDropout(ratio=0.5, random_offset=True, unit_size_range=None, holes_number_xy=None, shift_xy=(0, 0), fill=0, fill_mask=None, p=0.5)` | `holes_number_xy=(x, y)` overrides unit-size sampling. `ratio` must be in `(0, 1]`. |
| Mask-driven dropout | `A.MaskDropout`, `A.ConstrainedCoarseDropout` | Use when occlusion should follow mask labels or bboxes; ensure labels and masks are provided correctly. |
| Channel dropout | `A.ChannelDropout` | Do not use when channels have non-image semantics unless zeroing channels is meaningful. |
| Strip masking | `A.XYMasking` | General x/y strip masking for spectrogram-like images. |

For segmentation, choose whether the mask should change:

- `fill_mask=None` leaves mask regions unchanged for dropout transforms.
- `fill_mask=0` or an ignore index changes the segmentation labels in dropped regions.
- Inpainting image fills (`"inpaint_telea"`, `"inpaint_ns"`) are image-only fill strategies and require grayscale/RGB images.

## Mixing, overlays, and domain adaptation

These transforms need extra data supplied at call time. Missing metadata is a common error.

| Transform | Purpose | Required/important metadata |
| --- | --- | --- |
| `A.Mosaic(grid_yx=(2, 2), target_size=(512, 512), cell_shape=(512, 512), center_range=(0.3, 0.7), fit_mode="cover", interpolation=cv2.INTER_LINEAR, mask_interpolation=cv2.INTER_NEAREST, fill=0, fill_mask=0, metadata_key="mosaic_metadata", p=0.5)` | Combine primary image with additional images/targets in a mosaic. | Pass `mosaic_metadata` containing additional samples. Use `fit_mode="cover"` or `"contain"` depending on crop vs letterbox behavior. |
| `A.OverlayElements(metadata_key="overlay_metadata", p=0.5)` | Paste overlay images/masks/bboxes onto a base image. | Pass `overlay_metadata`, a list of dictionaries with at least `image`; optional `mask`, `bbox`, `mask_id`, and bbox id fields. Bbox values are normalized Albumentations format. |
| `A.FDA(reference_images=None, beta_limit=(0, 0.1), read_fn=..., metadata_key="fda_metadata", p=0.5)` | Fourier Domain Adaptation. | Prefer `fda_metadata=[reference_image_array, ...]`. Constructor `reference_images`/`read_fn` is deprecated and warns. |
| `A.HistogramMatching(reference_images=None, blend_ratio=(0.5, 1.0), read_fn=..., metadata_key="hm_metadata", p=0.5)` | Match histogram style to target domain. | Prefer `hm_metadata=[reference_image_array, ...]`. |
| `A.PixelDistributionAdaptation(reference_images=None, blend_ratio=(0.25, 1.0), read_fn=..., transform_type="pca", metadata_key="pda_metadata", p=0.5)` | Match pixel distribution via `"pca"`, `"standard"`, or `"minmax"`. | Prefer `pda_metadata=[reference_image_array, ...]`. |

Metadata examples:

```python
result = A.Compose([A.HistogramMatching(p=1.0)])(
    image=image,
    hm_metadata=[reference_image_1, reference_image_2],
)

result = A.Compose([A.Mosaic(p=1.0)])(
    image=image,
    mask=mask,
    mosaic_metadata=[{"image": image_b, "mask": mask_b}, {"image": image_c, "mask": mask_c}],
)
```

## Spectrogram and text surfaces

| Surface | Transforms | Notes |
| --- | --- | --- |
| Spectrogram images | `A.TimeReverse`, `A.TimeMasking`, `A.FrequencyMasking`, `A.XYMasking` | `TimeReverse` is an alias-style horizontal flip. `TimeMasking` and `FrequencyMasking` warn that `XYMasking` is more flexible. Treat spectrograms as image arrays and choose axis semantics carefully. |
| Rendered text | `A.TextImage(font_path, stopwords=(...), augmentations=(...), fraction_range=(0, 1), font_size_fraction_range=(0, 1), font_color=(...), clear_bg=False, metadata_key="textimage_metadata", p=0.5)` | Requires a usable font file and per-sample `textimage_metadata`. Text augmentations are `None`, `"insertion"`, `"swap"`, and `"deletion"`. |
| Type conversion | `A.ToFloat`, `A.FromFloat`, `A.Lambda` | Route serialization concerns for `Lambda` to `../serialization-and-reproducibility/`; use explicit max values for dtype scaling when needed. |

## Albumentations 2.x parameter migrations

Common replacements:

| Old/v1-style | Albumentations 2.x |
| --- | --- |
| `value` | `fill` |
| `mask_value` | `fill_mask` |
| `RandomResizedCrop(height=H, width=W, ...)` | `RandomResizedCrop(size=(H, W), ...)` |
| `CoarseDropout(min_holes=..., max_holes=...)` | `CoarseDropout(num_holes_range=(min_holes, max_holes), ...)` |
| `CoarseDropout(min_height=..., max_height=...)` | `CoarseDropout(hole_height_range=(min_height, max_height), ...)` |
| `CoarseDropout(min_width=..., max_width=...)` | `CoarseDropout(hole_width_range=(min_width, max_width), ...)` |
| `GridDropout(unit_size_min=..., unit_size_max=...)` | `GridDropout(unit_size_range=(unit_size_min, unit_size_max), ...)` |
| Constructor `reference_images=` for domain adaptation | Prefer passing arrays under `fda_metadata`, `hm_metadata`, or `pda_metadata` at transform call time. |

Use the bundled probe helper to print these mappings:

```bash
python scripts/transform_probe.py migrate --transform CoarseDropout --params min_holes=2 max_holes=5 min_height=8 max_height=16 value=0 mask_value=255
```

## Target support checklist

Before using a transform with non-image targets:

1. Check whether it is image-only or dual/spatial. Pixel transforms usually leave masks and coordinates unchanged.
2. Put target-aware transforms inside `A.Compose`, not as standalone calls, when bboxes/keypoints/labels are involved.
3. Use `mask_interpolation=cv2.INTER_NEAREST` for masks and `fill_mask` for constant borders.
4. Confirm bbox/keypoint formats and label fields with `../targets-and-formats/`.
5. Run a tiny probe with an image and mask before applying to real training data.
