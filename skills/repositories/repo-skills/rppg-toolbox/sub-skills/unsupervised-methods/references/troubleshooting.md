# Troubleshooting unsupervised inference

Use the narrowest failing unit first: config validation, loader item,
algorithm extraction, or metric window. Keep the method name and original
exception in the report.

## Configuration and dispatch

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Please set unsupervised method in yaml!` | `METHOD` is empty or omitted | Set one or more exact uppercase names. |
| `Not supported unsupervised method!` | Token is misspelled, lower-case, or a paper alias | Use only `POS`, `CHROM`, `ICA`, `GREEN`, `LGI`, `PBV`, `OMIT`. |
| pseudo-label `ValueError` | `USE_PSUEDO_PPG_LABEL` is true | Set it false; unsupervised methods never consume pseudo labels. |
| unsupported toolbox mode/dataset | Wrong mode or loader selector | Use `unsupervised_method` and one of the seven supported dataset names. |
| multiple methods stop after one failure | Dispatch is serial and does not isolate exceptions | Run the failing token alone, then restore the list. |

## Empty or missing data

- **No data for unsupervised method predicting:** the unsupervised dataloader
  is absent. Check mode, dataset name, raw path, cache path, and generated
  file list with the data-preparation skill.
- **Preprocessed directory does not exist:** either prepare the cache first or
  set preprocessing on for a deliberate first run. Do not point a config at a
  guessed cache directory.
- **File list missing:** the loader may try to build one from raw data. Confirm
  that the raw dataset and its loader-specific structure are valid.
- **Zero-length clip or label:** stop before method invocation. A valid clip
  has a positive time dimension and an aligned label sequence.
- **All windows ignored:** the extracted BVP (especially CHROM) or configured
  smaller window is below the nine-frame guard. Increase clip/window length;
  do not interpret an empty metric array as a good score.

## Shape, channel, and numerical failures

| Error pattern | Check | Recovery |
| --- | --- | --- |
| transpose/axis/index error | Item is not `(T,H,W,C)` or has fewer than 3 channels | Set `DATA_FORMAT: NDHWC`; inspect the post-loader item and first three channels. |
| NaN/Inf in BVP | Empty/constant RGB, zero channel mean, bad crop, or transformed data | Use `DATA_TYPE: ['Raw']`, inspect RGB finite-ness and spatial means, then fix upstream crop/exposure. |
| `padlen`/`filtfilt` error | Too few frames for POS/CHROM/ICA or evaluation filter | Increase `CHUNK_LENGTH`/video length; use the code's nine-frame guard only as a lower bound, not a target. |
| singular matrix / `solve` failure | PBV covariance is singular or nearly singular | Check RGB means and temporal rank; use real varied RGB input, not a constant synthetic clip. |
| ICA eigendecomposition/normalization failure | RGB channels have zero variance, poor rank, or too few observations | Confirm finite, non-collinear RGB trajectories and enough frames; test GREEN first. |
| LGI/OMIT QR/SVD shape error | Missing RGB channel or time dimension too short | Restore `(T,H,W,3)` and at least three RGB channels; increase frames. |
| finite but flat BVP | No pulse variation, over-aggressive crop, lighting/motion artifact | Treat as signal-quality failure; compare raw spatial averages and try a different clip/method. |

Do not “repair” a CHW array by guessing a transpose in a generated config. The
predictor always takes the last axis as channels.

## Sampling rate and filtering

`FS` is both a physical sampling rate and a filter parameter. Verify it is the
actual video rate and positive. POS uses an upper extraction edge near 3 Hz;
CHROM and ICA use one near 2.5 Hz. The evaluator uses approximately 0.6--3.3
Hz. If an upper edge is not below Nyquist, filter design fails or is invalid.
A wrong but numerically accepted `FS` produces wrong BPM, window sizes, and SNR.

## Evaluation failures

- **`Inference evaluation method name wrong!`:** use exact `FFT` or exact
  lower-case `peak detection`.
- **Peak detection error or NaN HR:** the window has fewer than two usable
  peaks or nearly uniform/noisy morphology. Use FFT for diagnosis, lengthen the
  window, and inspect the BVP/label quality.
- **FFT error or implausible HR:** the signal is too short for useful spectral
  resolution, has no energy in 0.6--3.3 Hz, or `FS` is wrong. Increase the
  window and confirm a plausible pulse band.
- **MAPE warning/Inf:** the label HR or label signal is zero/invalid. Check
  label representation and alignment; do not suppress the warning.
- **Pearson/MACC warning:** there are too few observations or a constant
  series. First confirm that windows survived and that both series vary.
- **BA plotting failure:** BA requires non-empty, finite HR arrays and can
  require enough observations for covariance-density plotting. Remove `BA`
  while isolating signal extraction, then restore it after metrics are valid.
- **No output in `saved_outputs`:** this is not necessarily a failure. The
  predictor computes and prints metrics; BA plots go to the experiment's
  Bland--Altman directory. It does not promise serialized BVP output there.

## Recovery order

1. Run `python scripts/unsupervised_smoke.py --help`, then its default check.
2. Set one method, `DATA_TYPE: ['Raw']`, `DATA_FORMAT: NDHWC`, and `FFT`.
3. Verify `FS`, clip length, RGB/label finite-ness, and label alignment.
4. Run GREEN to separate loader failures from filter/linear-algebra failures.
5. Add filtered/projection methods one at a time; use longer clips for CHROM,
   POS, and ICA and varied RGB for PBV/ICA.
6. Enable smaller windows and peak detection only after full-window FFT works.
7. Add aggregate metrics and BA last. Keep the original failure and all
   configuration values in the run note.
