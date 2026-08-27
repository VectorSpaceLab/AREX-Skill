# Signal-processing recipes

The recipes below are intentionally offline and use caller-provided data. They
show the contract and validation points; replace `st`/`tr` with the input
objects, not with an implicit network download.

## 1. Prepare, detrend, filter, and inspect

```python
import numpy as np
from obspy import Stream

work = st.copy()
for tr in work:
    sr = float(tr.stats.sampling_rate)
    if sr <= 0 or not np.isfinite(sr):
        raise ValueError(f"invalid sampling rate for {tr.id}: {sr}")
    if np.ma.isMaskedArray(tr.data):
        raise ValueError(f"masked samples require an explicit gap policy: {tr.id}")
    if not np.isfinite(np.asarray(tr.data, dtype=float)).all():
        raise ValueError(f"non-finite samples: {tr.id}")

# If there are same-ID segments, choose a gap policy explicitly.
# work.merge(method=0, fill_value=None)  # preserve gaps as masks
work.detrend(type="demean")
for tr in work:
    sr = tr.stats.sampling_rate
    fmin, fmax = 1.0, 12.0
    if not 0 < fmin < fmax < sr / 2:
        raise ValueError("filter corners must lie strictly below Nyquist")
work.filter("bandpass", freqmin=fmin, freqmax=fmax,
            corners=4, zerophase=True)
```

`zerophase=True` applies the filter forward and backward and is appropriate for
offline picks when phase preservation matters. It is not a streaming/casual
filter. For a causal result, use the default and document the phase delay. Keep
extra samples before/after a pick to reduce edge artifacts. A filter's high
corner at or above Nyquist is not a valid reproducible configuration even if
ObsPy warns and changes behavior.

## 2. STA/LTA and hysteretic trigger

Direct trigger functions take samples, while the convenience method accepts
seconds:

```python
import numpy as np
from obspy.signal.trigger import recursive_sta_lta, trigger_onset

tr = st.select(component="Z")[0].copy()
tr.detrend("demean")
tr.filter("bandpass", freqmin=1, freqmax=12, zerophase=True)
sr = float(tr.stats.sampling_rate)
sta_seconds, lta_seconds = 0.5, 4.0
nsta = max(1, int(round(sta_seconds * sr)))
nlta = max(1, int(round(lta_seconds * sr)))
if not nsta < nlta:
    raise ValueError("STA must be shorter than LTA after sample conversion")
if len(tr.data) < nlta:
    raise ValueError("waveform is shorter than the LTA window")

cft = recursive_sta_lta(np.asarray(tr.data, dtype=np.float64), nsta, nlta)
threshold_on, threshold_off = 3.5, 0.5
if threshold_off >= threshold_on:
    raise ValueError("use hysteresis: off threshold < on threshold")
on_off = trigger_onset(cft, threshold_on, threshold_off)
times = [(tr.stats.starttime + i / sr,
          tr.stats.starttime + j / sr) for i, j in on_off]
```

`cft` is not a probability. Tune thresholds on representative noise and
signal, and report the characteristic-function peak and event duration. For a
network, use a copied stream and:

```python
from obspy.signal.trigger import coincidence_trigger

network_events = coincidence_trigger(
    "recstalta", threshold_on, threshold_off, st.copy(),
    thr_coincidence_sum=2, sta=sta_seconds, lta=lta_seconds,
    details=True, max_trigger_length=60)
```

The `sta`/`lta` options above are seconds and are converted per trace by
`coincidence_trigger`. A list/dict of `trace_ids` can restrict and weight the
network sum. Treat the returned dictionaries as candidate detections, not
validated phase picks.

## 3. Correlate a template or refine picks

For two equal-rate arrays and a bounded lag:

```python
from obspy.signal.cross_correlation import correlate, xcorr_max

if tr1.stats.sampling_rate != tr2.stats.sampling_rate:
    raise ValueError("cross-correlation requires equal sampling rates")
shift_seconds = 0.2
max_shift = int(round(shift_seconds * tr1.stats.sampling_rate))
cc = correlate(tr1, tr2, max_shift, demean=True,
               normalize="naive", method="auto")
shift_samples, coefficient = xcorr_max(cc, abs_max=False)
shift_seconds_measured = shift_samples / tr1.stats.sampling_rate
```

For a longer search trace, use `correlate_template(data, template,
normalize="full", demean=True)`, take the maximum, and convert its index to
an absolute time using the search trace start time and the template offset.
`correlation_detector(data, template, heights, distance)` wraps this pattern;
`heights` is a similarity threshold and `distance` is seconds. Templates and
search traces must have matching IDs, sample rates, preprocessing, and no
unhandled gaps. Report normalization and whether negative correlation is
allowed. For pick refinement, `xcorr_pick_correction` requires extra data
before/after each pick and returns `(correction_seconds, coefficient)`; inspect
warnings about low coefficient or a peak at the search boundary.

## 4. Response removal versus controlled PAZ simulation

### Inventory/response removal

Use a real Inventory or attached response and save the input first:

```python
corrected = tr.copy()
pre_filt = (0.005, 0.01, 20.0, 25.0)  # adapt to sample rate/instrument
if pre_filt[-1] >= corrected.stats.sampling_rate / 2:
    raise ValueError("pre-filter upper corner exceeds Nyquist")
corrected.remove_response(
    inventory=inventory, output="VEL", water_level=60,
    pre_filt=pre_filt, zero_mean=True, taper=True)
assert corrected.stats.npts == tr.stats.npts
```

This is a prerequisite-gated operation: `inventory` must yield a matching
response for the trace and time, or the trace must already have a valid
attached response. Do not fabricate an Inventory/PAZ or fall back to raw
counts while labeling the output physical units. For output units that are not
the native flat part of the response, consider `water_level=None` with a
carefully chosen `pre_filt`, then inspect the response plot.

### Synthetic PAZ simulation

For a controlled test or known PAZ, use complete dictionaries:

```python
from obspy.signal.invsim import corn_freq_2_paz

source = tr.copy()
source_paz = {
    "poles": [-0.037004 + 0.037016j, -0.037004 - 0.037016j,
              -251.33 + 0j, -131.04 - 467.29j, -131.04 + 467.29j],
    "zeros": [0j, 0j], "gain": 60077000.0,
    "sensitivity": 2516778400.0,
}
target_paz = corn_freq_2_paz(1.0)
target_paz["sensitivity"] = 1.0
simulated = source.copy()
simulated.simulate(paz_remove=source_paz, paz_simulate=target_paz,
                   water_level=60.0)
```

`paz_remove`/`paz_simulate` require `poles`, `zeros`, and `gain`; sensitivity
correction also needs `sensitivity`. `paz_remove="self"` reads attached
`stats.paz`, but only use it after checking all required keys. Response
operations are in place and frequency-domain edge behavior depends on zero
mean, taper, `water_level`, `pre_filt`, and data length. Compare spectra and
units before treating a simulation as successful.

## 5. PPSD and spectral QC

```python
from obspy.signal import PPSD

tr_qc = st[0].copy()
ppsd = PPSD(tr_qc.stats, metadata=inventory, ppsd_length=3600.0,
            overlap=0.5, skip_on_gaps=True)
ppsd.add(Stream([tr_qc]))
print(ppsd.id, ppsd.times_processed, ppsd.times_gaps)
# ppsd.plot(filename="psd.png")  # optional, caller-owned output
# ppsd.save_npz("psd.npz")
```

PPSD expects one stable network/station/location/channel and sample rate. A
short synthetic trace may produce no processed segment with the default
one-hour length; check `times_processed` instead of treating an empty plot as
an error. Use `skip_on_gaps=True` when zero-filling gaps would create an
artificial noise line. A static PAZ dictionary does not account for response
changes over time; prefer time-aware Inventory/RESP metadata for long spans.

## 6. Array processing

Each trace needs equal sampling rate and coordinate metadata. For geographic
coordinates, attach `stats.coordinates.latitude`, `.longitude`, and
`.elevation` in km, then use a bounded frequency/slowness grid:

```python
from obspy.signal.array_analysis import array_processing

out = array_processing(
    array_stream, win_len=1.0, win_frac=0.05,
    sll_x=-3.0, slm_x=3.0, sll_y=-3.0, slm_y=3.0, sl_s=0.03,
    semb_thres=-1e9, vel_thres=-1e9,
    frqlow=1.0, frqhigh=8.0, prewhiten=0,
    stime=stime, etime=etime, coordsys="lonlat", timestamp="julsec")
# columns: timestamp, relative power, absolute power, backazimuth, slowness
```

Check `out.shape` before indexing: thresholds may legitimately yield no rows.
Do not pass latitude/longitude without the required coordinate attributes, mix
coordinate systems, or use unequal sampling rates. Travel-time/geodetic
interpretation belongs to the travel-times-and-imaging skill.

## 7. Stateful packet processing

```python
import numpy as np
from obspy import Trace
from obspy.realtime import RtTrace

rt = RtTrace(max_length=120.0)
rt.register_rt_process("boxcar", width=5)
rt.register_rt_process("integrate")
for packet in packets:
    # packet must have matching id/rate/dtype/calibration and contiguous time
    processed = rt.append(packet, gap_overlap_check=True)
    assert processed.stats.sampling_rate == packet.stats.sampling_rate
    assert np.isfinite(processed.data).all()
```

Stateful realtime processing preserves memory between packets. With strict gap
checking, a gap/overlap raises; if a deliberate discontinuity is accepted with
`gap_overlap_check=False`, ObsPy reinitializes processing memory and emits a
warning. Keep packet sizes, data types, calibration, IDs, and timestamps
consistent. `zerophase` offline filtering is not a substitute for a stateful
causal realtime filter.
