# Waveform API reference

All examples use public imports:

```python
import numpy as np
from obspy import UTCDateTime, Trace, Stream, read
```

## Core objects and metadata

| Object/API | Inputs and result | Operational detail |
|---|---|---|
| `UTCDateTime(value)` | ISO string, date/datetime, timestamp, or another `UTCDateTime`; returns a UTC time value | Use it for `Stats.starttime` and all bounds. It supports UTC arithmetic such as `start + seconds`, comparisons, `isoformat()`, and `ns`. |
| `Trace(data=array, header=None)` | One contiguous sample array plus optional header mapping; returns one trace | `Trace.data` is a NumPy array or masked array. `Trace.stats` is a `Stats` object. |
| `Stream([traces])` | List of `Trace` objects; returns a list-like stream | `st[i]` returns a trace; `st[i:j]` returns a stream. `st.copy()` deep-copies traces and data. |
| `tr.id` / `tr.get_id()` | `network.station.location.channel` | IDs are the primary identity used by `merge`. Set the four components with a valid three-dot string. |
| `Stats` | Attribute or mapping access | Defaults include `sampling_rate=1.0`, `delta=1.0`, `npts=0`, empty SEED code fields, and epoch `starttime`. `sampling_rate` and `delta` are linked; `endtime` is derived and read-only. |
| `tr.times(type="relative", reftime=None)` | Optional time representation and reference | Use to build plotting/analysis axes; sample count remains `tr.stats.npts`. |

A useful inspection record:

```python
for tr in st:
    print({
        "id": tr.id,
        "start": tr.stats.starttime.isoformat(),
        "end": tr.stats.endtime.isoformat(),
        "npts": tr.stats.npts,
        "sampling_rate": tr.stats.sampling_rate,
        "delta": tr.stats.delta,
        "dtype": str(tr.data.dtype),
        "masked": bool(np.ma.isMaskedArray(tr.data) and np.ma.is_masked(tr.data)),
        "processing": list(getattr(tr.stats, "processing", [])),
    })
```

`npts` is maintained from `Trace.data`; for a nonempty trace, the expected duration is `(npts - 1) * delta`, not `npts * delta`. Treat a nonempty masked array as data with missing samples, not as a clean continuous signal.

## Read and write

```python
st = read(
    pathname_or_url="input.mseed",
    format="MSEED",             # omit only when autodetection is wanted
    headonly=False,
    starttime=None,
    endtime=None,
    nearest_sample=True,
    dtype=None,
    apply_calib=False,
    check_compression=True,
)
st.write("output.mseed", format="MSEED")
```

`read` accepts a local path, `pathlib.Path`, file-like object, wildcard path, or URL. This route uses local paths/file-like objects only; remote retrieval is a different route. `headonly=True` is a metadata-only scan and must not be combined with `starttime`, `endtime`, or `dtype`. `starttime`/`endtime` bounds are applied after reading; `nearest_sample=False` selects inner samples at non-sample-aligned boundaries. `apply_calib=True` changes sample values by the trace calibration factor, so record it.

`Stream.write(filename, format=None, **kwargs)` requires a nonempty stream and rejects masked data. With `format=None`, the extension is used where possible. An unknown format hint raises `ValueError`; do not respond by renaming a file without determining its actual format. The supported format set is plugin-dependent; this sub-skill only treats local MiniSEED behavior as a verified smoke target.

## Selection, slicing, and trimming

| Operation | Mutation and aliasing | Use |
|---|---|---|
| `st.select(network=..., station=..., location=..., channel=..., sampling_rate=..., npts=..., component=..., id=...)` | New stream, but selected traces alias originals | Wildcards are supported for string fields; `component` matches the final channel character. Copy before mutation. |
| `st.slice(starttime, endtime, keep_empty_traces=False, nearest_sample=True)` | New stream; sample data can reference originals | Non-destructive time view. Copy the result before processing. |
| `tr.slice(starttime, endtime, nearest_sample=True)` | New trace with a view/reference to sample data | Same boundary semantics for one trace. |
| `st.trim(..., pad=False, keep_empty_traces=False, nearest_sample=True, fill_value=None)` | In-place over all traces | Use a copied stream to preserve the source. Padding outside the source creates masked data by default, or concrete values when `fill_value` is supplied. |
| `tr.trim(..., pad=False, nearest_sample=True, fill_value=None)` | In-place | `starttime > endtime` raises `ValueError`; sample boundary selection is explicit. |
| `st.slide(window_length, step, offset=0, include_partial_windows=False, nearest_sample=True)` | Yields time views | Copy each yielded window before mutation; windows may overlap and may contain different trace counts. |

For exact sample alignment, derive bounds from a trace's `starttime` and `delta`, then verify `window[0].stats.starttime` and `endtime`. Do not use a float as a UTC bound for `Stream.slice`; use `UTCDateTime`.

## Merge, split, and ordering

```python
work.sort(keys=["network", "station", "location", "channel", "starttime"])
work.merge(method=0, fill_value=None, interpolation_samples=0)
```

`merge` first performs cleanup and then requires same-ID traces to have the same sampling rate, dtype, and calibration. It mutates and returns the stream. Important policies:

- `method=0`: conflicting overlap is treated like missing data; with default `fill_value=None`, missing portions are masked.
- `method=1`: later trace values win in overlap; `interpolation_samples=0` leaves a transition, `-1` interpolates all overlap samples, and a positive number limits interpolation.
- `fill_value=0` uses a concrete constant; `'latest'` repeats the last value before a gap; `'interpolate'` linearly fills a gap. These are hypotheses about missing data and must be recorded.
- `method=-1` performs cleanup only and leaves unresolved gaps/overlaps as separate traces.

`st.split()` produces contiguous unmasked traces from masked traces. Use it before writers that do not support masks, or fill with an explicit policy first. If traces have mismatched sample rates, IDs, dtypes, or calibration, do not merge; route to a deliberate resampling/retyping/calibration decision.

## In-place conditioning and sample-rate changes

```python
work = st.copy()
work.detrend("demean")              # or "simple", "linear", "polynomial", "spline"
work.taper(max_percentage=0.05, type="cosine")
work.filter("bandpass", freqmin=1.0, freqmax=8.0,
            corners=4, zerophase=True)
work.normalize()                     # optional; converts integer data to float
```

`filter(type, *args, **options)` supports `bandpass`, `bandstop`, `lowpass`, `highpass`, `lowpass_cheby_2`, and plugin-provided FIR types. Frequencies are in Hz and must respect the trace Nyquist frequency. Filtering rejects masked data; split or fill explicitly first. `detrend`, `filter`, `taper`, `normalize`, `integrate`, and `differentiate` mutate data and append processing information. Check `stats.processing` where auditability matters.

Choose a rate-change method deliberately:

| Method | Key parameters | Semantics |
|---|---|---|
| `decimate(factor, no_filter=False, strict_length=False)` | Integer factor | Keeps every factor-th sample; by default applies an anti-aliasing lowpass. `strict_length=True` rejects an end-time change when sample count is not compatible. |
| `resample(sampling_rate, window="hann", no_filter=True, strict_length=False)` | Target Hz | Fourier-domain resampling; default assumes periodic behavior and does not automatically lowpass. `no_filter=False` enables ObsPy's automatic lowpass within supported factor limits. |
| `interpolate(sampling_rate, method="weighted_average_slopes", starttime=None, npts=None, time_shift=0.0)` | Target Hz and interpolation method | Interpolates to a requested time grid. For downsampling, apply a suitable anti-aliasing lowpass first. |

When using any of these, compare old/new `npts`, `sampling_rate`, `delta`, `starttime`, `endtime`, and signal assumptions. Never call `decimate(..., no_filter=True)` on broadband data unless aliasing is intentionally handled elsewhere.

## Validation checklist

```python
assert all(tr.stats.npts == len(tr.data) for tr in work)
assert all(tr.stats.sampling_rate > 0 for tr in work if tr.stats.npts)
assert all(tr.stats.starttime <= tr.stats.endtime
           for tr in work if tr.stats.npts)
assert not any(np.ma.isMaskedArray(tr.data) and np.ma.is_masked(tr.data)
               for tr in work)  # required before Stream.write
```

For a round trip, reopen the file and compare `id`, UTC bounds, sample rate, `npts`, and values with an appropriate dtype/tolerance policy. A format may legitimately alter dtype or calibration representation; treat that as an explicit format contract, not as silent equivalence.
