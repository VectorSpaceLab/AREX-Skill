# Discrete Transform API Reference

## When to read

Read this when you need the verified transform signatures, return conventions, or coefficient-shape rules for the decimated, stationary, multiresolution, coefficient-packaging, or fully separable workflows.

## Core signatures

### 1D decimated transforms

- `dwt(data, wavelet, mode='symmetric', axis=-1)`
- `idwt(cA, cD, wavelet, mode='symmetric', axis=-1)`
- `wavedec(data, wavelet, mode='symmetric', level=None, axis=-1)`
- `waverec(coeffs, wavelet, mode='symmetric', axis=-1)`
- `dwt_coeff_len(data_len, filter_len, mode)`
- `dwt_max_level(data_len, filter_len)`

### 2D decimated transforms

- `dwt2(data, wavelet, mode='symmetric', axes=(-2, -1))`
- `idwt2(coeffs, wavelet, mode='symmetric', axes=(-2, -1))`
- `wavedec2(data, wavelet, mode='symmetric', level=None, axes=(-2, -1))`
- `waverec2(coeffs, wavelet, mode='symmetric', axes=(-2, -1))`

### ND decimated transforms

- `dwtn(data, wavelet, mode='symmetric', axes=None)`
- `idwtn(coeffs, wavelet, mode='symmetric', axes=None)`
- `wavedecn(data, wavelet, mode='symmetric', level=None, axes=None)`
- `waverecn(coeffs, wavelet, mode='symmetric', axes=None)`
- `dwtn_max_level(shape, wavelet, axes=None)`

### Fully separable transforms

- `fswavedecn(data, wavelet, mode='symmetric', levels=None, axes=None)`
- `fswaverecn(fswavedecn_result)`
- `FswavedecnResult` exposes `coeffs`, `coeff_slices`, `approx`, `detail_keys()`, `wavelets`, `modes`, `axes`, `levels`, `ndim`, and `ndim_transform`

### Stationary transforms and MRA

- `swt(data, wavelet, level=None, start_level=0, axis=-1, trim_approx=False, norm=False)`
- `iswt(coeffs, wavelet, norm=False, axis=-1)`
- `swt2(data, wavelet, level, start_level=0, axes=(-2, -1), trim_approx=False, norm=False)`
- `iswt2(coeffs, wavelet, norm=False, axes=(-2, -1))`
- `swtn(data, wavelet, level, start_level=0, axes=None, trim_approx=False, norm=False)`
- `iswtn(coeffs, wavelet, axes=None, norm=False)`
- `swt_max_level(n)`
- `mra(data, wavelet, level=None, axis=-1, transform='swt', mode='periodization')`
- `mra2(data, wavelet, level=None, axes=(-2, -1), transform='swt2', mode='periodization')`
- `mran(data, wavelet, level=None, axes=None, transform='swtn', mode='periodization')`
- `imra(mra_coeffs)`, `imra2(mra_coeffs)`, `imran(mra_coeffs)`

### Coefficient packing

- `coeffs_to_array(coeffs, padding=0, axes=None)`
- `array_to_coeffs(arr, coeff_slices, output_format='wavedecn')`
- `ravel_coeffs(coeffs, axes=None)`
- `unravel_coeffs(arr, coeff_slices, coeff_shapes, output_format='wavedecn')`
- `wavedecn_shapes(shape, wavelet, mode='symmetric', level=None, axes=None)`
- `wavedecn_size(shapes)`

### Thresholding and padding

- `threshold(data, value, mode='soft', substitute=0)`
- `threshold_firm(data, value_low, value_high)`
- `pad(x, pad_widths, mode)`
- `Modes.modes` returns the supported extension modes in the live package order.

## Return-shape reminders

- `wavedec` returns `[cA_n, cD_n, ..., cD1]`.
- `wavedec2` returns `[cA_n, (cH_n, cV_n, cD_n), ..., (cH_1, cV_1, cD_1)]`.
- `wavedecn` returns `[cA_n, {detail_dict_n}, ..., {detail_dict_1}]`.
- `coeffs_to_array` and `ravel_coeffs` accept the decimated coefficient-list formats and convert them into arrays plus slice metadata.
- `waverec` and `waverecn` do not use `None` as a general omission marker; zero arrays are the safe omission mechanism.
- `fswavedecn` returns an `FswavedecnResult` object rather than a coefficient list.

## Verified backend assumptions

Everything in this repository is CPU-backed. No accelerator backend is required for the discrete transform APIs.
