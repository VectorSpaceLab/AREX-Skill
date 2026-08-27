# Wavelet and CWT API Reference

## When to read

Read this when you need the verified wavelet constructors, catalog helpers, frequency conversion helpers, or CWT call signature.

## Catalog helpers

- `families(short=True)`
- `wavelist(family=None, kind='all')`

The live package reports these families: `haar`, `db`, `sym`, `coif`, `bior`, `rbio`, `dmey`, `gaus`, `mexh`, `morl`, `cgau`, `shan`, `fbsp`, and `cmor`.

## Constructors

- `Wavelet(name[, filter_bank=None])`
- `ContinuousWavelet(name, dtype)`
- `DiscreteContinuousWavelet(name, filter_bank=None)`

Verified live behavior:

- `DiscreteContinuousWavelet(name)` resolves to a discrete or continuous wavelet object depending on the name.
- `Wavelet` exposes discrete-filter properties such as `dec_lo`, `dec_hi`, `rec_lo`, `rec_hi`, `dec_len`, `rec_len`, `orthogonal`, `biorthogonal`, `symmetry`, `family_name`, `short_family_name`, `vanishing_moments_phi`, and `vanishing_moments_psi`.
- `ContinuousWavelet` exposes `center_frequency`, `bandwidth_frequency`, `lower_bound`, `upper_bound`, `complex_cwt`, and `fbsp_order` where relevant.

## Wavelet-function helpers

- `Wavelet.wavefun(level=8)`
- `ContinuousWavelet.wavefun(level=8, length=None)`
- `integrate_wavelet(wavelet, precision=8)`
- `central_frequency(wavelet, precision=8)`
- `scale2frequency(wavelet, scale, precision=8)`
- `frequency2scale(wavelet, freq, precision=8)`
- `qmf(filt)`
- `orthogonal_filter_bank(scaling_filter)`

## Continuous wavelet transform

- `cwt(data, scales, wavelet, sampling_period=1.0, method='conv', axis=-1, *, precision=12)`

The live code requires:

- a continuous wavelet object or name
- positive scales
- `method='conv'` or `method='fft'`

## Bundled sample access

- `pywt.data.nino()` returns a `(time, sst)` pair suitable for CWT smoke checks.
- `pywt.data.demo_signal(name='Bumps', n=None)` returns a named 1D test signal family.
- `pywt.data.demo_signal('list')` returns the available demo signal names.

## Output-shape reminders

- `wavefun` on a discrete orthogonal wavelet returns `(phi, psi, x)`.
- `wavefun` on a discrete biorthogonal wavelet returns `(phi_d, psi_d, phi_r, psi_r, x)`.
- `wavefun` on a continuous wavelet returns `(psi, x)`.
- `cwt` returns `(coefs, frequencies)` with `coefs.shape[0] == len(scales)`.
