---
name: wavelets-and-cwt
description: "Routes PyWavelets users through wavelet-family inspection, custom
  wavelets, wavefun output, scale conversion, and continuous wavelet
  transforms."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Wavelets and CWT

Use this sub-skill when the task is about the wavelet catalog, custom wavelet construction, wavelet-function inspection, or the continuous wavelet transform.

## Route here when the task asks for

- `families()` or `wavelist()`
- `Wavelet`, `ContinuousWavelet`, or `DiscreteContinuousWavelet`
- custom wavelets built from a `filter_bank`
- `wavefun`, `integrate_wavelet`, `central_frequency`, `scale2frequency`, or `frequency2scale`
- `cwt` and continuous-wavelet scaleograms
- bundled demo signals such as `pywt.data.demo_signal(...)` or the sample `pywt.data.nino()` time series

## Route elsewhere when the task is about

- decimated transforms, SWT, MRA, coefficient packing, thresholding, padding, or fully separable transforms: go to `../discrete-transforms/SKILL.md`
- packet trees, packet path traversal, or packet reconstruction: go to `../wavelet-packets/SKILL.md`

## Start here

- Read `references/api-reference.md` for the verified constructor signatures and the live `cwt` call shape.
- Read `references/workflows.md` for recipes that choose a wavelet, inspect `wavefun`, and compute a CWT.
- Read `references/troubleshooting.md` when wavelet names, continuous/dtype selection, or CWT scale/method choices fail.
- Run `../../scripts/inspect_wavelet.py` when you want a safe, no-plot inspection of a discrete or continuous wavelet.
- Run `../../scripts/check_pywavelets_install.py` when you want a broader smoke check that also exercises the core transform stack.

## Common workflow anchors

- Use `pywt.families()` to group the built-in discrete wavelet families.
- Use `pywt.wavelist(kind='continuous')` to choose a continuous wavelet for `cwt`.
- Use `pywt.DiscreteContinuousWavelet(name)` when you need a one-call resolver for discrete or continuous names.
- Use `pywt.ContinuousWavelet(name, dtype)` when you want to force a continuous wavelet object directly.
- Use `pywt.scale2frequency(...)` and `pywt.frequency2scale(...)` to convert between CWT scale and normalized frequency.
- Use `pywt.data.nino()` or `pywt.data.demo_signal('Doppler', n)` for a small real-valued CWT input.

## Important package facts

- The live package accepts continuous wavelets such as `morl`, `mexh`, `cmor`, `shan`, `fbsp`, and `cgau` for `cwt`.
- The live `cwt` implementation requires a continuous wavelet object and positive scales.
- The code path currently accepts `method='conv'` and `method='fft'`; do not rely on `auto` as a runtime option.
- `wavefun` returns 2, 3, or 5 outputs depending on whether the wavelet is continuous, orthogonal, or biorthogonal.

## What to expect from the references

- `references/api-reference.md` records the verified public constructors, helper functions, and `cwt` arguments.
- `references/workflows.md` shows how to inspect wavelet objects and compute a scaleogram without guessing parameters.
- `references/troubleshooting.md` covers the common continuous-wavelet, dtype, parameter-string, and scale errors.
