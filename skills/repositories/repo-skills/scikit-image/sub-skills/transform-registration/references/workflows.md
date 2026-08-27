# Transform and Registration Workflows

These workflows focus on geometric operations, transform estimation, tomography, Hough helpers, and motion recovery. They assume any feature extraction, thresholding, or segmentation has already happened in another route.

## Warp, resize, and pyramids

Use the smallest operator that matches the geometry:

- `warp` for arbitrary inverse maps, transform objects, and custom coordinate fields.
- `swirl` for a localized nonlinear warp that is useful in tutorials and deformation demos.
- `rotate` for center rotation in degrees.
- `rescale` for scale factors.
- `resize` for an explicit output shape.
- `downscale_local_mean` for exact integer-factor block averages.
- `resize_local_mean` when you need area-based resizing with a multichannel axis.
- `pyramid_reduce`, `pyramid_expand`, `pyramid_gaussian`, and `pyramid_laplacian` for multiscale processing.

```python
import numpy as np
from skimage import data, img_as_float
from skimage.transform import (
    AffineTransform,
    downscale_local_mean,
    pyramid_gaussian,
    resize,
    resize_local_mean,
    rescale,
    rotate,
    warp,
)

rgb = img_as_float(data.astronaut())
gray = img_as_float(data.camera())

tform = AffineTransform(scale=(0.9, 0.9), rotation=np.deg2rad(10), translation=(12, -8))
warped = warp(rgb, tform.inverse)
rotated = rotate(gray, 15, resize=True)
scaled = rescale(rgb, 0.5, channel_axis=-1, anti_aliasing=True)
fitted = resize(rgb, (256, 256, 3), anti_aliasing=True)
block_mean = downscale_local_mean(gray, (4, 4))
area_resize = resize_local_mean(rgb, (128, 128, 3), channel_axis=-1)
pyramid = tuple(pyramid_gaussian(rgb, downscale=2, channel_axis=-1))
```

Notes:

- `resize` expects channels last; move axes yourself if your channel dimension is elsewhere.
- `downscale_local_mean` needs one factor per axis. For multichannel images, include a factor of 1 on the channel axis or use `resize_local_mean` instead.
- `preserve_range=True` keeps intensities on their native scale, but the result can still be floating point.
- `warp_coords` is the reusable helper when you need a custom coordinate grid rather than a named transform object.

## Custom coordinate fields and swirl

Use this path when you want a local deformation or a reusable custom map rather than a named transform class.

```python
import numpy as np
from skimage.transform import swirl, warp, warp_coords

swirled = swirl(gray, strength=2, radius=120, rotation=0)
coord_map = lambda coords: coords  # replace with a real coordinate transform
coords = warp_coords(coord_map, gray.shape)
custom = warp(gray, coords)
```

- `swirl` is a convenient tutorial-style warp for localized deformations.
- `warp_coords` turns a coordinate mapping into a reusable array that `warp` can consume.
- Use `matrix_transform` for point arrays, not images.

## Estimate a transform from point pairs

Use the transform class that matches the allowed degrees of freedom:

- `EuclideanTransform` for rigid motion.
- `SimilarityTransform` for rotation, translation, and scale.
- `AffineTransform` for shear plus the above.
- `ProjectiveTransform` for homographies.
- `PiecewiseAffineTransform`, `PolynomialTransform`, or `ThinPlateSplineTransform` when the warp is nonrigid.

```python
import numpy as np
from skimage import data
from skimage.transform import estimate_transform, matrix_transform, warp

text = data.text()

src = np.array([[0, 0], [0, 50], [300, 50], [300, 0]], dtype=float)
dst = np.array([[155, 15], [65, 40], [260, 130], [360, 95]], dtype=float)

tform = estimate_transform('projective', src, dst)
if not tform:
    raise RuntimeError(f'Failed estimation: {tform}')

warped = warp(text, tform, output_shape=(50, 300))
points = matrix_transform(src, tform.params)
```

Tips:

- If feature matching is noisy, do the matching and RANSAC in the `analysis` route first, then return here with the inlier point pairs.
- If estimation fails, check for repeated, collinear, or insufficient points.

## Radon and Hough workflows

### Tomography

`radon` and `iradon` use projection angles in degrees.

```python
import numpy as np
from skimage.data import shepp_logan_phantom
from skimage.transform import iradon, iradon_sart, order_angles_golden_ratio, radon, rescale

image = rescale(shepp_logan_phantom(), 0.4, mode='reflect', channel_axis=None)
theta = np.linspace(0.0, 180.0, max(image.shape), endpoint=False)
sinogram = radon(image, theta=theta)
recon = iradon(sinogram, theta=theta, filter_name='ramp')
refined = iradon_sart(sinogram, theta=theta, image=recon, clip=(0, 1))
ordered_indices = list(order_angles_golden_ratio(theta))
```

Useful controls:

- `filter_name` in `iradon` trades sharpness against noise.
- `iradon_sart` can take `projection_shifts=` and a previous reconstruction via `image=`.
- `order_angles_golden_ratio` is useful when acquisition order matters more than the angle set itself.
- The finite Radon helpers `frt2`/`ifrt2` exist for specialized discrete problems, but they are not the default tomography path.

### Straight lines, circles, and ellipses

`hough_line` and `probabilistic_hough_line` expect edge maps and use radians for `theta`.

```python
import numpy as np
from skimage.draw import circle_perimeter, ellipse_perimeter, line
from skimage.transform import (
    hough_circle,
    hough_circle_peaks,
    hough_ellipse,
    hough_line,
    hough_line_peaks,
    probabilistic_hough_line,
)

line_edges = np.zeros((120, 160), dtype=bool)
rr, cc = line(20, 15, 90, 140)
line_edges[rr, cc] = True
hspace, angles, dists = hough_line(line_edges)
accum, angles, dists = hough_line_peaks(hspace, angles, dists, min_distance=8, min_angle=10)
segments = probabilistic_hough_line(line_edges, threshold=10, line_length=20, line_gap=3, rng=0)

circle_edges = np.zeros((120, 160), dtype=bool)
rr, cc = circle_perimeter(70, 50, 18)
circle_edges[rr, cc] = True
radii = np.arange(10, 30, 2)
circle_space = hough_circle(circle_edges, radii)
accum, cx, cy, rad = hough_circle_peaks(circle_space, radii, total_num_peaks=3)

ellipse_edges = np.zeros((120, 160), dtype=bool)
rr, cc = ellipse_perimeter(80, 110, 16, 28)
ellipse_edges[rr, cc] = True
ellipses = hough_ellipse(ellipse_edges, threshold=10, accuracy=2)
if len(ellipses):
    ellipses.sort(order='accumulator')
    best = ellipses[-1]
```

Notes:

- `hough_line_peaks` suppresses nearby peaks using `min_distance` and `min_angle`.
- `hough_circle_peaks` returns `accum, cx, cy, rad`.
- `probabilistic_hough_line` returns endpoint pairs and accepts `rng=` for reproducibility.
- `hough_circle(..., full_output=True)` expands the accumulator when circle centers may lie outside the frame.

## Phase cross-correlation and log-polar registration

`phase_cross_correlation` returns the shift that should be applied to the moving image.

```python
import numpy as np
from scipy.ndimage import fourier_shift
from skimage import data
from skimage.registration import phase_cross_correlation

reference = data.camera()
shift = (-22.4, 13.32)
moving = np.fft.ifftn(fourier_shift(np.fft.fftn(reference), shift)).real

correction, error, diffphase = phase_cross_correlation(reference, moving, upsample_factor=100)
```

For masked or cropped data, pass valid-pixel masks instead of pre-masking the arrays:

```python
correction, error, diffphase = phase_cross_correlation(
    reference,
    moving,
    reference_mask=ref_mask,
    moving_mask=mov_mask,
)
```

For rotation and scale differences, use `warp_polar` first and then register the polar images:

```python
from skimage.transform import rotate, warp_polar

rotated = rotate(reference, 35)
ref_polar = warp_polar(reference, radius=reference.shape[0] // 2, scaling='log')
mov_polar = warp_polar(rotated, radius=reference.shape[0] // 2, scaling='log')
shift_polar, error, diffphase = phase_cross_correlation(ref_polar, mov_polar, normalization=None)
```

If translation also differs, work on a windowed FFT magnitude image first, then use the same log-polar + phase-correlation pattern.

## Optical flow registration

Use optical flow when the motion varies across the frame.

```python
import numpy as np
from skimage.color import rgb2gray
from skimage.data import stereo_motorcycle
from skimage.registration import optical_flow_tvl1
from skimage.transform import warp

image0, image1, _ = stereo_motorcycle()
image0 = rgb2gray(image0)
image1 = rgb2gray(image1)

v, u = optical_flow_tvl1(image0, image1)
row_coords, col_coords = np.meshgrid(np.arange(image0.shape[0]), np.arange(image0.shape[1]), indexing='ij')
registered = warp(image1, np.array([row_coords + v, col_coords + u]), mode='edge')
```

Guidance:

- `optical_flow_ilk` is faster and lighter; `optical_flow_tvl1` is usually smoother and more robust.
- The returned flow has one component per axis, so keep the row/column order straight when you warp the moving image.
- Inputs must be grayscale and floating point.
