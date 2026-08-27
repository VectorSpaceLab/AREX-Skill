# Evaluation API and metric contract

This is a source-derived contract, not an import recipe. A Researcher should
be able to reproduce the choices from this document without importing the
original checkout. The public orchestration entry points are
`calculate_metrics(predictions, labels, config)`,
`calculate_resp_metrics(predictions, labels, config)`,
`calculate_bvp_metrics(predictions, labels, config)`, and
`calculate_bp4d_au_metrics(preds, labels, config)`.

## Input representation

The neural test-output pickle has four required top-level keys:

| Key | Meaning |
|---|---|
| `predictions` | mapping trial/video id -> mapping chunk id -> tensor/array |
| `labels` | same structure and chunk alignment as `predictions` |
| `label_type` | normally `DiffNormalized`, `Raw`, or `Standardized` |
| `fs` | video sampling rate in frames/s |

Chunks are sorted by their keys and concatenated along their first dimension;
metric evaluation then flattens to one signal per trial. Align prediction and
label lengths before metric work. Do not assume pickle values are NumPy arrays:
repository trainers commonly save PyTorch tensors. A portable reader should
convert tensor-like values with `detach().cpu().numpy()` when available.

`LABEL_TYPE` controls `diff_flag`: `DiffNormalized` means the signal is a first
derivative and requires cumulative summation; `Raw` and `Standardized` are
already signal values and do not. This flag is about the saved signal, not the
input image `DATA_TYPE`.

## PPG per-video processing

The source-level signature is:

```text
calculate_metric_per_video(
    predictions, labels, fs=30, diff_flag=True,
    use_bandpass=True, hr_method='FFT'
) -> (hr_label, hr_pred, snr, macc)
```

Processing order:

1. If `diff_flag`, replace each signal with `cumsum(signal)` and detrend it;
   otherwise detrend the signal directly. Detrending uses the smoothness
   parameter `lambda_value=100`.
2. If `use_bandpass`, apply a first-order Butterworth bandpass. The source
   default is 0.6--3.3 Hz (36--198 bpm). Its comments recommend 0.75--2.5 Hz
   (45--150 bpm) when matching the toolbox paper. State which choice was used.
3. Compute MACC on the processed signals. It truncates both to the shorter
   length and scans nonnegative circular lags, taking the maximum absolute
   Pearson correlation.
4. For `hr_method='FFT'`, periodogram with an `nfft` equal to the next power of
   two and select the largest power in the selected band; multiply Hz by 60.
   For `hr_method='Peak'`, call peak detection and convert mean peak spacing to
   bpm: `60 / (mean(diff(peaks)) / fs)`.
5. Compute SNR using the label HR: integrate periodogram power around the first
   and second label harmonics, each within ±6 bpm, and divide by remaining power
   in the selected band. Convert the ratio with `10*log10`; zero remainder is
   returned as 0 by the source implementation.

Low-level signatures retained for compatibility are
`_calculate_fft_hr(ppg_signal, fs=60, low_pass=0.6, high_pass=3.3)`,
`_calculate_peak_hr(ppg_signal, fs)`,
`_compute_macc(pred_signal, gt_signal)`, and
`_calculate_SNR(pred_ppg_signal, hr_label, fs=30, low_pass=0.6,
high_pass=3.3)`.

## Windowing and aggregate metrics

`calculate_metrics(predictions, labels, config)` processes every trial and
window. With `INFERENCE.EVALUATION_WINDOW.USE_SMALLER_WINDOW=True`,
`WINDOW_SIZE` is in seconds and is multiplied by `TEST.DATA.FS`; otherwise the
whole video is one window. A final window with fewer than **9 samples** is
skipped because the signal processing pad length is too short. The configured
`INFERENCE.EVALUATION_METHOD` must be `FFT` or `peak detection`.

For each selected method, aggregate arrays of predicted and label HR are used
as follows:

- **MAE:** mean absolute error, with standard error of absolute errors.
- **RMSE:** square root of mean squared error. The source computes an error
  dispersion for its printed standard error; do not confuse that with RMSE.
- **MAPE:** mean `abs((pred-label)/label) * 100`; zero labels make this
  undefined and must be called out rather than silently presented as valid.
- **Pearson:** the off-diagonal coefficient from `corrcoef(pred, label)`.
- **SNR:** mean per-window SNR in dB.
- **MACC:** mean per-window maximum lagged correlation.
- **BA:** generate Bland--Altman scatter and difference plots.

`TEST.METRICS` examples are `['MAE', 'RMSE', 'MAPE', 'Pearson', 'SNR', 'BA']`.
`MACC` is supported by the PPG evaluator even when omitted from that example.
Pearson needs at least two nonconstant observations; MAPE needs nonzero labels.

## Bland--Altman outputs

The Bland--Altman object receives `(gold_std, new_measure, config,
averaged=True)`. It reports mean error, mean absolute error, mean squared error,
root mean squared error, correlation, and two 95% confidence limits. For
train/test modes its save directory is:

```text
LOG.PATH / TEST.DATA.EXP_DATA_NAME / bland_altman_plots
```

For an FFT evaluation, the filenames are
`<filename_id>_FFT_BlandAltman_ScatterPlot.pdf` and
`<filename_id>_FFT_BlandAltman_DifferencePlot.pdf`. For peak evaluation they
are the corresponding `_Peak_...` names. The respiration implementation uses
`FFT_BlandAltman_ScatterPlot.pdf`, `FFT_BlandAltman_DifferencePlot.pdf`, or
`Peak_BlandAltman_...` without a filename prefix, so separate experiments need
separate log directories. The scatter implementation adds random jitter to
points; treat it as a qualitative plot, not a byte-for-byte deterministic
artifact.

## BigSmall multitask metrics

`calculate_bvp_metrics` delegates to the PPG metrics above. Respiration uses:

```text
calculate_resp_metrics_per_video(
    predictions, labels, fs=30, diff_flag=True,
    use_bandpass=True, rr_method='FFT'
) -> (rr_label, rr_pred, snr)
```

It uses the same derivative/detrend sequence and peak-vs-FFT choice, but its
band is 0.13--0.5 Hz (8--30 breaths/min). FFT selects the dominant periodogram
bin in that band; peak mode converts mean peak spacing to breaths/min. SNR uses
the respiration band and the label RR as its harmonic reference. Aggregate
respiration metrics have MAE, RMSE, MAPE, Pearson, SNR, and BA variants.

The AU evaluator concatenates trials and evaluates the 12 BigSmall AUs:
`AU01`, `AU02`, `AU04`, `AU06`, `AU07`, `AU10`, `AU12`, `AU14`, `AU15`,
`AU17`, `AU23`, and `AU24`. Predictions are thresholded at 0.5. It reports
positive-class F1 and precision (and computes recall and accuracy) per AU,
plus `12AU_AvgF1`, `12AU_AvgPrec`, and `12AU_AvgAcc`, all as percentages. The
AU label layout is three-dimensional in the source (`labels[:, i, 0]`) while
predictions are indexed as `preds[:, i]`; verify shapes before concatenation.
This 12-AU classification subset is distinct from the 17 OpenFace intensity
columns used for motion analysis.

A source limitation is worth preserving in reports: the respiration aggregate
loop constructs windows but calls the per-video function with the full
`prediction` and `label` variables. If exact windowed respiration results
matter, check this behavior against the installed version and record whether
full-video or intended-window semantics were used.
