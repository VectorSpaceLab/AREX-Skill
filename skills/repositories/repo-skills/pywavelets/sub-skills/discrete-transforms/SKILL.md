---
name: discrete-transforms
description: "Routes PyWavelets users through DWT, IDWT, multilevel transforms,
  SWT, MRA, coefficient packing, thresholding, padding, and fully separable
  transforms."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Discrete Transforms

Use this sub-skill for the core `pywt` transform stack: decimated DWT/IDWT, 2D and ND transforms, coefficient packing, stationary wavelets, multiresolution analysis, thresholding, signal-extension modes, padding, and fully separable transforms.

## Route here when the task asks for

- `dwt`, `idwt`, `wavedec`, `waverec`, `dwt2`, `idwt2`, `wavedec2`, `waverec2`
- `dwtn`, `idwtn`, `wavedecn`, `waverecn`
- `swt`, `iswt`, `swt2`, `iswt2`, `swtn`, `iswtn`
- `mra`, `mra2`, `mran`, `imra`, `imra2`, `imran`
- `coeffs_to_array`, `array_to_coeffs`, `ravel_coeffs`, `unravel_coeffs`, `wavedecn_size`, `wavedecn_shapes`
- `threshold`, `threshold_firm`, `pad`, `Modes.modes`, `dwt_coeff_len`, `dwt_max_level`, `dwtn_max_level`
- `fswavedecn`, `fswaverecn`, or `FswavedecnResult`

## Route elsewhere when the task is about

- wavelet catalogs, custom wavelets, `wavefun`, `central_frequency`, `scale2frequency`, or `cwt`: go to `../wavelets-and-cwt/SKILL.md`
- packet trees, node paths, packet reconstruction, or `WaveletPacket*`: go to `../wavelet-packets/SKILL.md`

## Start here

- Read `references/workflows.md` for concrete transform recipes.
- Read `references/api-reference.md` when you need the verified signatures or result-shape rules.
- Read `references/troubleshooting.md` when modes, axes, coefficient shapes, or SWT/MRA constraints fail.
- Run `../../scripts/check_pywavelets_install.py` when you want a quick smoke check that covers the core transform stack.

## Common workflow anchors

- Use `pywt.Modes.modes` to confirm supported extension modes before choosing `mode=`.
- For 1D smoke checks, `db1` and `symmetric` are the safest defaults.
- For SWT and SWT-based MRA, prefer `mode='periodization'` and a signal length that is a multiple of `2**level`.
- For `waverec` and `waverecn`, zero arrays are the safe way to omit coefficients; `None` is not the general replacement mechanism.
- For coefficient packing, prefer `coeffs_to_array` / `array_to_coeffs` when you need a shaped array and `ravel_coeffs` / `unravel_coeffs` when you need a flat vector.
- For fully separable transforms, inspect the returned `FswavedecnResult` object instead of treating it as a raw coefficient list.

## Useful bundled data

- `pywt.data.ecg()` is a compact 1D signal for DWT, SWT, and thresholding examples.
- `pywt.data.camera()` is a compact 2D image for `dwt2`, `wavedec2`, `dwtn`, `wavedecn`, `swt2`, and packet-adjacent smoke checks.
- `pywt.data.nino()` is useful when a transform recipe needs a small real-valued signal with a time axis.

## What to expect from the references

- `references/workflows.md` gives copyable recipes for 1D, 2D, ND, SWT, MRA, coefficient packing, thresholding, padding, and fully separable transforms.
- `references/api-reference.md` lists the verified function signatures and the major return-shape conventions.
- `references/troubleshooting.md` explains the common error fragments and recovery steps for transform and coefficient workflows.
