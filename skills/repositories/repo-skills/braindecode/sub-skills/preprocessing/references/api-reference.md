# Preprocessing API reference

`Preprocessor(fn, *, apply_on_array=True, **kwargs)` accepts an MNE method name
or callable. `apply_on_array=True` applies a callable to NumPy data; set it
false when the callable expects an MNE object. `preprocess(concat_ds,
preprocessors, n_jobs=1, save_dir=None, overwrite=False, ...)` applies the
ordered list to the recordings or windows.

Dedicated classes wrap common operations such as `Pick`, `Resample`, `Filter`,
`Scale`, `Crop`, `SetEEGReference`, `SetMontage`, `RenameChannels`, and
`SetAnnotations`. Prefer a typed class when it expresses units and validation
clearly; use a callable for a genuinely custom operation.

A preprocessing list is ordered. For example, pick channels -> set montage ->
resample -> filter -> scale -> window. Window-level normalization belongs after
window creation when it must not use statistics from other trials.
