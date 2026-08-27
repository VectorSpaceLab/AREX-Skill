---
name: dataset-management
description: "Select, inspect, configure, and safely load MOABB datasets,
  including catalog search, MNE data directories and providers, subject/session
  filtering, FakeDataset, local BIDS data, metadata, and cache/download
  recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Dataset management

Use this route when the task is to choose a MOABB dataset, inspect its catalog
metadata, select subjects or sessions, configure where data lives, use a local
or synthetic dataset, or diagnose a data/cache/BIDS problem. This route owns
**data acquisition and representation**, not paradigm preprocessing, evaluation
protocols, or result analysis.

## Install and establish the boundary

Install the base distribution in the active environment (`python -m pip install
moabb`); its inspected project dependencies include MNE and `mne-bids`. Verify
with `python -c "import moabb, mne, mne_bids; print(moabb.__version__)"`.
Plotly is optional and only needed for `generate_figures=True` (`moabb[interactive]`).
The built-in XDF reader is part of MOABB; it is used by selected dataset loaders,
not a replacement for validating a recording.

- **No network / tests / tutorials:** use `FakeDataset` or a local BIDS root.
  These paths are deterministic and do not authorize a real download.
- **Catalog choice:** use `moabb.datasets.utils.dataset_search`; inspect the
  returned dataset objects (`code`, `paradigm`, `event_id`, `subject_list`,
  `n_sessions`, `interval`) before handing the object to a paradigm.
- **Root and sibling routes:** use the [MOABB root skill directory](../../),
  [paradigms-and-pipelines](../paradigms-and-pipelines/),
  [evaluations-and-benchmarks](../evaluations-and-benchmarks/), and
  [analysis-and-visualization](../analysis-and-visualization/) links for
  work outside this route.
- **Real data:** state the dataset, subjects, storage root, provider, license
  acceptance, and expected size first. `data_path()` and `get_data()` may
  download missing files; do not run them on an offline or read-only machine.
- **Pipeline/evaluation:** after data selection, route processing to
  `../paradigms-and-pipelines/SKILL.md` and generalization/split decisions to
  `../evaluations-and-benchmarks/SKILL.md` when those sibling routes are
  available. Plotting and result tables belong to
  `../analysis-and-visualization/SKILL.md`.

See [API reference](references/api-reference.md) for verified signatures,
[formats](references/data-formats.md) for structures and metadata, and
[workflows](references/workflows.md) for bounded recipes. Run the bundled
[safe download check](scripts/check_download_config.py) and
[fake/catalog smoke](scripts/smoke_catalog_fake.py) before attempting network
work.

## Select and inspect a dataset

1. Import public classes from `moabb.datasets`; `LocalBIDSDataset` is imported
   from `moabb.datasets.base`. Instantiate the smallest representative object
   first. Dataset objects print their `code`.
2. For filtering, call `dataset_search(paradigm=..., multi_session=...,
   events=..., has_all_events=..., interval=..., min_subjects=...,
   channels=...)`. Valid paradigm values are `imagery`, `p300`, `ssvep`,
   `cvep`, or `None`. `channels` filtering reads subject 1, so it is not an
   offline-safe filter for a catalog with real datasets.
3. Confirm `dataset.subject_list` (selected subjects), `dataset.all_subjects`
   (an immutable-copy view of the full release), `dataset.n_sessions`,
   `dataset.event_id`, `dataset.paradigm`, and `dataset.interval`. Do not
   infer trial counts or channel availability from a dataset name; use the
   summary tables or `metadata`.
4. Use representative catalog families rather than memorizing the whole
   catalog: BNCI classes cover MAT/MI and ERP variants, `PhysionetMI` is a
   large imagery release, and `Nakanishi2015` is a multi-class SSVEP release.
   The catalog and per-dataset docs remain bounded references, not a promise
   that any host is online or that every dataset is installed locally.

## Configure storage and acquisition deliberately

- `moabb.set_download_dir(path)` sets MNE's shared `MNE_DATA` directory and
  creates a missing directory. `None` restores the MNE default only when no
  prior `MNE_DATA` is configured. Prefer an explicit writable project/cache
  directory and verify it with `mne.get_config("MNE_DATA")`.
- Dataset-specific `MNE_DATASETS_<SIGNIFIER>_PATH` settings and an explicit
  `path=` take precedence according to the MNE resolver. `get_dataset_path()`
  may create the default home data directory. Never put credentials or private
  absolute paths in scripts or reports.
- `set_download_provider("auto" | "nemar" | "upstream" | None)` controls
  MOABB's source policy; `get_download_provider()` reports the effective value.
  The `MOABB_DOWNLOAD_PROVIDER` environment variable wins for a run. `auto`
  prefers NEMAR's original `sourcedata/` when available and falls back per
  subject; `nemar` fails instead of falling back; `upstream` bypasses NEMAR.
- `dataset.data_path(subject, path=None, force_update=False,
  update_path=None, verbose=None)` returns a list of local file paths and may
  fetch one subject. `dataset.download(subject_list=None, path=None,
  force_update=False, update_path=None, accept=False, verbose=None)` fetches
  all or selected subjects and returns `None`. `accept=True` is a deliberate
  license choice, not a generic troubleshooting flag.
- Treat `force_update=True` and cache `overwrite_*` as destructive to the
  selected cache/data representation. First preserve or separately copy user
  data, inspect available files, and prefer a new writable `path`.

## Use subjects, sessions, and raw data

`BaseDataset.get_data(subjects=None, cache_config=None, process_pipeline=None,
n_jobs=1)` returns `subject -> session -> run -> mne.io.BaseRaw` (or the object
produced by a fixed process pipeline). `subjects` must be a list drawn from
`dataset.subject_list`; an invalid subject raises `ValueError`. Constructor
filters are the safer repeatable form: `Dataset(subjects=[...], sessions=[...])`.
Session selectors accept integers or strings. Integer `0` matches session keys
such as `"0train"`; exact strings match compound keys. Returned session and run
keys must begin with a numeric index, optionally followed by letters/numbers.

Default loading keeps EEG channels and excludes `stim`; set
`return_all_modalities=True` or pass a channel-type dict such as
`{"eeg": True, "eog": True}` when auxiliary channels are needed. Check
`raw.info["sfreq"]`, `raw.ch_names`, `raw.get_channel_types()`, annotations, and
`raw.n_times` before downstream processing. A stimulus channel may be added by
a loader and is not necessarily a recorded EEG channel.

## Safe offline paths

- `FakeDataset(...)` creates deterministic MNE `RawArray` objects. Set
  `seed`, small `n_subjects`, `n_sessions`, `n_runs`, `duration`, and `n_events`
  for a tiny fixture; choose `stim=True` or `annotations=True` to exercise the
  intended event path. Its `data_path()` is intentionally a no-op and must not
  be used to test network behavior.
- `LocalBIDSDataset(bids_root, path_search_params=None,
  read_extra_params=None, *, subjects=None, sessions_per_subject=None,
  events, code="LocalBIDSDataset-", interval, paradigm, doi=None,
  unit_factor=1e6, return_all_modalities=False)` consumes an existing BIDS root.
  It infers subjects and the minimum sessions per subject when omitted; an
  empty/non-BIDS root raises `ValueError`. The inspected MOABB distribution
  declares `mne-bids` as a base dependency; an import failure means the active
  installation is incomplete or incompatible.
- `dataset.convert_to_bids(path=None, subjects=None, overwrite=False,
  format="EDF", verbose=None, generate_figures=False)` writes a clean BIDS
  representation and returns its root. Supported formats are `EDF`,
  `BrainVision`, `EEGLAB`, and `BDF`; `generate_figures=True` is optional
  Plotly work. This is a data-writing operation: use a new output root and
  verify channel/event metadata before sharing it.
- For archives from untrusted sources, use MOABB's
  `safe_extract_zip()`/`safe_extract_tar()` rather than raw `extractall()`.
  They reject traversal outside the destination and links. The helpers do not
  validate scientific content, checksums, or license terms.

## Validate metadata and mismatches

`dataset.metadata` is a cached `DatasetMetadata` object or `None`; catalog
entries include acquisition (`sampling_rate`, channel counts/types/sensors),
participants, experiment/paradigm, sessions/runs, documentation, and optional
processing/application fields. `get_dataset_metadata("BNCI2014_001")` retrieves
a catalog entry. `validate_metadata_against_dataset(dataset, metadata)` returns
a list of mismatch strings (empty means no checked mismatch). It compares full
release subject counts via `all_subjects`, not a constructor-filtered
`subject_list`; it also checks sessions and country-code validity.

For a BIDS mismatch, first compare the actual `Raw` object and sidecars: exclude
`stim` from EEG channel counts, compare names/types and sampling rate, and check
that `events.tsv` labels intersect `dataset.event_id`. MOABB's BIDS conversion
can enrich `dataset_description.json`, EEG sidecars, `participants.tsv`,
`electrodes.tsv`, event sidecars, and a metadata YAML file. Missing demographic
values are written as `n/a`; do not invent them. A channel-name or metadata
mismatch is a stop-and-review condition, not a reason to silently rename or
remove channels.

## Cache recovery and handoff

`CacheConfig.make(None | dict | CacheConfig)` normalizes cache settings.
Use `{"save_raw": True, "use": True, "path": writable_root}` only when a
repeatable cache is wanted. If a cache has files but no completed session lock,
MOABB treats it as unavailable and recomputes; this is safer than consuming a
partial session. If the root is read-only, do not delete or set overwrite flags:
write a small permission sentinel, select a new writable cache/output root, and
rerun with that `path`. Preserve the original tree for inspection. A permission
failure while writing a BIDS sidecar or lock is an environment/storage problem,
not proof that the dataset bytes are corrupt.

Keep network and large-data operations visibly separate from offline checks.
Record the dataset class/version, provider, path policy, selected subject/session
ids, event mapping, channel policy, and whether data was synthetic, local, or
downloaded. Do not claim a real dataset was downloaded or validated when only
catalog construction or a fake fixture ran.

## Route out

- Paradigm/event windows, filtering, epoching, and sklearn pipelines: [sibling
  paradigms-and-pipelines](../paradigms-and-pipelines/).
- Subject/session generalization, splitters, scores, and benchmark caching:
  [sibling evaluations-and-benchmarks](../evaluations-and-benchmarks/).
- Results DataFrames, chance levels, statistics, plots, and reports: [sibling
  analysis-and-visualization](../analysis-and-visualization/).
