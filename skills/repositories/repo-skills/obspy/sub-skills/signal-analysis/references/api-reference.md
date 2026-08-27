# Signal-analysis API reference

These are public ObsPy interfaces relevant to this sub-skill. Exact behavior
can vary with installed NumPy/SciPy versions; inspect the installed signature
when accepting additional keyword arguments.

## Waveform methods

| Interface | Important parameters | Returns/mutates |
|---|---|---|
| `Trace.filter(type, *args, **options)` | `bandpass(freqmin, freqmax, corners=4, zerophase=False)`, `lowpass(freq, ...)`, `highpass(freq, ...)`, `bandstop(...)` | Mutates trace data; returns the trace |
| `Stream.filter(type, *args, **options)` | Same filter options, applied to every trace | Mutates stream; returns stream |
| `Trace.trigger(type, **options)` / `Stream.trigger(...)` | `recstalta`, `classicstalta`, `recstaltapy`, `delayedstalta`, `carlstatrig`, `energyratio`, `modifiedenergyratio`, `zdetect`; `sta`/`lta` are seconds | Replaces waveform samples with characteristic functions |
| `Stream.merge(method=0, fill_value=None, interpolation_samples=0, **kwargs)` | `fill_value=None` preserves gaps as masked data; `'interpolate'` or numeric values are explicit alternatives | Mutates stream; returns stream |
| `Trace.remove_response(inventory=None, output='VEL', water_level=60, pre_filt=None, zero_mean=True, taper=True, taper_fraction=0.05, plot=False, ...)` | `output='DISP'|'VEL'|'ACC'|'DEF'`; inventory or attached response required | Mutates data; physical-unit output |
| `Trace.simulate(paz_remove=None, paz_simulate=None, ..., water_level=600, pre_filt=None, ...)` | Complete PAZ dicts or attached `stats.paz` via `paz_remove='self'` | Mutates data; returns trace |

All listed waveform methods are in-place. Use `copy()` before them when
provenance or a raw comparison is needed.

## Trigger and correlation functions

| Function | Contract | Useful output |
|---|---|---|
| `recursive_sta_lta(a, nsta, nlta)` | Numeric array, integer windows in samples; best for a fast recursive characteristic function | Float array, same length as `a` |
| `classic_sta_lta(a, nsta, nlta)` | Numeric array, integer windows; requires data length at least `nlta` | Float array, same length |
| `trigger_onset(charfct, thres1, thres2, max_len=9e99, max_len_delete=False)` | Hysteresis: on threshold is normally greater than off threshold | `n x 2` integer array of on/off sample indices; empty list when none |
| `coincidence_trigger(trigger_type, thr_on, thr_off, stream, thr_coincidence_sum, ...)` | Applies one-station triggers then combines overlaps; `sta` and `lta` options are seconds | Chronologically sorted list of event dictionaries |
| `correlate(a, b, shift, demean=True, normalize='naive', method='auto')` | `shift` is max lag in samples; returns `2*shift+1` (or parity-adjusted) values | Cross-correlation vector |
| `xcorr_max(fct, abs_max=True)` | Finds max or absolute max; reports center-relative sample shift | `(shift, value)` |
| `correlate_template(data, template, mode='valid', normalize='full', demean=True, method='auto')` | Template must not be longer than data; `'full'` normalization is local/zero-normalized | Correlation vector |
| `xcorr_pick_correction(pick1, trace1, pick2, trace2, t_before, t_after, cc_maxlag, ...)` | Equal sample rates and enough padding around picks; returns a correction and coefficient | `(pick2_correction_seconds, coefficient)` |
| `correlation_detector(stream, templates, heights, distance, ...)` | Template(s) shorter than data, matched IDs/rates; `distance` is seconds | `(detections, similarity_streams)` |

`coincidence_trigger` changes waveform samples in its input stream while it
computes characteristic functions; pass a copy if the waveform is needed
later. Detection times derived from sample indices are
`trace.stats.starttime + index / trace.stats.sampling_rate`.

## Spectral and response APIs

- `PPSD(stats, metadata, skip_on_gaps=False, db_bins=(-200, -50, 1.),
  ppsd_length=3600.0, overlap=0.5, ...)` creates a probabilistic PSD for one
  network/station/location/channel/sample-rate combination. `metadata` may be
  an Inventory, a Parser/RESP source, a local response file, or a PAZ dict.
  `ppsd.add(stream)` consumes matching data; inspect `times_processed`,
  `times_gaps`, and `psd_values`; persist with `save_npz()` and reload with
  `PPSD.load_npz()`.
- `simulate_seismometer(data, samp_rate, paz_remove=None,
  paz_simulate=None, remove_sensitivity=True, simulate_sensitivity=True,
  water_level=600.0, zero_mean=True, taper=True, taper_fraction=0.05,
  pre_filt=None, seedresp=None, ...)` is the array-level frequency-domain
  response operation. PAZ dictionaries require `poles`, `zeros`, and `gain`;
  sensitivity is required when sensitivity correction is enabled.
- `corn_freq_2_paz(fc, damp=0.707)` makes a simple two-pole PAZ with two zeroes
  and unit gain/sensitivity, useful for a controlled simulation rather than a
  real instrument response.
- `cosine_taper(npts, p=0.1, freqs=None, flimit=None)` creates a time or
  frequency taper. The four-corner pre-filter convention is `(f1, f2, f3, f4)`.

## Array and real-time APIs

- `array_processing(stream, win_len, win_frac, sll_x, slm_x, sll_y, slm_y,
  sl_s, semb_thres, vel_thres, frqlow, frqhigh, stime, etime, prewhiten,
  verbose=False, coordsys='lonlat', timestamp='mlabday', method=0, store=None)`
  returns rows `[timestamp, relative_power, absolute_power, backazimuth,
  slowness]` for accepted windows. All traces need the same sample rate and
  coordinate metadata in either `stats.coordinates.latitude/longitude` or
  `.x/.y`, depending on `coordsys`.
- `RtTrace(max_length=None)` accepts sequential packets through
  `append(trace, gap_overlap_check=False, verbose=False)`. Register a built-in
  process with `register_rt_process('boxcar', width=N)`, `'integrate'`,
  `'differentiate'`, `'tauc'`, `'mwpintegral'`, or a non-recursive callable.
  Stateful functions use `RtMemory` across packets. With
  `gap_overlap_check=True`, timing gaps/overlaps raise instead of silently
  resetting process state.
- `obspy.realtime.signal` provides state-aware `offset`, `scale`, `integrate`,
  `differentiate`, `boxcar`, and other packet functions. Pass a `Trace`, not a
  bare array, to these public realtime functions.
