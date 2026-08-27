# Bundled Data and Demo Signals

## When to read

Read this when you need safe sample inputs for smoke checks, docs examples, or notebook-free reproductions.

## Bundled arrays

These arrays live in `pywt.data` and are safe, deterministic smoke fixtures:

- `pywt.data.aero()` → 512×512 grayscale image
- `pywt.data.ascent()` → 512×512 grayscale image
- `pywt.data.camera()` → 512×512 grayscale image
- `pywt.data.ecg()` → 1024-point ECG signal
- `pywt.data.nino()` → `(time, sst)` with 264 samples after aggregation

The bundled datasets are loaded from small package resources, so they do not require network access.

## Demo signals

`pywt.data.demo_signal(name='Bumps', n=None)` returns a 1D synthetic test signal family.

Useful facts from the live package:

- `pywt.data.demo_signal('list')` returns the available names.
- The signal names are case-insensitive.
- Most signals require an explicit `n`.
- `Gabor` and `sineoneoverx` use a fixed internal length and require `n=None`.
- A bad `n` or an unknown signal name raises `ValueError`.

## Common smoke choices

- Use `ecg()` for short 1D transform and thresholding checks.
- Use `camera()` for 2D DWT, SWT, and packet checks.
- Use `nino()` for CWT checks with a real-valued time axis.
- Use `demo_signal('Doppler', 1024)` or `demo_signal('Bumps', 1024)` for synthetic 1D examples.

## No-surprises policy

These fixtures are intentionally small enough to use in bundled scripts and verification cases without depending on the original checkout or any external data download.
