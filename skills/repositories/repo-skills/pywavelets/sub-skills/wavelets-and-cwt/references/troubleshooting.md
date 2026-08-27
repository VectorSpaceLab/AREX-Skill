# Wavelet and CWT Troubleshooting

## When to read

Read this when wavelet construction, `wavefun`, frequency conversion, or CWT calls fail.

## Discrete vs continuous wavelet confusion

### Symptoms
- `ValueError: cwt() requires a continuous wavelet ...`
- The wavelet name works for `Wavelet(...)` but not for `cwt(...)`

### Causes
- A discrete wavelet such as `db2` or `haar` was passed to `cwt`.

### Recovery
- Choose a continuous wavelet from `pywt.wavelist(kind='continuous')`, such as `morl`, `mexh`, `cmor1.5-1.0`, `shan1-1`, or `fbsp2-1-1`.
- If you only need transform coefficients for a discrete wavelet family, route back to the discrete-transforms sub-skill.

## Parameter-string failures

### Symptoms
- `ValueError` when constructing `cmor`, `shan`, or `fbsp` names.
- `FutureWarning` for the bare family names `cmor`, `shan`, or `fbsp`.

### Causes
- The parameterized continuous-wavelet name is malformed.
- The family name was used without its required numeric parameters.

### Recovery
- Use the documented forms, e.g. `cmor1.5-1.0`, `shan1-1.5`, or `fbsp2-1.5-1.0`.
- For a generic family listing, call `pywt.wavelist(kind='continuous')` instead of guessing.

## dtype failures

### Symptoms
- `ValueError` when constructing a continuous wavelet with the wrong dtype.

### Causes
- The requested `dtype` is not one of the supported floating-point dtypes.

### Recovery
- Use `float32` or `float64` unless you have a documented reason to choose another supported floating-point dtype.

## CWT scale and method failures

### Symptoms
- `ValueError: `scales` must only include positive values`
- `ValueError: Selected scale of ... too small.`
- `ValueError` for an unexpected `method` value

### Causes
- `scales` contains zero or negative values.
- The scale is too small for the requested wavelet and signal length.
- The live code only accepts `method='conv'` or `method='fft'`.

### Recovery
- Keep all scales positive.
- Increase the scale or shorten the signal if the scale is too small.
- Do not rely on `method='auto'` in the live package even if an older docstring mentions it.

## Wavefun output confusion

### Symptoms
- A caller expects the wrong number of return values from `wavefun`.

### Causes
- The output arity depends on whether the wavelet is continuous, orthogonal, or biorthogonal.

### Recovery
- Continuous wavelets return `(psi, x)`.
- Orthogonal discrete wavelets return `(phi, psi, x)`.
- Biorthogonal discrete wavelets return `(phi_d, psi_d, phi_r, psi_r, x)`.
- Use `../../scripts/inspect_wavelet.py` to see the arity without guessing.

## Next helper to run

- Run `../../scripts/inspect_wavelet.py <wavelet-name>` for a no-plot object summary.
- Run `../../scripts/check_pywavelets_install.py` if you also want to confirm the broader package smoke path.
