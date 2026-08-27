# Dataset data formats and invariants

Back to [dataset-management](../SKILL.md).

## Catalog objects

A MOABB dataset object describes a release and a current selection:

```text
Dataset
├── subject_list       selected subjects used by get_data()
├── all_subjects       full release (copy returned by the property)
├── n_sessions         declared sessions per subject
├── event_id           event label -> integer code
├── interval           task interval, normally [start, stop] seconds
├── paradigm           imagery | p300 | ssvep | cvep | ...
└── metadata            DatasetMetadata or None
```

`subject_list` can be narrowed by constructor `subjects=[...]`; `all_subjects`
remains the release list. A constructor `sessions=[0]` or `sessions=["0desc"]`
controls the loaded view without changing the release. Do not conflate the
number of selected subjects with the metadata catalog's full-release count.

## `get_data` hierarchy

The canonical raw data shape is:

```python
{
    subject_id: {
        "session_key": {
            "run_key": mne.io.BaseRaw,
        },
    },
}
```

Session/run keys start with an integer ordering prefix and may have an
alphanumeric suffix, for example `"0"`, `"0train"`, or `"1test"`. MOABB
rejects keys with underscores or duplicate numeric prefixes. A session is a
recording day/cap placement; a run is a contiguous recording within a session.
The actual number of runs can vary by dataset, so inspect each returned dict.

`FakeDataset` produces `RawArray` objects with EEG channels from `channels`,
optional `stim`, and optional event annotations. Its default event map is
`{"fake1": 1, "fake2": 2, "fake3": 3}`. For a tiny deterministic fixture,
use for example:

```python
FakeDataset(
    event_list=("left", "right"),
    n_subjects=2,
    n_sessions=2,
    n_runs=1,
    channels=("C3", "C4"),
    sfreq=32,
    duration=4,
    n_events=4,
    seed=7,
    annotations=True,
)
```

The generated array is random but reproducible for a fixed seed and subject.
The helper is for API/data-shape checks, not scientific validity or performance.

## Channel and event policy

By default the dataset-to-paradigm boundary retains EEG channels. A raw object
may still contain a `stim` channel used to encode event integers. With
`return_all_modalities=True`, MOABB retains all non-stim modalities; with a dict,
for example `{"eeg": True, "eog": True}`, it asks MNE to keep those types.
Always inspect:

```python
raw.get_channel_types()
raw.ch_names
raw.info["sfreq"]
raw.annotations.description
```

A metadata `n_channels` value normally describes recorded non-stim channels.
Compare channel types and names explicitly; do not “fix” a mismatch by dropping
channels before understanding whether the metadata, BIDS sidecar, or loader is
wrong. For a local BIDS dataset, event labels are read from an `events.tsv`
sidecar and filtered to the dataset's `event_id` keys.

## BIDS layout

A local BIDS EEG root typically contains:

```text
bids_root/
├── dataset_description.json
├── participants.tsv            optional participant values
├── participants.json            optional column descriptions
├── sub-01/
│   └── ses-01/
│       └── eeg/
│           ├── sub-01_ses-01_task-imagery_run-01_eeg.edf
│           ├── ..._events.tsv
│           ├── ..._events.json  optional event descriptions
│           ├── ..._channels.tsv
│           └── ..._electrodes.tsv / ..._electrodes.json (if positions exist)
└── README / derivatives / code  optional
```

`LocalBIDSDataset` searches EEG raw extensions with `mne_bids`, infers subjects
from BIDS entities if `subjects` is omitted, and chooses the minimum observed
session count if `sessions_per_subject` is omitted. It maps missing session or
run entities to `"0"` and warns. Supply `path_search_params` to narrow a root
(e.g. task, session, or run filters) and `read_extra_params` for arguments to
`mne_bids.read_raw_bids`.

MOABB's `convert_to_bids` writes a clean representation without the cache
pipeline `desc` hash. Cache files are different: cache interfaces can write
raw EDF/BrainVision/EEGLAB/BDF, FIF epochs, or NumPy arrays, with lock files
under `code/` to signal complete sessions. A visible data file without its
completed lock is treated as an incomplete cache and is recomputed.

## Metadata schema

`DatasetMetadata` aggregates:

- `acquisition`: sampling rate, `n_channels`, `channel_types`, sensors,
  hardware, line frequency and reference;
- `participants`: `n_subjects`, age summaries/lists, sex/handedness and health;
- `experiment`: paradigm, events, class count, task type and timing;
- `sessions_per_subject`, `runs_per_session`, optional session labels;
- `documentation`: DOI, license, country and repository;
- optional preprocessing, signal-processing, cross-validation, BCI application,
  paradigm-specific, data-structure and external-link fields.

BIDS enrichment uses participant metadata priority of per-subject values, then
raw `subject_info`, then aggregate values where applicable. Unknowns become
`n/a`; sex is normalized to BIDS `male`/`female`, and handedness to
`right`/`left`/`ambidextrous` when recognized. Treat aggregate values as
provenance, not an observed per-person fact.

## XDF recordings

Some catalog loaders consume `.xdf` recordings through MOABB's built-in
`moabb.datasets._xdf.read_xdf(path)`. The result is `(streams, header)`;
numeric streams expose `time_series` as a NumPy array and marker streams expose
per-sample string lists. The reader handles clock offsets, regular-rate
 dejittering, nested XML metadata, and recorder footers that are not accepted by
some external readers. It is a loader implementation detail: validate stream
names, channel count, nominal rate, timestamps, and marker semantics for a real
recording instead of assuming every XDF variant is supported.

## Safe file and cache handling

The archive helpers validate destination paths and reject absolute/`..`
traversal and symlink/hardlink members. They do not make a malicious file
scientifically trustworthy. For incomplete or read-only data:

1. stop writes and preserve the original root;
2. inspect permissions, free space, and the presence of expected files/sidecars;
3. choose a new writable cache/output root;
4. rerun without `force_update` or `overwrite_*` unless a separate copy exists;
5. validate one subject/session before scaling up.

Never delete a user's cache merely because a lock or sidecar is missing.
