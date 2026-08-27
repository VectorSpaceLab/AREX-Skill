---
name: waveform-processing
description: "Processes ObsPy waveform Streams and Traces by loading,
  inspecting, selecting, time-windowing, merging, conditioning, resampling, and
  writing local data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Waveform processing

Use this route for local waveform data represented by `obspy.Stream` and `obspy.Trace`: construct or load traces, inspect `Stats` and `UTCDateTime`, select and window data, reconcile gaps/overlaps, apply general conditioning, change sample rates, and write a local result. Keep format-specific schemas and event/inventory serialization in `formats-and-metadata`; use `data-access` for remote retrieval; use `signal-analysis` for triggers and instrument-response work; use `travel-times-and-imaging` for TauP, geodetics, and imaging.

## Operating contract

- Inputs: a local path, file-like object, or an already constructed `Trace`/`Stream`; optional format hint and UTC bounds. Outputs: a new object for non-mutating operations, an in-place modified object for processing methods, or a local file from `Stream.write`.
- Treat waveform samples and timing metadata as a pair. Inspect `id`, `starttime`, `endtime`, `sampling_rate`, `delta`, `npts`, `dtype`, masks, and `stats.processing` before and after changes.
- Processing methods (`filter`, `detrend`, `taper`, `normalize`, `resample`, `decimate`, `interpolate`, `integrate`, `differentiate`, and `trim`) mutate their traces. Use `st.copy()`/`tr.copy()` when raw data must remain available; `slice`, `select`, and `Stream.__getitem__` may alias sample data.
- Prefer explicit `format="MSEED"` (or another known format) when the format is known. Do not guess a format from an informal label, and do not use a remote URL in this route.
- Before merging, group by trace ID and confirm equal sampling rate, dtype, and calibration. Never “fix” a mismatch by silently changing metadata. A gap with `fill_value=None` becomes masked; choose and record a fill policy explicitly.
- Validate counts and UTC bounds after every destructive or time-changing operation. Do not write masked arrays: fill or split them deliberately first.

## Fast route

1. **Load or construct.** `st = obspy.read(path, format="MSEED", headonly=False)`; use `headonly=True` only for metadata scans, and do not combine it with `starttime`, `endtime`, or `dtype`. For synthetic data use `Trace(data=array, header={...})` and wrap with `Stream([tr])`.
2. **Inspect.** Print `st`, then for each trace inspect `tr.id`, `tr.stats`, `tr.data.shape`, `tr.data.dtype`, and `np.ma.isMaskedArray(tr.data)`. `Stats.endtime` is derived/read-only from `starttime`, `npts`, and `sampling_rate`; set `delta` or `sampling_rate`, not `endtime`.
3. **Select/window without losing the source.** `view = st.select(id="XX.STA.00.BHZ")` or wildcard fields; `window = st.slice(UTCDateTime(...), UTCDateTime(...), nearest_sample=False)`. Use `st.copy().trim(...)` for an in-place cut of an independent object. Use `pad=True` only with a declared `fill_value`/mask policy.
4. **Reconcile.** `work.sort(keys=["network", "station", "location", "channel", "starttime"])`; call `work.merge(method=0, fill_value=None)` for conservative overlap handling, `fill_value=0` or `'interpolate'` only when justified, and `method=1` when later samples should win. Check the resulting trace count and mask. `split()` returns contiguous pieces from masked data.
5. **Condition and resample.** On a copy, typically `detrend("demean")`, `taper(max_percentage=0.05, type="cosine")`, then `filter("bandpass", freqmin=..., freqmax=..., corners=..., zerophase=True)`. For integer-factor downsampling prefer `decimate(factor, no_filter=False, strict_length=...)`; otherwise choose `resample` or `interpolate` intentionally and document anti-aliasing/periodicity assumptions. Normalize only when a unit-scale signal is wanted.
6. **Write and reopen.** After confirming no masks remain and the metadata is valid, `work.write(output_path, format="MSEED")`; reopen with `obspy.read(output_path, format="MSEED")` and compare IDs, UTC bounds, sample rate, count, dtype-compatible values, and any expected quantization. Use a temporary local path in tests.

## References and helper

- [API reference](references/api-reference.md) contains public signatures, mutation/alias rules, and parameter decisions.
- [Workflows](references/workflows.md) contains reproducible local recipes and validation checkpoints.
- [Troubleshooting](references/troubleshooting.md) maps symptoms to safe diagnosis and recovery.
- [`scripts/waveform_smoke.py`](scripts/waveform_smoke.py) runs deterministic construction, gap/overlap policy, processing, and a headless MiniSEED round-trip using a temporary directory. Run `python scripts/waveform_smoke.py --help` and then `python scripts/waveform_smoke.py`; it never contacts a network or alters the checkout.

## Handoff

Pass to `formats-and-metadata` when a format's headers, encoding, or event/inventory serialization is needed. Pass to `data-access` for FDSN or routing clients. Pass to `signal-analysis` for STA/LTA, coincidence triggers, response removal, or specialized signal algorithms. Preserve a concise processing record: input identity, UTC interval, original/new sample counts and rate, gap/overlap decision, operations and parameters, output format/path, and reopen validation result.
