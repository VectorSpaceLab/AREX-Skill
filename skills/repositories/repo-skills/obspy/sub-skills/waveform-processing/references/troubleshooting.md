# Waveform troubleshooting

| Symptom | Likely cause | Safe diagnosis | Recovery / handoff |
|---|---|---|---|
| `read` raises `IOError`/cannot open file | Missing local path, empty match, or unreadable input | Check `Path(path).is_file()` and whether a wildcard has matches; do not alter the source | Correct the local path or route format discovery to `formats-and-metadata`. |
| `read(..., format="...")` raises a format/plugin error | The hint is not a registered waveform reader or does not match the bytes | Retry only after confirming the actual local format; an explicit hint disables autodetection | Use the correct public format name. Do not silently switch formats. |
| `read(..., format="NOT_A_REAL_FORMAT")` fails | Expected malformed format-hint case | Catch `ValueError` and retain the original path | Report the invalid hint; do not use network fallback. |
| `headonly=True` warning mentions time bounds or dtype | Unsupported combination | `headonly` cannot be combined with `starttime`, `endtime`, or `dtype` | Perform a metadata scan first, then a normal sample read with bounds/conversion. |
| `Stream.write` says empty stream | No traces survived selection/trim or the input was empty | Check `len(st)` and each trace's `npts` before writing | Fix selection/window bounds or set `keep_empty_traces` only for inspection, not for output. |
| `Stream.write` rejects masked arrays | A gap/padded trim remains masked | Check `np.ma.is_masked(tr.data)` and inspect mask locations | Split to contiguous traces, or fill with an explicit domain-approved value and record it. Never call `.filled()` without choosing a policy. |
| `merge` refuses same IDs with different sampling rates | Metadata mismatch | Compare `stats.sampling_rate`, `delta`, dtype, and calibration for every candidate | Resample/retype/calibrate deliberately before merging, or keep separate traces. Do not edit only the header. |
| `merge` refuses different dtypes or calibration | Data/scale mismatch | Print `tr.data.dtype` and `tr.stats.calib`; compare units and encoding | Convert values/metadata under a documented policy, then merge; otherwise hand off to format/metadata route. |
| `merge` leaves multiple traces | A real gap, conflicting overlap, or unequal IDs remains | Sort and inspect IDs, UTC ranges, masks, and overlap values; use `method=-1` to inspect cleanup only | Choose `method=0` (conservative), `method=1` (later wins), and an explicit gap fill policy. |
| Merge unexpectedly masks an overlap | `method=0` treats conflicting overlap as missing | Compare the overlapping samples and their time alignment before merging | Keep the mask for uncertainty or select `method=1` only if the later trace is authoritative. |
| Filter/detrend/taper raises for masked data | Signal operations require a continuous array | Test for a masked array and locate the gap | Split or fill first; document how the missing interval was handled. |
| Filter raises a frequency/Nyquist error or unstable result | Cutoff is invalid for the current sample rate, or trace is too short | Check `stats.sampling_rate`, Nyquist (`rate/2`), `npts`, and filter parameters | Choose valid cutoffs, use a suitable trace length, or route specialized analysis to `signal-analysis`. |
| Original data changed after `slice`/`select` processing | Returned traces can alias source samples | Compare source values before and after a tiny mutation test | Use `st.copy()` or `tr.copy()` before every destructive pipeline. |
| Trim result has unexpected start/end or count | Bounds are between sample times or nearest-sample policy differs | Print requested and actual UTC bounds and compare with `nearest_sample=True/False` | Select the intended policy and validate sample indices; do not overwrite `starttime` to hide a mismatch. |
| `starttime > endtime` or invalid UTC input | Reversed bounds or malformed time representation | Construct bounds separately with `UTCDateTime` and compare them | Correct the bounds; preserve UTC, not local naive time assumptions. |
| `decimate` changes the end time or refuses strict length | `npts` is not compatible with the integer factor | Compare `npts % factor` and old/new `endtime` | Use `strict_length=False` only when the sub-sample end-time change is acceptable; otherwise trim or choose another method. |
| Downsampling shows aliasing | Anti-aliasing filter was disabled or inadequate | Compare spectra/known high-frequency content before and after | Use `decimate(no_filter=False)` or manually lowpass before interpolation; record cutoff. |
| Fourier `resample` gives edge artifacts | The method assumes periodicity | Inspect endpoints and compare with a method appropriate to the signal | Use tapering/windowing or `interpolate`; preserve the raw trace for comparison. |
| Round trip changes dtype or calibration | Format encoding has its own representation rules | Compare values, `dtype`, `calib`, UTC metadata, and `_format` after reopen | Apply format-specific expectations; hand off schemas/encoding to `formats-and-metadata`. |
| Plotting fails in a headless environment | Plotting backend/display is unavailable | Avoid using plotting as validation; inspect numeric values and metadata | Use numerical assertions or configure a caller-owned noninteractive backend; imaging is out of scope here. |
| Native MiniSEED path cannot load a shared library | Optional compiled runtime/backend is unavailable in the current environment | Run a tiny import/write probe and capture the exception | Treat it as an environment gap, not a waveform API failure; report the missing backend to the parent verifier. |

## Minimal pre-write gate

```python
import numpy as np

if not st:
    raise ValueError("refusing to write an empty stream")
for tr in st:
    if tr.stats.npts != len(tr.data):
        raise ValueError(f"npts/data mismatch for {tr.id}")
    if np.ma.isMaskedArray(tr.data) and np.ma.is_masked(tr.data):
        raise ValueError(f"masked data remain for {tr.id}; choose a fill/split policy")
    if tr.stats.npts and tr.stats.sampling_rate <= 0:
        raise ValueError(f"invalid sample rate for {tr.id}")
```

Keep the original input and an operation log when debugging. A successful method return is not sufficient evidence: check the trace count, masks, sample count, UTC bounds, rate, values, and reopen behavior.
