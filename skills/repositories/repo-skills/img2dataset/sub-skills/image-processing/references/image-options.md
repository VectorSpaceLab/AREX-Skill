# Image options

`Resizer` decides geometry, codec, filters, and optional bbox blur. The current decision order is:

1. `disable_all_reencoding` returns raw bytes immediately.
2. Otherwise the image is decoded with OpenCV.
3. Filter checks run on the original decoded width and height.
4. Alpha-channel images are white-matted and forced through reencoding.
5. Resize mode, blur, and optional crop or pad are applied.
6. `skip_reencode` can reuse the original bytes only if the image did not change and the target format already matches.

## Resize modes

`image_size` is the target pixel size used by the resize transform. The code accepts all five mode names below, even where the public README only highlights a subset.

| Mode | Exact geometry rule | Gate when `resize_only_if_bigger=True` | Final dimensions |
| --- | --- | --- | --- |
| `no` | Do not resize at all. | Ignored. | Original `width x height`. |
| `keep_ratio` | Scale with `SmallestMaxSize` so the smaller side becomes `image_size`, preserving aspect ratio. | Only resize if `min(original_width, original_height) > image_size`. | Smaller side is `image_size`; the other side is proportional, rounded to integers. |
| `keep_ratio_largest` | Scale with `LongestMaxSize` so the larger side becomes `image_size`, preserving aspect ratio. | Only resize if `max(original_width, original_height) > image_size`. | Larger side is `image_size`; the other side is proportional, rounded to integers. |
| `border` | Apply `LongestMaxSize`, then pad with white borders to reach a square. | Only resize if `max(original_width, original_height) > image_size`. | Square `image_size x image_size` when resized; otherwise original size. |
| `center_crop` | Apply `SmallestMaxSize`, then center crop to a square with `CenterCrop`. | Only resize if `min(original_width, original_height) > image_size`. | Square `image_size x image_size` when resized; otherwise original size. |

### Practical notes

- The gate is strict: `>` for the relevant side. A side exactly equal to `image_size` does **not** trigger resizing when `resize_only_if_bigger=True`.
- `no` ignores `resize_only_if_bigger` completely.
- If the gate blocks resize, bbox blur can still run and the output dimensions stay unchanged.
- The resize helpers come from Albumentations; expect integer rounding that is close to `round(original_side * scale)`.
- `border` pads with white (`[255, 255, 255]`).

## Interpolation strings

The resize code accepts the following strings and maps them to OpenCV constants:

| String(s) | OpenCV constant |
| --- | --- |
| `nearest` | `cv2.INTER_NEAREST` |
| `linear`, `bilinear` | `cv2.INTER_LINEAR` |
| `cubic`, `bicubic` | `cv2.INTER_CUBIC` |
| `area` | `cv2.INTER_AREA` |
| `lanczos`, `lanczos4` | `cv2.INTER_LANCZOS4` |

Invalid strings raise `ValueError("Invalid option for interpolation: ...")`.

## Encoding and reencoding

Supported output formats are exactly `jpg`, `png`, and `webp`.

| Format | Quality field meaning | Validation in `Resizer` |
| --- | --- | --- |
| `jpg` | OpenCV JPEG quality scale, conceptually `0-100`. | Passed through to OpenCV. |
| `png` | Compression level, `0-9` with lower values keeping larger files. | Constructor validates the range and raises if outside `0-9`. |
| `webp` | OpenCV WebP quality scale, conceptually `0-100`. | Passed through to OpenCV. |

### Reencoding controls

- `skip_reencode=True` only skips the final encode when the decoded image did not change, the alpha path did not force a conversion, and the input file type already matches the requested output format.
- `disable_all_reencoding=True` is stronger: it returns the original byte stream immediately and does not decode, resize, filter, blur, or validate the image.
- If the image has a 4-channel alpha plane, it is matted onto a white background, converted to 3 channels, and forced through reencoding.

## Filtering

Filter checks happen before any resize or blur work and use the original decoded dimensions.

| Setting | Condition on the original decoded image | Error string |
| --- | --- | --- |
| `min_image_size` | `min(width, height) < min_image_size` | `image too small` |
| `max_image_area` | `width * height > max_image_area` | `image area too large` |
| `max_aspect_ratio` | `max(width, height) / min(width, height) > max_aspect_ratio` | `aspect ratio too large` |

These checks are strict: equality at the threshold is allowed.

## Bounding-box blur

`bbox_col` enables bbox blur in the downloader path, and `BoundingBoxBlurrer` can also be used directly with `Resizer`.

### Input contract

- Each bbox must be normalized to the original image size.
- The expected box order is `[x_min, y_min, x_max, y_max]`.
- Each value should be a float in `[0, 1]`.
- A Parquet bbox column is commonly stored as `list<list<double>>`, i.e. one list of boxes per row.

### Blur flow

1. Convert normalized coordinates to pixel coordinates using the current image width and height.
2. Expand each box by `10%` of the box diagonal on all sides.
3. Clip the expanded box to image bounds.
4. Build a mask over the union of all boxes.
5. Derive a Gaussian kernel size from the largest box diagonal.
6. Seed `numpy.random` and `random` with `42` for deterministic output.
7. Apply `A.GaussianBlur`, blend the blurred region into the original image, and convert back to `uint8`.

### Dimension semantics with blur

- Blur does not change output dimensions.
- In `keep_ratio` and `center_crop`, blur runs after scaling and before the optional crop.
- In `border` and `keep_ratio_largest`, blur runs after scaling and before the optional pad.
- In `no`, blur runs after validation on the original image size.

## API fragments

```python
from img2dataset.resizer import Resizer
from img2dataset.blurrer import BoundingBoxBlurrer

resizer = Resizer(
    image_size=256,
    resize_mode="border",
    resize_only_if_bigger=False,
    upscale_interpolation="lanczos",
    downscale_interpolation="area",
    encode_quality=95,
    encode_format="jpg",
    skip_reencode=False,
    disable_all_reencoding=False,
    min_image_size=0,
    max_image_area=float("inf"),
    max_aspect_ratio=float("inf"),
    blurrer=BoundingBoxBlurrer(),
)
```

```python
from img2dataset.main import download

download(
    url_list,
    image_size=256,
    resize_mode="border",
    resize_only_if_bigger=False,
    upscale_interpolation="lanczos",
    downscale_interpolation="area",
    encode_quality=95,
    encode_format="jpg",
    skip_reencode=False,
    disable_all_reencoding=False,
    min_image_size=0,
    max_image_area=float("inf"),
    max_aspect_ratio=float("inf"),
    bbox_col=None,
)
```
