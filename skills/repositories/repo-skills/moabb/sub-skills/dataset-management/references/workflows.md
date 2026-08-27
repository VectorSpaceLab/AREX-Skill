# Dataset-management workflows

Back to [dataset-management](../SKILL.md). These recipes separate offline
inspection from data acquisition. Replace all paths with caller-owned writable
locations; do not embed machine-specific paths in reusable code.

## 1. Offline fake two-session check

Use this before a paradigm or evaluation is chosen:

```python
from moabb.datasets import FakeDataset

dataset = FakeDataset(
    event_list=("left", "right"),
    n_subjects=2,
    n_sessions=2,
    n_runs=1,
    channels=("C3", "C4"),
    sfreq=32,
    duration=4,
    n_events=4,
    seed=11,
    annotations=True,
    subjects=[1, 2],
    sessions=[0, 1],
)
data = dataset.get_data(subjects=[1, 2])
assert set(data) == {1, 2}
assert set(data[1]) == {"0", "1"}
raw = data[1]["0"]["0"]
assert raw.info["sfreq"] == 32
```

This proves subject/session/run shape and reproducibility only. It does not
prove a real dataset's event semantics, sensor quality, or benchmark result.
The bundled `scripts/smoke_catalog_fake.py` runs a smaller variant and can
optionally construct the catalog search.

## 2. Search without touching data

```python
from moabb.datasets.utils import dataset_search

candidates = dataset_search(
    paradigm="imagery",
    multi_session=True,
    min_subjects=2,
)
for ds in candidates[:10]:
    print(ds.code, ds.subject_list, ds.n_sessions, ds.event_id)
```

This instantiates catalog classes but does not request subject data when
`channels=()` (the default). `channels=[...]` and
`find_intersecting_channels(...)` do load subject 1 and may download. Apply
those filters only after a network/data decision and a writable cache have been
approved. Event filters select datasets by declared event keys, not by a
validated raw recording.

## 3. Subject/session selection

```python
from moabb.datasets import FakeDataset

selected = FakeDataset(
    n_subjects=4,
    n_sessions=3,
    subjects=[2, 4],
    sessions=[0],
    seed=3,
)
data = selected.get_data()  # uses constructor-selected subjects
assert set(data) == {2, 4}
assert all(set(subject_data) == {"0"} for subject_data in data.values())
```

Use `all_subjects` when reporting the release population and `subject_list`
when describing the actual run. For cross-subject evaluation, route the
protocol decision to the evaluation route rather than implementing a split in
this route.

## 4. Local/private BIDS two-session flow

A local root must already contain BIDS EEG files and matching sidecars. Do not
call `download()` for it:

```python
from moabb.datasets.base import LocalBIDSDataset

local = LocalBIDSDataset(
    bids_root="/caller/owned/bids-root",
    events={"left": 1, "right": 2},
    interval=[0, 3],
    paradigm="imagery",
    subjects=[1],
    sessions_per_subject=2,
)
paths = local.bids_paths(1)
data = local.get_data(subjects=[1])
metadata = local.get_additional_metadata("1", "01", "01")
```

If `paths` is empty, inspect BIDS subject/session/task/run entities and raw
extensions. If `metadata` is `None`, the matching run has no events sidecar;
if it is empty, the sidecar labels did not intersect `event_id`. Validate the
actual raw channel names/types and sampling rate before handing off.

For a no-network synthetic BIDS fixture, first generate a tiny `FakeDataset`,
write a temporary BIDS root with `convert_to_bids`, then load that root with
`LocalBIDSDataset`. Keep this as a test fixture; do not represent it as a
scientific data conversion or overwrite a user root.

## 5. Cache a small raw layer

```python
from moabb.datasets import FakeDataset

cache = FakeDataset(n_subjects=1, n_sessions=2, n_runs=1, seed=5)
data = cache.get_data(
    subjects=[1],
    cache_config={
        "save_raw": True,
        "use": True,
        "path": "/caller/owned/cache",
    },
)
```

The first run can write EDF/BIDS sidecars and per-session lock markers; a later
run can read the cache. If files exist but a session lock is absent, MOABB
recomputes rather than trusting a partial session. For recovery, preserve the
root, use a new writable `path`, and do not combine `overwrite_raw=True` with
unexamined user data. `bids_metainfo(Path(root))` is useful for a read-only
inventory after a cache has completed.

## 6. Configure a real download (explicit boundary)

After approval of network, license, provider, storage, and size:

```python
from moabb import set_download_dir, set_download_provider
from moabb.datasets import BNCI2014_001

set_download_dir("/caller/owned/mne-data")
set_download_provider("auto")
dataset = BNCI2014_001(subjects=[1])
paths = dataset.data_path(subject=1, path=None, force_update=False)
```

`paths` is a local-path list only after the resolver completes. A full
`dataset.download(subject_list=[1], accept=True)` is an explicit acquisition
operation. Prefer a single subject first, check the resulting raw structure,
and only then scale up. `force_update=True` is for a deliberate refresh, not a
first response to a failed or incomplete cache.

## 7. Convert selected data to clean BIDS

```python
from moabb.datasets import FakeDataset

source = FakeDataset(n_subjects=1, n_sessions=2, n_runs=1, seed=9)
bids_root = source.convert_to_bids(
    path="/caller/owned/bids-output",
    subjects=[1],
    overwrite=False,
    format="EDF",
)
```

Use a new output directory. `overwrite=False` skips existing subject files;
`overwrite=True` removes/replaces the selected converted subject. Afterward,
inspect `*_events.tsv`, channels, participant/description metadata, and the
absence of cache `desc` hashes. `generate_figures=True` is optional Plotly work
and is not needed for a data-management check.
