# Model Overview

## Supported versions

| Version | Typical use | CPU sample limit |
| --- | --- | --- |
| `v2` | Legacy checkpoint family | 1000 |
| `v2.5` | Older gated family | 1000 |
| `v2.6` | Transitional gated family | 1000 |
| `v3` | Current default family | 5000 |

## Model selection

- `ModelVersion.V3` is the default version in current installs.
- `create_default_for_version(version, **overrides)` picks the correct estimator
  defaults for a pinned version.
- `model_path='auto'` resolves to the version-appropriate default checkpoint.
- `model_path` can also be a path, a list of paths, or a model-spec object.

## Cache and path resolution

- Bare filenames are resolved against the current working directory first and
  then the TabPFN cache directory.
- `TABPFN_MODEL_CACHE_DIR` overrides the cache root.
- `TABPFN_MODEL_CACHE_SIZE` enables the built-model cache and should only be set
  when repeated fits or repeated load/build cycles are expected.

## How to route version questions

- For selection of estimator defaults, see `tabular-prediction`.
- For download, cache, and checkpoint behavior, see `model-management`.
