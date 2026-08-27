# Dataset-management API reference

Back to [dataset-management](../SKILL.md). The signatures below were checked
against the inspected MOABB 1.5 development package. Treat the installed
package version as authoritative if a later release differs.

## Public dataset classes

| API | Signature / important defaults | Result and failure behavior |
|---|---|---|
| `BaseDataset` | `BaseDataset(subjects, sessions_per_subject, events, code, interval, paradigm, doi=None, unit_factor=1e6, *, selected_subjects=None, selected_sessions=None, return_all_modalities=False)` | Abstract dataset contract. `selected_subjects` validates and deduplicates; invalid ids raise `ValueError`. |
| `FakeDataset` | `FakeDataset(event_list=("fake1", "fake2", "fake3"), n_sessions=2, n_runs=2, n_subjects=10, code="FakeDataset", paradigm="imagery", channels=("C3", "Cz", "C4"), seed=None, sfreq=128, duration=120, n_events=60, stim=True, annotations=False, subjects=None, sessions=None, *, return_all_modalities=False, **kwargs)` | Generates MNE `RawArray` data. `data_path()` is a no-op. `seed` makes repeated fixtures reproducible. |
| `LocalBIDSDataset` | `LocalBIDSDataset(bids_root, path_search_params=None, read_extra_params=None, *, subjects=None, sessions_per_subject=None, events, code="LocalBIDSDataset-", interval, paradigm, doi=None, unit_factor=1e6, return_all_modalities=False)` | Reads an existing BIDS root using `mne-bids`; infers subjects and minimum sessions when omitted. Empty matching root raises `ValueError`. Import from `moabb.datasets.base`. |
| `BaseBIDSDataset.bids_paths` | `bids_paths(self, subject, path=None, force_update=False, update_path=None, verbose=None)` | Returns matching `mne_bids.BIDSPath` objects. The subclass supplies download/root behavior. |

MOABB re-exports catalog classes such as `BNCI2014_001`, `PhysionetMI`, and
`Nakanishi2015` from `moabb.datasets`. Avoid relying on spelling aliases or
removed classes; inspect the installed module's public attributes.

## Dataset selection and loading

| API | Signature | Notes |
|---|---|---|
| `dataset_search` | `dataset_search(paradigm=None, multi_session=False, events=None, has_all_events=False, interval=None, min_subjects=1, channels=())` | Returns instantiated dataset objects. Valid `paradigm`: `imagery`, `p300`, `ssvep`, `cvep`, or `None`. `events` filters event keys; `has_all_events=True` requires all requested events. `channels` may call `get_data([1])` and can download. |
| `BaseDataset.get_data` | `get_data(self, subjects=None, cache_config=None, process_pipeline=None, n_jobs=1)` | Returns nested `subject -> session -> run -> Raw/Epochs/array`. `subjects` must be a list; omitted means `subject_list`. Invalid subjects raise `ValueError`. `process_pipeline` is fixed (not fitted here). |
| `BaseDataset.data_path` | `data_path(self, subject, path=None, force_update=False, update_path=None, verbose=None)` | Abstract per-dataset implementation; normally returns a list of local file paths and may download. `update_path` is retained compatibility behavior. |
| `BaseDataset.download` | `download(self, subject_list=None, path=None, force_update=False, update_path=None, accept=False, verbose=None)` | Downloads selected/all subjects and returns `None`. `accept` is for a dataset license prompt. Provider behavior can use NEMAR `sourcedata` before upstream fallback. |
| `BaseDataset.convert_to_bids` | `convert_to_bids(self, path=None, subjects=None, overwrite=False, format="EDF", verbose=None, generate_figures=False)` | Writes a clean BIDS dataset and returns a `pathlib.Path`. Formats accepted by the inspected version: `EDF`, `BrainVision`, `EEGLAB`, `BDF`; unsupported values raise `ValueError`. |
| `BaseDataset.sourcedata_path` | `sourcedata_path(self, subject=None, path=None, force_update=False, verbose=None)` | Fetches original pre-BIDS NEMAR `sourcedata` for datasets declaring `nemar_id`; otherwise raises `ValueError`. Network/provider-specific. |

A returned `Raw` is not automatically an epoch matrix. Inspect
`raw.info`, annotations, and channel types before routing to a paradigm.

## Configuration and cache

| API | Signature | Notes |
|---|---|---|
| `moabb.set_download_dir` | `set_download_dir(path)` | Sets MNE `MNE_DATA`; creates a missing directory. `path=None` uses the MNE home default only when no current value exists. |
| `moabb.set_download_provider` | `set_download_provider(provider)` | Accepts `None`, `"auto"`, `"nemar"`, or `"upstream"`; unknown values raise `ValueError`. Stores a MOABB config preference. |
| `moabb.get_download_provider` | `get_download_provider()` | Returns the effective provider. `MOABB_DOWNLOAD_PROVIDER` environment configuration wins and invalid stored values fall back to `"auto"` with a warning. |
| `CacheConfig` | `CacheConfig(save_raw=False, save_epochs=False, save_array=False, use=False, overwrite_raw=False, overwrite_epochs=False, overwrite_array=False, path=None, verbose=None)` | Dataclass controlling BIDS-backed cache layers. `overwrite_*` can erase a selected representation. |
| `CacheConfig.make` | `CacheConfig.make(dic=None)` | Accepts `None`, a `dict`, or an existing `CacheConfig`; other values raise `ValueError`. |
| `get_dataset_path` | `get_dataset_path(sign, path)` | Resolves an MNE dataset root from explicit `path`, dataset-specific config, or shared `MNE_DATA`; may create the home default. Low-level/download behavior. |
| `download_if_missing` | `download_if_missing(file_path, url, warn_missing=True, verbose=True, force_update=False)` | Network helper that creates a parent directory and downloads a missing file. `force_update=True` removes the existing target; do not use for recovery until data is preserved. |

A safe configuration inspection does not call `data_path`, `download`,
`data_dl`, or `get_data` on a real dataset. Use
`scripts/check_download_config.py` for a temporary directory check.

## Catalog metadata and data utilities

| API | Signature | Result |
|---|---|---|
| `find_intersecting_channels` | `find_intersecting_channels(datasets, verbose=False)` | Returns `(common_channels, keep_datasets)` after loading subject 1 from each dataset; it is not offline-safe for real datasets. |
| `bids_metainfo` | `bids_metainfo(bids_path: pathlib.Path)` | Returns a dict keyed by BIDS filename with entity fields and `fpath`; requires a BIDS root and `mne-bids`. |
| `get_dataset_metadata` | `get_dataset_metadata(name)` | Returns a `DatasetMetadata` catalog object or raises `KeyError` for an unknown name. Import from `moabb.datasets.metadata`. |
| `BaseDataset.metadata` | property | Cached `DatasetMetadata` or `None` when the class has no catalog entry; `FakeDataset.metadata` is `None`. |
| `validate_metadata_against_dataset` | `validate_metadata_against_dataset(dataset, metadata)` | Returns a list of mismatch strings. It checks release subject count (`all_subjects` when present), sessions, and country code; it does not replace raw-data inspection. |
| `safe_extract_zip` | `safe_extract_zip(zf, dest_dir, members=None)` | Extracts selected/all ZIP members after rejecting traversal and symlink entries. |
| `safe_extract_tar` | `safe_extract_tar(tf, dest_dir, members=None)` | Extracts selected/all TAR members after rejecting traversal and links. |
| `build_raw_from_epochs` | `build_raw_from_epochs(data, ch_names, sfreq, event_ids, montage_name, *, ch_types=None, scale=1e-6, buffer_samples=50, onset_sample=0)` | Converts a `(n_trials, n_channels, n_samples)` array into continuous `RawArray` plus `STI` stimulus channel. Validates dimensions and event count. |
| `read_xdf` | `read_xdf(path)` from `moabb.datasets._xdf` | Built-in loader helper used by XDF-backed dataset classes. Returns `(streams, header)` in a pyxdf-shaped form; numeric streams are arrays and marker streams are string rows. Invalid headers raise `ValueError`. This internal module is not a general-format guarantee. |

Use metadata as a declared contract and raw/BIDS content as the observed data.
For example, compare `metadata.acquisition.sampling_rate` to
`raw.info["sfreq"]`, and exclude `stim` when comparing recorded channel counts.
