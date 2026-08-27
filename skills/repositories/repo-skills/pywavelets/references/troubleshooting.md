# Troubleshooting

## When to read

Read this when PyWavelets import, build, transform, packet, or parameter-selection workflows fail.

## Install and import failures

### Symptom
- `ModuleNotFoundError: No module named 'pywt._extensions._pywt'`
- `ImportError` when importing `pywt`
- Editable install succeeds partially but the compiled extension is missing

### Likely causes
- The editable/source build was attempted without the Meson/Cython build tools.
- The local checkout has not been installed into the active Python environment.
- The build used an incompatible Python version or unsupported compiler setup.

### Recovery
- Install from PyPI with `python -m pip install PyWavelets` for users.
- For a source checkout, install build tools and then run `python -m pip install -e .`.
- Re-run the bundled smoke script to confirm that the C extension and public APIs import cleanly.

## Source-build problems

### Symptom
- Build errors during editable install or wheel build.

### Likely causes
- Missing `cython`, `meson-python`, `meson`, `ninja`, or a working C compiler.
- A Python version older than the one required by `pyproject.toml`.

### Recovery
- Check the current repository's `pyproject.toml` and install the build dependencies listed there.
- Keep build tooling minimal; do not install unrelated scientific extras just to get the compiled extension to build.

## Transform parameter failures

### Symptom
- `ValueError: Unknown mode name ...`
- `ValueError: Axis greater than data dimensions`
- `ValueError: At least one coefficient parameter must be specified.`
- `ValueError: Coefficients arrays must have the same size.`
- `ValueError: The mode parameter only takes values from: ...`

### Likely causes
- A `mode` string does not match `pywt.Modes.modes`.
- A transform axis is out of range for the input array.
- `idwt` was called with incompatible or missing coefficients.
- A thresholding mode name is invalid.

### Recovery
- Check `pywt.Modes.modes` before choosing a mode.
- Use `pywt.dwt_coeff_len(...)` or the inverse transform's own coefficient-shape rules before constructing coefficients by hand.
- For `idwt`, keep paired coefficient arrays aligned and use `None` only for one side at a time.

## CWT failures

### Symptom
- `ValueError: cwt() requires a continuous wavelet...`
- `ValueError: `scales` must only include positive values`
- `ValueError: Selected scale of ... too small.`

### Likely causes
- A discrete wavelet such as `db2` was passed to `cwt`.
- `scales` contains zero or negative values.
- The chosen scale is too small for the requested wavelet and data length.

### Recovery
- Use `pywt.wavelist(kind='continuous')` and choose a continuous family such as `morl`, `mexh`, `cmor`, `shan`, `fbsp`, or `cgau`.
- Keep scales positive and large enough to produce a valid filter length.
- For small-scale edge cases, increase the scale or use the documented sample data and plotting examples as guidance.

## Wavelet packet failures

### Symptom
- `IndexError: Path length is out of range.`
- `ValueError: Subnode name must be in [...]`
- `ValueError` from invalid axes or incompatible node shapes

### Likely causes
- The path walks past the packet tree's maximum decomposition level.
- A packet path uses an invalid child name for the tree type.
- The data shape and chosen axes do not match the decomposition constraints.

### Recovery
- Inspect `maxlevel` before descending further.
- Use `WaveletPacket` for 1D paths, `WaveletPacket2D` for `a/h/v/d`, and `WaveletPacketND` for generalized axes-based trees.
- Use the dedicated packet sub-skill's route and packet examples rather than trying to infer valid paths from memory.

## Data and demo helper failures

### Symptom
- `ValueError` from `demo_signal` about `n` or signal names.
- Unexpected shape from a bundled data helper.

### Likely causes
- `demo_signal('gabor')` or `demo_signal('sineoneoverx')` was called with `n` instead of `None`.
- A required signal length was omitted.

### Recovery
- Read `references/data-and-demo-signals.md` and use `demo_signal('list')` to confirm the valid names and length rules.
