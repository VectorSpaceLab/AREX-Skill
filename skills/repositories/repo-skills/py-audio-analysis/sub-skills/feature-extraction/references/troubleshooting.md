# Feature Extraction Troubleshooting

Use this reference when pyAudioAnalysis feature extraction returns empty matrices, confusing shapes, non-finite values, import/decode failures, or plotting issues.

## Quick diagnosis checklist

1. Confirm the active environment imports `pyAudioAnalysis`, `numpy`, `scipy`, `matplotlib`, and `tqdm`.
2. Prefer WAV input for feature extraction; convert MP3/OGG/AU workflows through `cli-and-io` when decoder setup is uncertain.
3. Run `python scripts/feature_smoke.py --duration 2.0` from this sub-skill to verify synthetic short/mid extraction.
4. If using a real file, run `python scripts/feature_smoke.py --input-wav clip.wav` and inspect the JSON `shape`, `name_count`, and `finite` fields.
5. Check unit conversions: low-level feature APIs use samples, while directory/file wrappers use seconds.

## Common failure modes

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: need at least one array to concatenate` or empty short-term output | Audio is shorter than the short-term window, or window/step values rounded to invalid sample counts. | Reduce `short_window`/`short_step`, use a longer clip, and assert `len(signal) >= short_window_samples` before calling `feature_extraction`. |
| Mid-term extraction hangs or never returns | `int(round(mid_step / short_step))` became `0` inside `mid_feature_extraction`. | Make `mid_step_samples` at least about one `short_step_samples`; validate the ratio before calling. |
| Feature shape rows do not match names | Wrong output orientation assumption, package mismatch, or partial failed computation. | Treat feature matrices as `(feature_rows, time_windows)`. Assert `features.shape[0] == len(names)` and rerun the smoke helper. |
| Expected 34 short-term rows but got 68 | `deltas=True` is the default. | Pass `deltas=False` to `ShortTermFeatures.feature_extraction` when only base rows are wanted. Mid-term extraction uses the package default short-term rows internally. |
| Mid-term features have 136 rows | Mid-term rows are mean/std over the 68 default short-term rows. | This is expected: `2 * 68 = 136`. Use `mid_features.T` for row-per-window tables. |
| Directory extraction returns a 1-D vector | Only one file was accepted, so the package did not stack multiple rows. | Normalize with `features = np.atleast_2d(features)` before tabular processing. |
| Directory extraction returns no files | Folder had unsupported extensions, zero-byte files, failed decodes, or clips shorter than roughly 0.2 seconds. | Check `accepted_files`, convert media to WAV, remove empty files, and use longer clips or smaller windows. |
| `signal.ndim` is 2 after `stereo_to_mono` | Input has more than two channels; pyAudioAnalysis only flattens single-channel arrays and averages two-channel arrays. | Downmix multichannel audio explicitly before calling feature functions. |
| Non-finite values or all-zero/constant feature rows | Silent or constant audio produces degenerate statistics; some mid-term values are sanitized with `np.nan_to_num`. | Check signal RMS/variance before extraction. Treat beat and spectral dynamics from silence as invalid even if matrices are finite. |
| Beat extraction fails under newer NumPy with `np.Inf`, `numpy.Inf`, `np.NaN`, or `numpy.NaN` errors | pyAudioAnalysis 0.3.14 uses legacy NumPy aliases in a helper path. | Use a NumPy 1.x-compatible environment for strict package behavior, or add compatibility aliases (`np.Inf = np.inf`, `np.NaN = np.nan`) in a local smoke/check wrapper before calling beat extraction. The bundled helper applies this compatibility only inside the helper process. |
| `spectrogram(...)` prints a shape before JSON/log output | The 0.3.14 implementation prints `specgram.shape` unconditionally. | Capture stdout with `contextlib.redirect_stdout` when calling `spectrogram` from scripts. |
| Spectrogram/chromagram frame counts differ from short-term feature frame counts | The representation functions use legacy frame-start conventions that are not identical to `feature_extraction`. | Validate each returned matrix against its own axis lengths instead of forcing all frame counts to match. |
| Matplotlib errors, blocked execution, or empty plot windows | `plot=True` was used in a headless environment or without an interactive backend. | Keep `plot=False` for automation. If plotting is required, configure a Matplotlib backend such as `Agg` for file output or use an environment with a display. |
| `read_audio_file` returns `sampling_rate <= 0` or prints decode errors for MP3/OGG/AU | Optional media decoding stack is missing or ffmpeg/avlib is unavailable to pydub. | Convert the file to WAV through the IO/CLI workflow, or install the required media decoder dependencies and verify them separately. |
| `ModuleNotFoundError: No module named 'aifc'` | Python 3.13 removed the stdlib AIFF module imported by pyAudioAnalysis 0.3.14. | Use a Python version that still provides `aifc`, or install a compatible backport if allowed by the environment. For WAV-only smoke checks, the bundled helper can avoid exercising AIFF decoding. |
| `ModuleNotFoundError` for `eyed3` or `pydub` | The package's media reader imports optional media dependencies at module import time. | Install pyAudioAnalysis requirements for full media support. For feature-only synthetic or WAV smoke checks, use the bundled helper's default WAV-only import shims; use `--strict-imports` when verifying complete dependency installation. |

## Window and step validation helper

Use this pattern before low-level API calls:

```python
def seconds_to_samples(value_seconds, sampling_rate, name):
    if value_seconds <= 0:
        raise ValueError(f"{name} must be positive seconds")
    samples = int(round(value_seconds * sampling_rate))
    if samples <= 0:
        raise ValueError(f"{name} rounds to zero samples")
    return samples

short_window = seconds_to_samples(0.050, sampling_rate, "short_window")
short_step = seconds_to_samples(0.050, sampling_rate, "short_step")
mid_window = seconds_to_samples(1.0, sampling_rate, "mid_window")
mid_step = seconds_to_samples(1.0, sampling_rate, "mid_step")

if len(signal) < short_window:
    raise ValueError("audio is too short for the requested short-term window")
if int(round(mid_step / short_step)) < 1:
    raise ValueError("mid_step must be at least about one short_step")
if round((mid_window - (short_window - short_step)) / short_step) < 1:
    raise ValueError("mid_window is too small relative to short_window/short_step")
```

## Shape interpretation guide

| Matrix | Expected orientation | Row names |
| --- | --- | --- |
| Short-term features | `(short_feature_rows, short_windows)` | `short_names` |
| Mid-term features | `(mid_feature_rows, mid_windows)` | `mid_names` |
| Directory averaged features | `(files, feature_rows)` after `np.atleast_2d` | `feature_names` |
| Spectrogram | `(time_frames, frequency_bins)` | `freq_axis` names bins; `time_axis` names rows |
| Chromagram | `(time_frames, 12)` | `chroma_axis` labels 12 bins |

For CSV output, transpose short/mid matrices when the target tool expects one time window per row.
