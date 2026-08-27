# Discrete Transform Troubleshooting

## When to read

Read this when DWT, IDWT, multilevel, SWT, MRA, coefficient packing, thresholding, padding, or fully separable workflows fail.

## `mode` and axis errors

### Symptoms
- `ValueError: Unknown mode name ...`
- `ValueError: Axis greater than data dimensions`
- `ValueError: The axes passed to ... must be unique.`
- `ValueError: The length of axes doesn't match ...`

### Causes
- The mode string does not match `pywt.Modes.modes`.
- The requested axis is out of range or duplicated.
- The transform was computed over a subset of axes but the pack/unpack call omitted the same axes.

### Recovery
- Re-read `references/api-reference.md` and confirm the mode or axes signature.
- Use `pywt.Modes.modes` before choosing a mode string.
- Keep the same `axes=` value through both the forward and inverse path.

## Coefficient-shape mismatches

### Symptoms
- `ValueError: Coefficients arrays must have the same size.`
- `ValueError: Unexpected detail coefficient type ...`
- `ValueError: incompatible coefficient array sizes`
- `ValueError: input must be a list of coefficients from wavedecn`

### Causes
- Hand-built coefficient lists do not match the original transform's shapes.
- `waverec`/`waverecn` were given the wrong coefficient-list flavor.
- `coeffs_to_array` or `ravel_coeffs` was asked to decode a coefficient tree with the wrong layout.

### Recovery
- Use the helper that matches the original forward transform: `wavedec*` -> `waverec*`, `wavedecn` -> `waverecn`.
- Use `coeffs_to_array` / `array_to_coeffs` or `ravel_coeffs` / `unravel_coeffs` as a pair.
- When a coefficient array is intentionally omitted from `waverec` or `waverecn`, replace it with zeros of the correct shape rather than `None`.

## SWT and MRA constraints

### Symptoms
- `ValueError` about `periodization` when using SWT-based MRA.
- `ValueError` or warnings about signal length and levels.
- Reconstruction changes when the signal length is not a multiple of `2**level`.

### Causes
- SWT-based workflows require `periodization`.
- The transformed axis length is not compatible with the chosen decomposition depth.
- The level requested exceeds the maximum supported by the input size.

### Recovery
- For SWT or MRA, choose `mode='periodization'` and verify the input length first.
- For decimated transforms, inspect `dwt_max_level`, `dwtn_max_level`, or `swt_max_level` before choosing a level.
- If you need a softer boundary treatment, use `pad` first and then transform the padded array intentionally.

## Fully separable transform issues

### Symptoms
- `ValueError` about `levels` length or axis validity.
- The reconstructed array shape does not match the input shape.

### Causes
- `levels` does not match the number of transformed axes.
- The axes tuple includes an invalid or repeated axis.

### Recovery
- Match the `levels` tuple length to the number of axes you pass.
- Use the `FswavedecnResult` object directly; it stores the coefficient slices and axis metadata needed for reconstruction.

## Thresholding and padding issues

### Symptoms
- `ValueError: The mode parameter only takes values from ...`
- Complex-valued data fails with `greater` or `less`.
- Padding with a negative width fails.

### Causes
- The threshold mode is invalid.
- `greater` and `less` only support real arrays.
- `pad_widths` was negative.

### Recovery
- Use `soft`, `hard`, `garrote`/`garotte`, `greater`, or `less` only.
- Switch to `soft` or `hard` for complex data.
- Keep `pad_widths >= 0` and let `pad` mirror the transform boundary rules.

## Next helper to run

- Run `../../scripts/check_pywavelets_install.py` if you want to confirm that the installed package and core transforms still work on a tiny fixture.
