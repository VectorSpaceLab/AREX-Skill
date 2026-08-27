# Visualization and Convolution Workflows

## Normalize an Astronomy Image

```python
import numpy as np
from astropy.visualization import ImageNormalize, ZScaleInterval, AsinhStretch

image = np.asarray(image, dtype=float)
norm = ImageNormalize(image, interval=ZScaleInterval(), stretch=AsinhStretch())
scaled = norm(image)
```

Inspect outliers and NaNs before choosing interval/stretches. Use fixed
`vmin`/`vmax` only when the science or display standard requires it.

## WCSAxes Plot

```python
import matplotlib.pyplot as plt

fig = plt.figure()
ax = fig.add_subplot(111, projection=wcs)
ax.imshow(image, origin="lower", norm=norm, cmap="gray")
ax.set_xlabel("RA")
ax.set_ylabel("Dec")
fig.savefig("image.png", dpi=150)
```

Validate the WCS in `wcs-nddata` first. Use temporary filenames until the user
approves an output path.

## Lupton RGB

```python
from astropy.visualization import make_lupton_rgb

rgb = make_lupton_rgb(red, green, blue, stretch=5, Q=8)
```

Ensure all channels have aligned shapes and comparable background treatment.

## FITS to Bitmap CLI

```bash
fits2bitmap --help
fits2bitmap image.fits -o image.png --stretch asinh
```

Use a temporary output path for trial runs. Check which HDU is selected with the
CLI help and task-specific flags.

## Direct Convolution

```python
import numpy as np
from astropy.convolution import Gaussian2DKernel, convolve

kernel = Gaussian2DKernel(x_stddev=1)
smoothed = convolve(image, kernel, boundary="extend", nan_treatment="interpolate")
assert smoothed.shape == image.shape
```

## FFT Convolution

```python
from astropy.convolution import convolve_fft

smoothed = convolve_fft(image, kernel, boundary="fill", fill_value=0.0,
                        nan_treatment="interpolate", allow_huge=False)
```

Use FFT convolution for large images/kernels, but keep `allow_huge=False` unless
the user explicitly accepts memory risk.
