# Preprocessing troubleshooting

- **Filter/resample errors**: check Nyquist limits, positive sampling rates,
  channel types, and whether the data are preloaded. A high cutoff after
  resampling is invalid; recalculate all sample-based parameters.
- **Callable receives the wrong object**: choose `apply_on_array=True` only for
  a function accepting an array (often with channel-wise behavior); use false
  for an MNE `Raw`/`Epochs` method. Test the callable on one item first.
- **Missing channels or montage**: pick/rename channels consistently across
  recordings and set a montage before topographic operations. Never silently
  reorder channels to fit a model.
- **Unexpected mutation**: many MNE operations are in-place. Keep a copy for
  comparisons and record the ordered preprocessing list with the saved result.
- **Parallel hangs or memory spikes**: reproduce with `n_jobs=1`, smaller
  recordings, and `preload=True`; lower workers or use serialized `save_dir`
  processing after correctness is established.
- **Stale output directory**: use a new cache directory or confirm
  `overwrite=True` is intentional and that preprocessing parameters match.
- **EEGPrep import failure**: install the EEGPrep extra only for that route and
  retain a standard MNE preprocessing fallback when the optional package is
  unavailable.
