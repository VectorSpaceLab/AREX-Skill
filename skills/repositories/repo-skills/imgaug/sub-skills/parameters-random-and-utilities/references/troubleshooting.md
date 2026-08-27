# Parameters, RNG, and utility troubleshooting

## NumPy 2 import failure

**Symptom:** `AttributeError: np.sctypes was removed` or import failure during `import imgaug`.

**Cause:** imgaug 0.4.0 reads `np.sctypes` during import.

**Recovery:** install `numpy<2` for this package release and rerun the environment check.

## Deprecated randomness arguments

**Symptom:** warnings mention `random_state` or `deterministic`.

**Cause:** these legacy arguments still appear in signatures but are deprecated.

**Recovery:** prefer `seed=` at construction time and `to_deterministic()` for replay.

## Parameter range surprise

**Symptom:** a tuple/list parameter samples values outside what the user expected.

**Cause:** different parameter normalizers interpret scalars, tuples, lists, and `StochasticParameter` objects according to the target augmenter parameter.

**Recovery:** use explicit `imgaug.parameters` objects such as `Clip(Normal(...), min, max)` when the distribution must be precise.

## Dtype clipping or rounding surprise

**Symptom:** values are clipped, rounded, or arrays change dtype unexpectedly.

**Cause:** dtype conversion helpers are range-aware and clip/round by default.

**Recovery:** validate value ranges before conversion and document whether clipping/rounding is acceptable.

## Sample data cannot load

**Symptom:** quokka image/data functions fail.

**Cause:** package data was not included in the installation or the environment is mixing an incomplete checkout with an installed package.

**Recovery:** reinstall the public `imgaug` package or run the root environment check to confirm the import source and distribution metadata.

## Display fails on headless systems

**Symptom:** `ia.imshow` or Matplotlib backend errors occur on servers/CI.

**Recovery:** use `ia.draw_grid` plus `imageio.imwrite` to save a file instead of showing a window.
