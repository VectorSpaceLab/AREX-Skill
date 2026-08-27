# Local dataset workflows

## Array fixture

```python
import numpy as np
from braindecode.datasets import create_from_X_y

X = np.random.default_rng(0).normal(size=(8, 4, 1000)).astype("float32")
y = np.arange(8) % 2
ds = create_from_X_y(
    X, y, drop_last_window=False, sfreq=100,
    window_size_samples=200, window_stride_samples=100,
)
assert len(ds) > 0
```

Use this path for already segmented trials. Set `ch_names` when channel identity
matters; otherwise downstream montages and topomaps cannot be aligned safely.

## MNE fixture

Create `mne.io.RawArray` or `mne.EpochsArray` from local arrays with an explicit
`mne.Info` object. Ensure channel types and `sfreq` are correct before converting.
Attach a `description` dictionary such as `{"subject": 1, "session": "A"}`
so splits can be performed by recording identity.

## Splitting

Keep all overlapping windows from a recording in one split. Prefer a split on
subject/session descriptions, then verify the unique identifiers in each
partition. A random split of windows from the same raw file generally leaks
near-duplicate samples.

## Serialization

Use braindecode's datautil serialization/load helpers when datasets must be
reused. Choose a new writable directory, avoid overwriting an existing
preprocessing result until its parameters match, and record preprocessing,
channel order, sampling rate, and target selection alongside the saved data.
Test a save/load round trip on a small local fixture before launching a large
operation. Never put credentials or private Hub repositories in serialized
metadata.
