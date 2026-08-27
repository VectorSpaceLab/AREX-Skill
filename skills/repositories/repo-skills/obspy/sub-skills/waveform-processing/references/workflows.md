# Local waveform workflows

These recipes are deliberately local and deterministic. Replace placeholders only after checking the input contract and preserving the original data.

## 1. Inspect a local file without changing samples

```python
from pathlib import Path
from obspy import UTCDateTime, read

path = Path("input.mseed")
head = read(path, format="MSEED", headonly=True)
for tr in head:
    print(tr.id, tr.stats.starttime, tr.stats.endtime,
          tr.stats.sampling_rate, tr.stats.npts, tr.data.shape)
```

Use `headonly` only for a metadata scan. For actual samples, call `read` again without `headonly`. If the file contains multiple records or channels, sort/group before any merge or processing.

## 2. Construct a trace with auditable metadata

```python
import numpy as np
from obspy import UTCDateTime, Trace, Stream

start = UTCDateTime("2020-01-01T00:00:00Z")
tr = Trace(
    data=np.arange(100, dtype=np.float32),
    header={
        "network": "XX", "station": "SYN", "location": "00",
        "channel": "BHZ", "starttime": start, "sampling_rate": 20.0,
        "calib": 1.0,
    },
)
st = Stream([tr])
assert tr.stats.npts == 100
assert tr.stats.endtime == start + 99 * tr.stats.delta
```

A header's `endtime` is derived. If the array is replaced, `npts` updates; if the sampling rate changes, `delta` and `endtime` are recalculated.

## 3. Select and process an independent UTC window

```python
from obspy import UTCDateTime

start = st[0].stats.starttime
stop = start + 2.0
window = st.slice(start, stop, nearest_sample=False).copy()
window.detrend("demean")
window.taper(max_percentage=0.05, type="cosine")
window.filter("lowpass", freq=5.0, corners=2, zerophase=True)
```

`slice` can alias source samples, so `.copy()` is the boundary between a read-only view and a destructive processing pipeline. `nearest_sample=False` makes the interval conservative at non-aligned bounds; validate the actual returned bounds rather than assuming the requested floating-point times were represented exactly.

## 4. Reconcile a gap with an explicit policy

```python
work = st.copy()
work.sort(keys=["starttime"])
work.merge(method=0, fill_value=None)
tr = work[0]
if np.ma.isMaskedArray(tr.data) and np.ma.is_masked(tr.data):
    # Choose one policy based on domain requirements, not convenience.
    filled = tr.data.filled(0.0)
    tr.data = filled
```

Prefer leaving a gap masked while inspecting it. If you fill, record the constant or use a second trace as evidence. `fill_value='interpolate'` is suitable only when linear interpolation across the gap is justified. If an overlap contains conflicting samples, `method=0` marks the overlap missing; `method=1` prioritizes the later trace. Compare the overlap before choosing.

## 5. Downsample without accidental aliasing

```python
work = st.copy()
old = (work[0].stats.sampling_rate, work[0].stats.npts,
       work[0].stats.endtime)
work[0].decimate(factor=2, no_filter=False, strict_length=False)
new = (work[0].stats.sampling_rate, work[0].stats.npts,
       work[0].stats.endtime)
print("old/new", old, new)
```

`decimate` is for an integer factor and defaults to an anti-aliasing lowpass. For arbitrary target rates, `resample` is Fourier-domain and assumes periodicity; `interpolate` uses a selected interpolation method and needs an anti-aliasing decision when downsampling. `strict_length=True` is a guard when the original end time must not change.

## 6. Headless MiniSEED round trip

```python
from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np
from obspy import Stream, Trace, UTCDateTime, read

start = UTCDateTime("2020-01-01T00:00:00Z")
source = Stream([Trace(
    data=np.arange(40, dtype=np.int32),
    header={"network": "XX", "station": "SYN", "location": "00",
            "channel": "BHZ", "starttime": start, "sampling_rate": 10.0},
)])
with TemporaryDirectory() as td:
    path = Path(td) / "roundtrip.mseed"
    source.write(path, format="MSEED")
    recovered = read(path, format="MSEED")
    assert len(recovered) == 1
    got = recovered[0]
    assert got.id == source[0].id
    assert got.stats.starttime == start
    assert got.stats.endtime == source[0].stats.endtime
    assert got.stats.sampling_rate == 10.0
    assert got.stats.npts == 40
    np.testing.assert_array_equal(got.data, source[0].data)
```

Use a temporary directory, not a repository or production output directory. If the writer rejects a masked trace, decide whether to split or fill before writing. For format-specific headers or event/inventory data, hand off to `formats-and-metadata`.

## 7. Difficult synthetic verification cases

1. **Gap plus metadata mismatch:** create two same-ID traces at 10 Hz with a two-sample gap, then create a third with the same ID but 20 Hz. Assert that `merge(fill_value=None)` produces one masked trace for the compatible pair and that merging the mismatched-rate trace raises rather than silently changing metadata. Also compare `fill_value=0` and `'interpolate'` values at the gap.
2. **UTC bounds plus malformed hint:** write an integer local MiniSEED trace with a fractional UTC start, reopen it using `starttime`/`endtime` bounds, and assert exact chosen sample bounds with both `nearest_sample=True` and `False`. Then call `read(path, format="NOT_A_REAL_FORMAT")` and assert a clear format error; do not fall back to a network or a different file.
3. **Aliasing and mutation:** create a trace, take `st.slice(...).select(...)`, mutate the view, and demonstrate why processing must start from `.copy()`. Assert that a copied pipeline leaves the source values unchanged.
