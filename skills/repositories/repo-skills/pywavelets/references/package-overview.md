# Package Overview

## When to read

Read this first when you need a quick map of the public `pywt` surface, the bundled example data, or the source-build expectations for this checkout.

## Public surface

PyWavelets exposes its main functionality from the top-level `pywt` package:

- `Wavelet`, `ContinuousWavelet`, and `DiscreteContinuousWavelet`
- `Modes` and `Modes.modes`
- Discrete transforms: `dwt`, `idwt`, `wavedec`, `waverec`, `dwt2`, `idwt2`, `wavedec2`, `waverec2`, `dwtn`, `idwtn`, `wavedecn`, `waverecn`
- Stationary / multiresolution transforms: `swt`, `iswt`, `swt2`, `iswt2`, `swtn`, `iswtn`, `mra`, `mra2`, `mran`, `imra`, `imra2`, `imran`
- Coefficient helpers: `coeffs_to_array`, `array_to_coeffs`, `ravel_coeffs`, `unravel_coeffs`, `wavedecn_size`, `wavedecn_shapes`
- Wavelet families and helpers: `families`, `wavelist`, `integrate_wavelet`, `central_frequency`, `scale2frequency`, `frequency2scale`, `qmf`, `orthogonal_filter_bank`
- Thresholding and padding: `threshold`, `threshold_firm`, `pad`
- Packet trees: `WaveletPacket`, `WaveletPacket2D`, `WaveletPacketND`
- Bundled data accessors under `pywt.data`

## Source-build expectations for this checkout

The current repository is built with Meson/Cython rather than a pure Python fallback. The editable inspection used for this skill confirmed that the checkout builds with:

- Python 3.12+
- `numpy`
- `cython`
- `meson-python`
- `meson`
- `ninja`
- a working C compiler

The top-level `pyproject.toml` is the source of truth for the current checkout's build requirements. If the editable import fails with a missing compiled extension, consult `references/troubleshooting.md`.

## Sample data and demos

The package ships small example arrays under `pywt.data` so future agents can use deterministic smoke fixtures without opening the original repository:

- `aero()`, `ascent()`, `camera()` for 512×512 grayscale images
- `ecg()` for a 1024-point signal
- `nino()` for a standardized monthly SST signal pair
- `demo_signal(name='Bumps', n=None)` for named 1D test signals

See `data-and-demo-signals.md` for the exact smoke-oriented use cases.

## Choosing the workflow route

- Use `discrete-transforms` for signal/image transforms, coefficient packaging, SWT, MRA, padding, and thresholding.
- Use `wavelets-and-cwt` for wavelet catalogs, custom wavelets, wavefun, and continuous transforms.
- Use `wavelet-packets` for tree navigation and reconstruction.
