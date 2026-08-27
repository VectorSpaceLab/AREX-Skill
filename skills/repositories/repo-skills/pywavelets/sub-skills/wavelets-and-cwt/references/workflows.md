# Wavelet and CWT Workflows

## When to read

Read this when you need a practical recipe for choosing a wavelet, inspecting its properties, using `wavefun`, or computing a CWT.

## Choose a wavelet family

1. Start with `pywt.families()` to see the family names.
2. Use `pywt.wavelist(family)` when you want the discrete names in one family.
3. Use `pywt.wavelist(kind='continuous')` when you need a CWT-compatible name.
4. For quick experiments, `db1`, `db2`, `morl`, and `cmor1.5-1.0` are the safest defaults.

## Inspect a wavelet object

Use `../../scripts/inspect_wavelet.py` when you want the properties without plotting.

```python
import pywt
w = pywt.Wavelet('db3')
print(w)
phi, psi, x = w.wavefun(level=5)
```

For continuous wavelets:

```python
cw = pywt.ContinuousWavelet('cmor1.5-1.0')
psi, x = cw.wavefun(length=128)
```

## Build a custom wavelet

- For a discrete custom wavelet, pass a four-filter `filter_bank` to `Wavelet(...)`.
- For a name that could resolve to either discrete or continuous, use `DiscreteContinuousWavelet(...)`.
- For a continuous wavelet with a dtype constraint, use `ContinuousWavelet(name, dtype)`.

Example:

```python
from math import sqrt
import pywt

fb = ([sqrt(2)/2, sqrt(2)/2], [-sqrt(2)/2, sqrt(2)/2],
      [sqrt(2)/2, sqrt(2)/2], [sqrt(2)/2, -sqrt(2)/2])
custom = pywt.Wavelet('My Haar', filter_bank=fb)
```

## Compute a CWT

1. Pick a continuous wavelet from `pywt.wavelist(kind='continuous')`.
2. Choose positive scales.
3. If the signal is real-valued and the example is synthetic, `pywt.data.nino()` or `pywt.data.demo_signal('Doppler', n)` are convenient.
4. Call `pywt.cwt(data, scales, wavelet, sampling_period)`.
5. Convert between scale and normalized frequency with `scale2frequency` and `frequency2scale` when needed.

Example:

```python
import numpy as np
import pywt

time, sst = pywt.data.nino()
scales = np.arange(1, 32)
coefs, freqs = pywt.cwt(sst, scales, 'cmor1.5-1.0', time[1] - time[0])
```

## Common inspection patterns

- Use `central_frequency` when you only need the normalized center frequency.
- Use `integrate_wavelet` when you want the integrated wavelet used by the CWT implementation.
- Use `wavefun` to compare the discrete and continuous shapes without drawing a plot.

## CWT smoke-check pattern

For a quick no-network smoke check, use `morl` or `cmor1.5-1.0` on a small real-valued signal and assert the coefficient shape rather than trying to reproduce a publication-grade scaleogram.
