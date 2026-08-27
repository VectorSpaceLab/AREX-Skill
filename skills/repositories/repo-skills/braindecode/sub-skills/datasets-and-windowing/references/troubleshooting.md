# Dataset troubleshooting

- **Unexpected number of windows**: compute `window_size_samples` and stride from
  the current `sfreq`; inspect whether the last partial window is dropped. For
  a short synthetic fixture, enumerate crop indices and compare against the
  expected half-open intervals.
- **`KeyError` or empty targets**: inspect `description`, event IDs, annotation
  mappings, and the selected target column. Print one raw/epoch object and one
  dataset item before fitting.
- **MNE channel or sampling mismatch**: verify channel names/types, order,
  montage, and `raw.info["sfreq"]` for every recording before concatenation.
  Resample first, then recalculate all sample-based window parameters.
- **Serialization failure or stale results**: use a new writable directory,
  check free space and permissions, and ensure the saved metadata records the
  same preprocessing and target selection. Do not overwrite a result from a
  different parameterization.
- **Optional integration import/network error**: install only the named extra,
  verify cache/credentials and consent, then retry one subject/file. A local
  synthetic MNE fixture is the correct fallback for API smoke checks.
- **Leakage in evaluation**: split by subject/session or recording description
  before windowing or before concatenating overlapping windows; do not use a
  random window-level split for cross-recording claims.
