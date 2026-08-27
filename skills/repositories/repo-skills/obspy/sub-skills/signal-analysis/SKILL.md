---
name: signal-analysis
description: "The signal-analysis skill guides agents through ObsPy waveform
  filtering, trigger/STA-LTA detection, correlation, spectral quality control,
  response correction or simulation, array processing, and stateful real-time
  analysis with explicit sampling assumptions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Signal analysis

Use this skill after a `Trace`/`Stream` is available and the task is waveform
processing, detection, correlation, spectral QC, response handling, array
beamforming, or packet-by-packet processing. Keep raw data intact with
`.copy()` before any in-place operation. This skill does not acquire remote
waveforms, solve travel times/geodesy, or make plots the primary deliverable.

## Operating contract

- **Input:** `Trace` or `Stream` with numeric samples, accurate
  `stats.sampling_rate`, and (for time-aware work) `starttime`/trace IDs.
  Before processing, report sample rate, duration, gaps/overlaps, masked data,
  units, and response metadata status.
- **Output:** a new or explicitly mutated waveform object, characteristic
  function/detection records, correlation values/shifts, PSD/PPSD products,
  response-corrected/simulated samples, array result rows, or real-time packet
  output. Record parameters and validation signals in the caller's result.
- **Invariant:** convert seconds to samples using the *trace's* actual sample
  rate, then validate positive windows and `nsta < nlta`; never silently reuse
  thresholds or windows from another sampling rate.
- **Mutation:** `Trace.filter`, `Stream.filter`, `trigger`, `simulate`,
  `remove_response`, `merge`, and realtime append/processes mutate or consume
  data/state. Copy first when raw data or packet data must remain available.
- **Validation:** check finite values, expected lengths, timing continuity,
  Nyquist constraints, trigger onset/off indices, correlation peak and sign,
  response prerequisites, and output units. Do not infer physical units from
  channel names alone.

For a deterministic CPU smoke check, run the bundled helper (it creates only
in-memory data):

```bash
python scripts/signal_smoke.py --help
python scripts/signal_smoke.py
```

See [api-reference.md](references/api-reference.md) for public signatures and
[processing-recipes.md](references/processing-recipes.md) for complete recipes.
Use [troubleshooting.md](references/troubleshooting.md) when a processing gate
fails.

## Route by task

1. **Prepare:** copy, inspect timing and gaps, merge only with an intentional
   overlap/gap policy, detrend before filtering or spectral work, and choose a
   pre-filter below Nyquist.
2. **Filter/QC:** use `Trace.filter`/`Stream.filter` for labeled waveforms;
   use `obspy.signal.filter` functions only when operating on arrays and pass
   `df`. Prefer `zerophase=True` for offline phase-preserving analysis; use
   causal/stateful processing for real time.
3. **Detect:** band-limit as justified, convert STA/LTA durations to samples,
   compute a characteristic function, then apply hysteretic `trigger_onset`.
   Preserve the original waveform because `Trace.trigger` overwrites samples.
   Use `coincidence_trigger` for weighted multi-trace evidence.
4. **Correlate:** align IDs, sample rates, units, and preprocessing between
   data and template. Use `correlate` for bounded shifts, `correlate_template`
   for a search trace, and `correlation_detector` for thresholded detections.
   Report lag convention, peak value, normalization, and detection distance.
5. **Spectral/response:** use `PPSD` only with a stable ID/sample rate and
   response metadata (Inventory, Parser/RESP, or an explicit PAZ dictionary).
   For `remove_response`, an Inventory or attached response is mandatory;
   without it, stop and request metadata rather than guessing. For controlled
   PAZ simulation, use `Trace.simulate`/`simulate_seismometer` with complete
   poles/zeros/gain (and sensitivity when sensitivity correction is enabled),
   taper, zero-mean, and an appropriate water level or pre-filter.
6. **Array/real time:** `array_processing` requires equal sample rates and
   per-trace coordinates plus a declared coordinate system. `RtTrace` requires
   matching IDs, sample rates, dtypes, calibration, and contiguous packet
   timing; register stateful processes and reset/raise on gaps as appropriate.

## Guardrails

- Do not call response removal with `inventory=None` unless a valid response is
  already attached; missing response is a prerequisite failure, not a reason to
  substitute a guessed PAZ.
- Do not pass Hz where an API requires samples, or samples where it requires
  seconds. `coincidence_trigger` maps its `sta`/`lta` options from seconds per
  trace; direct STA/LTA functions require integer samples.
- Do not filter at/above Nyquist. A high corner at Nyquist may be downgraded by
  the package with a warning; treat that as a configuration error in a
  reproducible pipeline.
- Avoid response deconvolution outside the instrument's valid band. Use a
  four-corner `pre_filt=(f1, f2, f3, f4)` and inspect the response plot or
  spectral bounds when physical amplitudes matter.
- Treat masked/gappy streams, unequal three-component lengths, mismatched
  correlation rates, and missing array coordinates as explicit failures.
- Network clients, live SeedLink paths, Cartopy, and shapefile integrations are
  outside this skill's verified operating path; do not invent credentials or
  claim a live acquisition succeeded.
