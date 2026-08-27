# Modeling, Stats, and Time Series Workflows

## Fit a Simple Model

```python
import numpy as np
from astropy.modeling import fitting, models

x = np.arange(6.0)
y = 2.0 * x + 1.0
model = models.Linear1D()
fitter = fitting.LinearLSQFitter()
fit = fitter(model, x, y)
assert abs(fit.slope.value - 2.0) < 1e-12
```

For nonlinear models, initialize parameters close to the expected solution and
inspect residuals.

## Fit with Outlier Rejection

```python
import numpy as np
from astropy.stats import sigma_clip

mask = sigma_clip(y, sigma=3).mask
fit = fitter(model, x[~mask], y[~mask])
```

For model-specific iterative outlier rejection, combine Astropy modeling with a
clear clipping policy and validation plot/statistic.

## Robust Summary Statistics

```python
from astropy.stats import mad_std, sigma_clipped_stats

mean, median, std = sigma_clipped_stats(data, sigma=3)
robust_sigma = mad_std(data)
```

Record axis behavior and whether masks/NaNs were ignored.

## Lomb-Scargle Periodogram

```python
from astropy import units as u
from astropy.timeseries import LombScargle

t = [1, 2, 3, 4, 5] * u.day
y = [1.0, 0.0, 1.0, 0.0, 1.0]
freq = [0.1, 0.2, 0.3] / u.day
power = LombScargle(t, y).power(freq)
```

Use frequency units and choose normalization/false-alarm methods intentionally.

## Box Least Squares

```python
from astropy.timeseries import BoxLeastSquares

bls = BoxLeastSquares(t, y)
result = bls.power(period=[2, 3] * u.day, duration=0.2 * u.day)
```

Keep grid sizes bounded for interactive or agent-driven tasks.

## TimeSeries Container

```python
from astropy import units as u
from astropy.time import Time
from astropy.timeseries import TimeSeries

ts = TimeSeries(time=Time(["2024-01-01", "2024-01-02"]), data={"flux": [1.0, 1.2] * u.Jy})
```

Route file format questions back to the table/I/O sub-skill.
