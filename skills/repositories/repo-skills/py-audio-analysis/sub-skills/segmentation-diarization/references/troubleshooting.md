# Troubleshooting

## `.segments` rows are ignored or labels look shifted

- Use tab-separated rows with exactly three columns.
- Time values are seconds, not frames or samples.
- The file should usually have no header row.
- Make sure the `.wav` and `.segments` files share the same stem.

## Accuracy or purity stays at zero, empty, or `-1`

- Pass a matching ground-truth `.segments` file.
- `hmm_segmentation` and `speaker_diarization` only score against GT when the
  sidecar exists.
- Without GT, the evaluation numbers are placeholders.

## Headless plotting hangs or opens windows

- Keep `plot_results=False`, `plot_res=False`, and `plot=False`.
- If you need plots in CI, set `MPLBACKEND=Agg` before running.
- The bundled smoke script does not plot.

## Diarization changes between runs

- KMeans is stochastic and no fixed seed is set in the source.
- Use a known `n_speakers` when you have one.
- For unknown speaker counts, `n_speakers <= 0` searches 2..9 and picks the best
  silhouette, so borderline clips can still move around.

## The speaker count is wrong

- Purity can look low even when clustering is internally consistent.
- Re-check the expected number of speakers or use the auto-search path.
- If you have reference annotations, compare against the `.segments` sidecar.

## Very short audio fails or returns no spans

- Silence removal and thumbnailing need enough short-term windows.
- Increase clip length or reduce `st_win`, `st_step`, `short_window`, or
  `thumb_size`.
- `smooth_moving_avg(...)` raises when the smoothing window exceeds the frame
  count.

## HMM model errors

- `train_hmm_from_file` and `train_hmm_from_directory` write one pickled model
  artifact that also stores the class names and mid-window settings.
- Keep that file intact with the same path you pass to `hmm_segmentation`.
- Retrain if the artifact was created in an incompatible environment.

## Speaker model load failure

- `speaker_diarization` loads packaged speaker models internally.
- Reinstall with package data intact if the speaker model files are missing.
- The expected model names are `svm_rbf_speaker_10` and
  `svm_rbf_speaker_male_female`.

## Diarization crashes on GT sidecars

- Some package versions raise a type-conversion error when diarization finds a
  same-stem `.segments` file and tries to score purity.
- Work around it by running diarization on a copy of the WAV that has no
  matching `.segments` sidecar.
- The bundled smoke script already uses a temp copy for this reason.

## Unexpected WAV side effects

- The CLI wrapper for silence removal writes one WAV per detected segment next
  to the source input.
- The CLI wrapper for thumbnailing writes `_thumb1` and `_thumb2` files next to
  the source input.
- Use the API directly if you only want labels or time spans.

## MP3 or other media inputs fail

- Install `ffmpeg` if you need MP3 or generic media decoding.
- `pydub`-backed reads and the legacy media conversion helpers depend on it.
- Core segmentation workflows remain WAV-first and do not need media
  conversion.

## Legacy import caveat

- `audioAnalysis.py` and `audacityAnnotation2WAVs.py` use top-level imports.
- Treat them as script-style entry points or add their package directory to
  `sys.path` if you intentionally reuse them.
- The bundled smoke script avoids this caveat by using package imports.
