# Operation API reference

This reference covers `Augmentor.Pipeline` operation convenience methods and the custom `Operation` contract. Use these APIs inside a pipeline; route disk input/output orchestration to the pipeline workflow skill.

## Global probability rule

Most `Pipeline` operation methods validate `probability` with:

```python
0 < probability <= 1
```

Invalid values raise:

```text
ValueError: The probability argument must be between 0 and 1.
```

Use `probability=1` when the transform is required, such as fixed resizing or converting all outputs to greyscale. Keep the same rule for manually added `Operation` objects even when a lower-level class does not validate it for you.

## Geometry operations

| Method | Main effect | Key parameters and ranges | Common errors / notes |
| --- | --- | --- | --- |
| `rotate90(probability)` | Rotate by 90 degrees. | `0 < probability <= 1`. | Output canvas expands for the 90-degree rotation. |
| `rotate180(probability)` | Rotate by 180 degrees. | `0 < probability <= 1`. | Output canvas expands for the rotation. |
| `rotate270(probability)` | Rotate by 270 degrees. | `0 < probability <= 1`. | Output canvas expands for the rotation. |
| `rotate_random_90(probability)` | Uniformly choose 90, 180, or 270 degrees when the operation executes. | `0 < probability <= 1`. | The probability controls whether a rotation happens, not which angle is chosen. |
| `rotate(probability, max_left_rotation, max_right_rotation)` | Rotate by a random arbitrary angle, crop the largest valid rectangle, then resize back to the original dimensions. | `0 <= max_left_rotation <= 25`; `0 <= max_right_rotation <= 25`; values are rounded up with `ceil()`. | Errors: `The max_left_rotation argument must be between 0 and 25.` / `The max_right_rotation argument must be between 0 and 25.` Keep angles small when corners or content loss are unacceptable. |
| `rotate_without_crop(probability, max_left_rotation, max_right_rotation, expand=False, fillcolor=None)` | Rotate by a random arbitrary angle without the automatic largest-rectangle crop. | Use the same practical bounds as `rotate`: probability in `(0, 1]`, left/right rotations in `0..25`. `expand=True` expands the canvas; `fillcolor` can be `None` or a Pillow color such as `(0, 0, 0)`. | This convenience method delegates directly to `RotateStandard`; validate inputs yourself before adding it. `expand=False` preserves dimensions and may fill corners. |
| `flip_top_bottom(probability)` | Mirror top-to-bottom. | `0 < probability <= 1`. | Use only when vertical inversion preserves labels. |
| `flip_left_right(probability)` | Mirror left-to-right. | `0 < probability <= 1`. | Common for natural images with left/right symmetry. |
| `flip_random(probability)` | Randomly choose left-right or top-bottom flip. | `0 < probability <= 1`. | Do not use if one axis invalidates labels. |
| `skew_left_right(probability, magnitude=1)` | Perspective skew left or right. | `0 < magnitude <= 1`; `1` represents the largest supported tilt, documented as 45 degrees. | Error: `The magnitude argument must be greater than 0 and less than or equal to 1.` |
| `skew_top_bottom(probability, magnitude=1)` | Perspective skew forward/backward. | `0 < magnitude <= 1`. | Same magnitude error as above. |
| `skew_tilt(probability, magnitude=1)` | Randomly skew left, right, up, or down. | `0 < magnitude <= 1`. | Same magnitude error as above. |
| `skew_corner(probability, magnitude=1)` | Randomly skew one of the eight corner directions. | `0 < magnitude <= 1`. | Same magnitude error as above. |
| `skew(probability, magnitude=1)` | Randomly choose among tilt and corner skew families. | `0 < magnitude <= 1`. | Same magnitude error as above. |
| `shear(probability, max_shear_left, max_shear_right)` | Shear in a random axis/direction, crop and resize back to original dimensions. | `0 < max_shear_left <= 25`; `0 < max_shear_right <= 25`. | Errors: `The max_shear_left argument must be between 0 and 25.` / `The max_shear_right argument must be between 0 and 25.` Unlike `rotate`, zero is not accepted by the source validation. |

## Distortion operations

| Method | Main effect | Key parameters and ranges | Common errors / notes |
| --- | --- | --- | --- |
| `random_distortion(probability, grid_width, grid_height, magnitude)` | Elastic mesh distortion with random displacement. | Probability in `(0, 1]`. Source guidance: grid width/height usually `2..10`; magnitude usually `1..10`. | The convenience method does not validate grid/magnitude beyond probability. Use positive integer grid sizes that divide the image reasonably; tiny images plus large grids can create degenerate cells. |
| `gaussian_distortion(probability, grid_width, grid_height, magnitude, corner, method, mex=0.5, mey=0.5, sdx=0.05, sdy=0.05)` | Elastic distortion whose displacement follows a Gaussian-like surface. | Probability in `(0, 1]`; positive grid sizes and magnitude. `corner` should be one of `"bell"`, `"ul"`, `"ur"`, `"dl"`, `"dr"`. `method` should be `"in"` or `"out"`. | Invalid `corner` can fail at execution because the lower-level class indexes known corner names. Start with `corner="bell", method="in"` for a safe smoke. |

## Size, crop, zoom, and resize operations

| Method | Main effect | Key parameters and ranges | Common errors / notes |
| --- | --- | --- | --- |
| `zoom(probability, min_factor, max_factor)` | Zoom into the centre while returning the original dimensions. | `min_factor > 0`; choose `max_factor >= min_factor` even though the source only validates `min_factor`. Typical values: `1.1..1.5`. | Error: `The min_factor argument must be greater than 0.` |
| `zoom_random(probability, percentage_area, randomise_percentage_area=False)` | Crop a random area and resize back to original dimensions. | `0.1 <= percentage_area < 1`; `randomise_percentage_area` must be bool. | Errors: `The percentage_area argument must be greater than 0.1 and less than 1.` and `The randomise_percentage_area argument must be True or False.` |
| `crop_by_size(probability, width, height, centre=True)` | Crop fixed pixel dimensions from the centre or a random location. | `width > 1`; `height > 1`; `centre` must be bool. | Errors: `The width argument must be greater than 1.`, `The height argument must be greater than 1.`, `The centre argument must be True or False.` If the crop is larger than the image, the source returns the full image unchanged. |
| `crop_centre(probability, percentage_area, randomise_percentage_area=False)` | Centre crop by area fraction. | `0.1 <= percentage_area < 1`; `randomise_percentage_area` must be bool. | Same percentage/bool errors as `zoom_random`. |
| `crop_random(probability, percentage_area, randomise_percentage_area=False)` | Random crop by area fraction. | `0.1 <= percentage_area < 1`; `randomise_percentage_area` must be bool. | Same percentage/bool errors as `zoom_random`. Combine with `resize(probability=1, ...)` if outputs must return to fixed dimensions. |
| `scale(probability, scale_factor)` | Enlarge while preserving aspect ratio; returns larger dimensions. | `scale_factor > 1`. | Error: `The scale_factor argument must be greater than 1.` This is not the same as `zoom`, which preserves original dimensions. |
| `resize(probability, width, height, resample_filter="BICUBIC")` | Resize to absolute pixel dimensions. | `width > 1`; `height > 1`; filter in `"NEAREST"`, `"BICUBIC"`, `"ANTIALIAS"`, `"BILINEAR"`. | Errors: `Width must be greater than 1.`, `Height must be greater than 1.`, `The save_filter argument must be one of ...` Source uses legacy Pillow constants; with Pillow 10+, avoid `ANTIALIAS` unless compatibility aliases are present. |

## Color, intensity, and occlusion operations

| Method | Main effect | Key parameters and ranges | Common errors / notes |
| --- | --- | --- | --- |
| `histogram_equalisation(probability=1.0)` | Apply histogram equalisation. | Probability in `(0, 1]`. | `probability=1` is recommended when equalisation is required. |
| `greyscale(probability)` | Convert to greyscale. | Probability in `(0, 1]`. | Returns greyscale PIL images. |
| `black_and_white(probability, threshold=128)` | Convert to 1-bit black/white using a threshold. | `0 <= threshold <= 255`. | Error: `The threshold must be between 0 and 255.` Use after operations that expect RGB if those operations cannot handle 1-bit images. |
| `invert(probability)` | Invert pixel values. | Probability in `(0, 1]`. | Source warns this can error on binary 1-bit images. If needed, invert before `black_and_white()` or convert back to a compatible mode. |
| `random_brightness(probability, min_factor, max_factor)` | Uniformly choose a Pillow brightness factor. | `0 <= min_factor <= max_factor`. `1.0` keeps original brightness; `0.0` gives black; values above `1.0` brighten. | Error: `The min_factor must be between 0 and max_factor.` |
| `random_color(probability, min_factor, max_factor)` | Uniformly choose a Pillow color/saturation factor. | `0 <= min_factor <= max_factor`. `1.0` keeps original color; `0.0` approaches black-and-white; values above `1.0` increase color. | Same min/max error as brightness. |
| `random_contrast(probability, min_factor, max_factor)` | Uniformly choose a Pillow contrast factor. | `0 <= min_factor <= max_factor`. `1.0` keeps original contrast; `0.0` gives solid grey; values above `1.0` increase contrast. | Same min/max error as brightness. |
| `random_erasing(probability, rectangle_area)` | Add a random-noise rectangle to simulate occlusion. | `0.01 <= rectangle_area <= 1`. | Error: `The rectangle_area must be between 0.01 and 1.` The operation is marked work-in-progress in source comments; smoke it on sample images before large jobs. |

## Custom and lower-level operations

### Add a custom `Operation` subclass

```python
import Augmentor
from PIL import Image
from Augmentor.Operations import Operation

class InvertRed(Operation):
    def __init__(self, probability):
        Operation.__init__(self, probability)

    def perform_operation(self, images):
        transformed = []
        for image in images:
            image = image.convert("RGB")
            r, g, b = image.split()
            transformed.append(Image.merge("RGB", (r.point(lambda x: 255 - x), g, b)))
        return transformed

p = Augmentor.Pipeline("images")
p.add_operation(InvertRed(probability=0.5))
```

Contract:

- The object passed to `add_operation(operation)` must be an instance of `Augmentor.Operations.Operation`, otherwise `Pipeline.add_operation()` raises `TypeError: Must be of type Operation to be added to the pipeline.`
- `__init__` must call `Operation.__init__(self, probability)`.
- `perform_operation(self, images)` receives a list of PIL Images and must return a list of PIL Images. Preserve list length unless you intentionally own all downstream behavior.
- Custom operations can be mixed with built-ins by inserting them in the desired pipeline order.

### Lower-level classes without top-level convenience methods

- `HSVShifting(probability, hue_shift, saturation_scale, saturation_shift, value_scale, value_shift)` exists as a lower-level `Operation` class but has no `Pipeline.hsv_shifting()` convenience method. Add it manually only after a small smoke check.
- `Mixup(probability, alpha=0.4)` exists as a lower-level class, but source comments say it is not enabled for the normal pipeline because it requires image-label pairs. Do not present it as a ready `Pipeline` workflow.
- `Operations.Custom` exists as a lower-level wrapper, but the robust extension path is to subclass `Operation` directly and pass the instance to `Pipeline.add_operation()`.
