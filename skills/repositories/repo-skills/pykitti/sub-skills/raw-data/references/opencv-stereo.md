# Optional OpenCV and stereo processing

`pykitti.raw` decodes files with Pillow and returns `PIL.Image` objects. It
does not invoke OpenCV while reading images. There is nevertheless an import
boundary in `pykitti==0.3.1`: `pykitti/__init__.py` imports `tracking.py`, and
that module imports `cv2` eagerly. A successful normal `import pykitti` thus
requires a compatible OpenCV package even for a Pillow-only raw workflow. See
[troubleshooting](troubleshooting.md) if the import fails.

## Convert raw images without a GUI

Camera modes are already normalized by pykitti. Convert explicitly at the
boundary to avoid channel-order surprises:

```python
import cv2
import numpy as np

left_gray, right_gray = data.get_gray(index)
left_gray_u8 = np.asarray(left_gray)
right_gray_u8 = np.asarray(right_gray)
assert left_gray_u8.ndim == 2

gray_disparity = cv2.StereoBM_create(
    numDisparities=16,
    blockSize=15,
).compute(left_gray_u8, right_gray_u8)

left_rgb, right_rgb = data.get_rgb(index)
left_rgb_u8 = np.asarray(left_rgb)
right_rgb_u8 = np.asarray(right_rgb)
assert left_rgb_u8.shape[-1] == 3
left_for_cv = cv2.cvtColor(left_rgb_u8, cv2.COLOR_RGB2GRAY)
right_for_cv = cv2.cvtColor(right_rgb_u8, cv2.COLOR_RGB2GRAY)
rgb_disparity = cv2.StereoBM_create(
    numDisparities=16,
    blockSize=15,
).compute(left_for_cv, right_for_cv)
```

The example performs no display, file write, network access, or GUI call. A
real StereoBM input must satisfy the OpenCV algorithm's size, block-size, and
disparity constraints; the tiny raw fixture is intended to verify pykitti
loading, not to produce a meaningful disparity map. For larger real images,
choose algorithm parameters appropriate to their width and texture.

If an OpenCV API expects BGR rather than RGB, convert with
`cv2.cvtColor(image, cv2.COLOR_RGB2BGR)` at that boundary. Do not reinterpret
`np.asarray(PIL_image)` as BGR without converting. `cam0` and `cam1` are
already single-channel `L` images; avoid a redundant RGB-to-gray conversion.

## Relate disparity to calibration

For a rectified pair, the approximate depth relation is `Z = f * B / d`,
where `f` is the rectified focal length in pixels, `B` is the matching
baseline in meters, and `d` is positive disparity in pixels. Use the matching
fields:

- gray pair (`cam0`, `cam1`): `data.calib.P_rect_00[0, 0]` and
  `data.calib.b_gray`;
- RGB pair (`cam2`, `cam3`): `data.calib.P_rect_20[0, 0]` and
  `data.calib.b_rgb`.

This relation is meaningful only after confirming the cameras are the intended
rectified pair and the disparity convention is known. Treat zero or negative
disparity as invalid for this calculation, and do not infer depth from a
single unrectified image.

## Dependency and runtime boundary

Install an OpenCV build compatible with the active Python environment when
stereo computation is required. A headless build is appropriate for a service
or CI workflow that does not display windows. Keep `cv2.imshow`,
`cv2.waitKey`, Matplotlib display, and any archive downloader out of
non-interactive validation. The bundled raw fixture smoke test deliberately
uses Pillow and NumPy assertions only; it does not require a GUI or perform
stereo matching.
