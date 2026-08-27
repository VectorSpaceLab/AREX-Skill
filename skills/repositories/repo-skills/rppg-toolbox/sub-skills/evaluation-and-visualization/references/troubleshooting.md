# Troubleshooting

## Empty or malformed saved output

- **`missing required key`**: the file is not a test-output pickle. Confirm it
  contains `predictions`, `labels`, `label_type`, and `fs`; do not guess a
  schema from a filename.
- **No trials or empty selected trial**: check that the trainer actually saved
  test batches and that the selected trial has nonempty chunks. The plotting
  helper exits without writing a misleading blank figure.
- **Prediction/label lengths differ**: inspect chunk keys and cache alignment
  before truncating. Metric MACC truncates to the shorter length, but a report
  must disclose any alignment repair.
- **Tensor unpickling fails**: load the pickle in an environment that can
  resolve the tensor class, then export arrays to a simple local format. The
  helper intentionally does not install packages or import the original
  project.

## Signal processing failures

- **`window < 9`**: repository evaluation skips it. Do not pad it and report a
  normal HR result. For a visual sanity check use `plot_saved_predictions.py
  --raw`, but label the trace as too short for evaluation.
- **`filtfilt` pad-length error**: use `--raw` for a short trace, or collect a
  longer window. Do not silently change the filter order or band.
- **No peaks / one peak**: peak HR is undefined. Try FFT only after checking
  the signal and sampling rate; do not replace a missing peak estimate with
  zero.
- **`NaN` MACC, Pearson, or SNR**: a constant signal, zero-power band, empty
  harmonic bin, or too few observations can make a correlation or ratio
  undefined. Report `NaN`/unavailable and the cause. A constant trace may be
  plotted, but it is not evidence of successful recovery.
- **Unexpected HR/RR**: verify `fs`, `label_type`/`diff_flag`, band (PPG
  0.6--3.3 vs paper-recommended 0.75--2.5 Hz; respiration 0.13--0.5 Hz),
  FFT vs Peak method, and window size in seconds. A wrong `fs` scales both
  FFT and peak results.
- **MAPE divide-by-zero**: label HR/RR values of zero make MAPE undefined;
  retain the invalid count and use MAE/RMSE for those observations.

## Preprocessed-array plot failures

- **Input shape rejected**: the static helper expects frame-first `(..., 3)`
  or `(..., 6)` arrays. Check that an entire dataset cache or batch tensor was
  not passed accidentally.
- **Label length differs from frames**: report the lengths and inspect the
  cache pairing; do not fabricate labels.
- **Short label or constant label**: use `--no-filter` for inspection and note
  that frequency-domain HR is not reliable. The CLI marks a constant trace;
  it does not create a fake dominant frequency.
- **Wrong diff behavior**: choose `--diff-flag` explicitly when the path name
  does not describe label type. `DiffNormalized` requires cumulative summation
  before detrending; `Raw` and `Standardized` do not.

## OpenFace conversion and CSVs

- **No files discovered**: check the explicit `--mode` layout and input root;
  the converter does not search arbitrary paths or download data.
- **Unreadable video/MP4**: confirm OpenCV can decode the input and that the
  output directory is writable. A failed writer is fatal; no partial success is
  claimed.
- **Existing output refused**: choose a new output path or pass `--force` only
  when replacement is intentional.
- **CSV missing columns**: rerun OpenFace with `-pose -aus` and compatible
  feature output. The required contract is `frame`, `timestamp`, 17 `AU##_r`
  columns, and `pose_Rx`, `pose_Ry`, `pose_Rz`; see
  [motion-analysis.md](motion-analysis.md).
- **All-NaN or one-row CSV**: treat that file as invalid for standard deviation,
  not as zero motion. Check OpenFace tracking quality and output version.
- **Comparison plot has different scales**: preserve group labels and record
  OpenFace version, frame rate, and dataset preprocessing before interpreting
  AU/pose differences.

## Safe output behavior

All bundled helpers require an explicit output path, create only missing parent
directories, and refuse to overwrite an existing file unless `--force` is
passed. They never download data, invoke OpenFace, modify input arrays, or
write into the repository source tree by default.
