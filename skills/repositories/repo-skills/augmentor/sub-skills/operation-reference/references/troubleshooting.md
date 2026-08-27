# Operation troubleshooting

## Validation quick fixes

| Symptom / error | Likely cause | Recovery |
| --- | --- | --- |
| `The probability argument must be between 0 and 1.` | `probability <= 0` or `probability > 1`. | Use `0 < probability <= 1`. Use `1` for required operations. |
| `The max_left_rotation argument must be between 0 and 25.` or `The max_right_rotation argument must be between 0 and 25.` | `rotate()` arbitrary angle bound is outside `0..25`. | Clamp each rotate bound to `0..25`. Use `rotate90/180/270` for right-angle rotations. |
| `The max_shear_left argument must be between 0 and 25.` or `The max_shear_right argument must be between 0 and 25.` | `shear()` bound is not strictly positive or exceeds 25. | Use `0 < max_shear_left <= 25` and `0 < max_shear_right <= 25`. |
| `The percentage_area argument must be greater than 0.1 and less than 1.` | `crop_centre()`, `crop_random()`, or `zoom_random()` has area outside bounds. | Use `0.1 <= percentage_area < 1`. Remember it is area fraction, not output pixel size. |
| `The randomise_percentage_area argument must be True or False.` | Non-bool value such as `0`, `1`, or string. | Pass `True` or `False`. |
| `The width argument must be greater than 1.` / `The height argument must be greater than 1.` | `crop_by_size()` crop dimension is too small. | Use integer dimensions greater than 1. If dimensions exceed the image, the source returns the image unchanged rather than cropping. |
| `Width must be greater than 1.` / `Height must be greater than 1.` | `resize()` target dimension is too small. | Use target dimensions greater than 1. |
| `The save_filter argument must be one of ...` | `resize(..., resample_filter=...)` is not in the allowed names. | Use one of `NEAREST`, `BICUBIC`, `ANTIALIAS`, or `BILINEAR`. Prefer `BICUBIC` or `BILINEAR` for cross-version safety. |
| `The scale_factor argument must be greater than 1.` | `scale()` was used for downscaling or no-op scaling. | Use `scale_factor > 1`, or use `resize()` for absolute dimensions. |
| `The magnitude argument must be greater than 0 and less than or equal to 1.` | Skew magnitude outside bounds. | Use `0 < magnitude <= 1`; start much lower than 1 for subtle perspective changes. |
| `The threshold must be between 0 and 255.` | `black_and_white()` threshold outside byte range. | Use integer threshold `0..255`; default is `128`. |
| `The min_factor must be between 0 and max_factor.` | Brightness/color/contrast `min_factor` is negative or greater than `max_factor`. | Choose `0 <= min_factor <= max_factor`; values around `0.8..1.2` are conservative. |
| `The rectangle_area must be between 0.01 and 1.` | `random_erasing()` rectangle area outside bounds. | Use `0.01 <= rectangle_area <= 1`. Keep it small enough to avoid erasing the whole object. |
| `Must be of type Operation to be added to the pipeline.` | `add_operation()` received a function, class, or object that does not inherit `Augmentor.Operations.Operation`. | Instantiate a subclass of `Operation`, call `Operation.__init__`, then pass the instance to `add_operation()`. |

## Pillow resize filters and legacy constants

`Pipeline.resize()` accepts string names and then resolves them on `PIL.Image`:

```python
p.resize(probability=1, width=224, height=224, resample_filter="BICUBIC")
```

Allowed names are `NEAREST`, `BICUBIC`, `ANTIALIAS`, and `BILINEAR`. Older Augmentor releases were written against legacy Pillow constants. In Pillow 10+, `Image.ANTIALIAS` was removed in favor of newer `Resampling` enum names. To avoid compatibility failures, prefer `BICUBIC`, `BILINEAR`, or `NEAREST`, or use a Pillow version that still exposes the legacy constants.

## Invalid parameter recovery pattern

1. Read the exact validation message.
2. Map it to the method-specific range in `api-reference.md`.
3. Fix the parameter before adding the operation; do not catch the error and continue with a partially configured pipeline.
4. Run a tiny smoke sample before starting a large augmentation job.

Example recovery:

```python
# Fails: arbitrary rotate bounds are limited to 25 degrees.
p.rotate(probability=0.8, max_left_rotation=45, max_right_rotation=45)

# Recover: use small arbitrary rotation or a right-angle rotate method.
p.rotate(probability=0.8, max_left_rotation=10, max_right_rotation=10)
# or
p.rotate_random_90(probability=0.8)
```

## Custom Operation gotchas

A robust custom operation looks like this:

```python
from PIL import ImageOps
from Augmentor.Operations import Operation

class Posterize(Operation):
    def __init__(self, probability, bits=4):
        Operation.__init__(self, probability)
        self.bits = bits

    def perform_operation(self, images):
        out = []
        for image in images:
            out.append(ImageOps.posterize(image.convert("RGB"), self.bits))
        return out

p.add_operation(Posterize(probability=0.25, bits=4))
```

Checklist:

- `Operation.__init__(self, probability)` is called in `__init__`.
- `perform_operation(self, images)` accepts a list, iterates over the list, and returns a list.
- Every returned item is a PIL Image.
- Preserve the number and ordering of images in the list when future mask/ground-truth workflows may pass multiple paired images.
- If you mutate an image in place, understand that later operations will see the mutated image. Use `image.copy()` if you need to preserve the input object.
- Insert the custom operation in the intended order relative to built-ins; operations run sequentially.

## Custom PIL operation mixed with built-ins

When mixing custom and built-in operations, place operations so each receives the image mode and dimensions it expects:

```python
p.rotate(probability=0.5, max_left_rotation=5, max_right_rotation=5)
p.add_operation(Posterize(probability=0.25, bits=4))
p.resize(probability=1, width=128, height=128, resample_filter="BICUBIC")
```

If the custom step outputs mode `1`, `P`, or `L`, later operations such as `invert()` or color enhancement may fail or behave differently. Convert to `RGB` inside the custom operation when downstream color operations are expected.

## Distortion and Gaussian distortion failures

- Use positive integer `grid_width` and `grid_height`.
- Keep generated smoke images larger than the grid. For a `32x32` image, start with `grid_width=4`, `grid_height=4`, `magnitude=2`.
- For `gaussian_distortion()`, use `corner` in `"bell"`, `"ul"`, `"ur"`, `"dl"`, `"dr"` and `method` in `"in"`, `"out"`. Invalid corner names can fail when the operation executes.

## Color and mode ordering

- `black_and_white()` outputs 1-bit images; put it near the end of the operation list unless downstream operations explicitly support that mode.
- `invert()` source docs warn about binary 1-bit images; invert before converting to black and white, or convert back to `RGB` first.
- `histogram_equalisation()` is commonly used with `probability=1` when it is a normalization step rather than stochastic augmentation.

## Boundary reminders

- Disk input/output, output folder cleanup, `sample()`, `process()`, multithreading, and seeding are not operation-selection issues; route them to `pipeline-augmentation`.
- Mask/ground-truth safety requires paired-image handling; route it to `masks-and-arrays`.
- Keras, PyTorch, and DataFrame generator behavior belongs in `generators-and-frameworks`.
