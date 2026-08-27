# Operation selection guide

Use this guide to choose Augmentor operations by augmentation goal. Keep dataset semantics first: an operation is useful only if the transformed image should keep the same label or annotation meaning.

## Selection table

| Goal | Prefer these operations | Avoid or check |
| --- | --- | --- |
| Make labels robust to right-angle orientation changes | `rotate90()`, `rotate180()`, `rotate270()`, `rotate_random_90()` | Avoid for digits, text, medical laterality, road signs, or any class where orientation changes the label. |
| Simulate small camera tilt while preserving original output size | `rotate(probability, max_left_rotation, max_right_rotation)` with small values such as `5..10`; `shear()` with values well below 25 | Keep arbitrary rotation/shear at or below 25 degrees. Large values are rejected or over-cropped. |
| Keep all rotated content rather than auto-cropping | `rotate_without_crop(..., expand=True, fillcolor=(r, g, b))` | `expand=True` changes dimensions. If later model inputs need fixed size, add `resize(probability=1, ...)` after rotation. |
| Use perspective/viewpoint variation | `skew_left_right()`, `skew_top_bottom()`, `skew_tilt()`, `skew_corner()`, `skew()` | Keep `magnitude` in `(0, 1]`; lower values are safer. Do not use if perspective changes class meaning. |
| Use mirror symmetry | `flip_left_right()`, `flip_top_bottom()`, `flip_random()` | `flip_random()` can choose an invalid axis; use a specific flip when only one axis is label-safe. |
| Fixed model input dimensions | `resize(probability=1, width=..., height=..., resample_filter="BICUBIC")` | Use filters supported by the installed Pillow version. Avoid `ANTIALIAS` with Pillow 10+ unless a compatibility alias exists. |
| Crop viewpoint or object position | `crop_by_size()`, `crop_centre()`, `crop_random()` | Crop percentages must be at least `0.1` and less than `1`. Combine with `resize()` if output dimensions must be fixed. |
| Zoom while preserving output dimensions | `zoom()` for centre zoom; `zoom_random()` for random-region zoom | `zoom()` validates only `min_factor > 0`; still choose `max_factor >= min_factor`. `zoom_random()` uses `percentage_area`, not a zoom factor. |
| Enlarge dimensions while preserving aspect ratio | `scale(probability, scale_factor)` | `scale()` returns larger images. Use `zoom()` instead if dimensions must stay unchanged. |
| Simulate non-rigid local deformation | `random_distortion()` or `gaussian_distortion()` | Start with modest grids/magnitude. Very small images, oversized grids, or large magnitudes can create degenerate distortions. |
| Normalize or vary intensity/color | `histogram_equalisation()`, `random_brightness()`, `random_color()`, `random_contrast()` | Do not let color transforms erase class-discriminative color if color is part of the label. |
| Convert image mode | `greyscale()`, `black_and_white()`, `invert()` | `invert()` can fail on binary 1-bit images; place it before `black_and_white()` or convert modes. `black_and_white()` threshold must be `0..255`. |
| Simulate occlusion | `random_erasing(probability, rectangle_area)` | `rectangle_area` is `0.01..1`; large rectangles may remove the object entirely. Smoke before high-volume generation. |
| Add a domain-specific PIL transform | Subclass `Augmentor.Operations.Operation` and call `p.add_operation(custom_op)` | Return a list of PIL Images, call `Operation.__init__`, and preserve image list length when masks/paired images might be used later. |

## Safe built-in operation stacks

### General natural-image classifier

```python
p.flip_left_right(probability=0.5)
p.rotate(probability=0.7, max_left_rotation=10, max_right_rotation=10)
p.zoom_random(probability=0.3, percentage_area=0.8)
p.random_brightness(probability=0.3, min_factor=0.8, max_factor=1.2)
p.random_contrast(probability=0.3, min_factor=0.8, max_factor=1.2)
p.resize(probability=1, width=224, height=224, resample_filter="BICUBIC")
```

Use only if left/right flips and small rotations preserve labels. The final `resize()` standardizes dimensions after crop/zoom.

### Segmentation-like imagery with future masks

```python
p.rotate(probability=0.5, max_left_rotation=5, max_right_rotation=5)
p.flip_left_right(probability=0.5)
p.zoom_random(probability=0.2, percentage_area=0.9)
```

Keep transforms geometric and conservative. Route the actual mask pairing and identical-transform execution to `masks-and-arrays`.

### Document, digit, or orientation-sensitive labels

```python
p.random_brightness(probability=0.4, min_factor=0.9, max_factor=1.1)
p.random_contrast(probability=0.4, min_factor=0.9, max_factor=1.1)
p.resize(probability=1, width=target_w, height=target_h)
```

Avoid right-angle rotations, vertical flips, and aggressive perspective transforms unless the label definition explicitly allows them.

### Custom PIL operation mixed with built-ins

```python
p.rotate(probability=0.5, max_left_rotation=5, max_right_rotation=5)
p.add_operation(MyPILOperation(probability=0.25))
p.resize(probability=1, width=128, height=128)
```

The custom operation runs exactly where it is inserted. If it changes image mode or size, ensure later built-ins can accept that mode/size.

## Lower-level operation classes

- `HSVShifting` is a lower-level `Operation` class, not a `Pipeline` convenience method. Add it manually only after a small probe confirms it works for the image mode and value ranges.
- `Mixup` is a lower-level class whose source comments state it is not enabled for ordinary pipeline use because it needs label pairs. Do not use it as a standard top-level augmentation workflow.
- For ordinary user-facing workflows, built-in `Pipeline` methods plus explicit custom `Operation` subclasses are the most reliable path.
