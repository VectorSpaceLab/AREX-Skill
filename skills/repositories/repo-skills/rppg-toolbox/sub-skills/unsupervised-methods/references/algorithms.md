# Algorithm reference

## Shared input reduction

For each loader item, the unsupervised predictor takes the first three channels
of an NDHWC clip: `(T, H, W, C) -> (T, H, W, 3)`. Each method reduces each
frame to spatially averaged RGB. Consequently, spatially detailed frames are
useful only insofar as their RGB averages carry pulse and motion information.
The methods do not consume the label array.

The codebase implements these exact public names:

- `POS`: `POS_WANG(frames, fs)`.
- `CHROM`: `CHROME_DEHAAN(frames, FS)`.
- `ICA`: `ICA_POH(frames, FS)`.
- `GREEN`: `GREEN(frames)`.
- `LGI`: `LGI(frames)`.
- `PBV`: `PBV(frames)`.
- `OMIT`: `OMIT(frames)`.

The dispatch layer accepts only those uppercase tokens. It calls the selected
method once for each clip and repeats the entire dataset pass for every token
in `UNSUPERVISED.METHOD`.

## POS (Wang)

POS computes normalized RGB over rolling windows of `ceil(1.6 * FS)` frames,
projects the chrominance components, combines them using their standard
-deviation ratio, accumulates overlapping windows, detrends, and applies a
first-order bandpass around 0.75--3 Hz. It needs a configured `FS`, RGB data,
and enough frames to fill at least one rolling window plus the filter margin.

Typical symptoms:

- `FS <= 0` or an upper pass edge at/above Nyquist causes a filter-design
  error.
- A clip shorter than the rolling window returns mostly/all zeros and then can
  fail evaluation.
- Constant channels make the normalization or standard-deviation ratio
  undefined. Check exposure, face crop, and raw RGB channels before tuning
  metrics.

## CHROM (De Haan)

CHROM averages RGB, normalizes each window by its RGB baseline, forms two
chrominance combinations, bandpasses them at approximately 0.7--2.5 Hz,
scales one by the other channel's standard deviation, applies a Hann window,
and overlap-adds the result. Its fixed window is 1.6 seconds, rounded up to an
even frame count. The returned BVP can be shorter than the input because the
implementation allocates only its completed overlap-add length; evaluation
must therefore tolerate the BVP/label length difference.

Typical symptoms:

- `filtfilt` padding errors mean a CHROM window is too short; increase clip
  length or use a real sampling rate.
- Division by zero or NaN values indicate a zero RGB baseline or no variation
  in one chrominance component.
- A low-quality or strongly clipped face signal can produce a finite but
  physiologically meaningless BVP. Use FFT first and inspect signal quality.

## ICA (Poh)

ICA detrends each spatially averaged RGB channel with a high smoothing
parameter, centers and scales the channels, separates three components with a
JADE-style blind-source-separation routine, chooses the component with the
largest normalized spectral peak, and bandpasses it at approximately
0.7--2.5 Hz. `FS` is required for frequency selection and filtering.

ICA is more sensitive than GREEN to rank and signal length. It needs at least
three observations/channels in a well-conditioned RGB sequence and enough
frames for detrending, spectral selection, and `filtfilt`. Constant or
collinear channels can lead to singular matrices, zero variance, invalid
normalization, or ambiguous source selection. Treat an ICA failure as a
signal-conditioning problem before treating it as a configuration problem.

## GREEN

GREEN returns the averaged green channel directly. It does not receive `FS`
and does not apply its own temporal bandpass. The common evaluator later
filters the returned BVP and labels and uses the configured `FS` for HR.
GREEN is the easiest method for checking whether the loader provides finite
RGB frames, but it still fails on empty/invalid input and is not robust to
lighting or motion artifacts.

## LGI

LGI performs an SVD over the processed RGB trajectory, builds a projection
orthogonal to the dominant spatial direction, and returns the projected green
coordinate as BVP. It does not receive `FS`. It assumes a finite RGB trajectory
with enough temporal variation for a meaningful spatial decomposition. At
least three RGB channels are required; a rank-deficient or malformed input can
produce shape or linear-algebra errors. No heart-rate quality is implied by a
finite output.

## PBV

PBV normalizes each RGB trajectory by its channel mean, estimates a pulse
signature from channel standard deviations, constructs per-sample covariance
matrices, solves a linear system, and combines the result into a BVP. It does
not receive `FS`. It is the method most likely to expose singular covariance
from constant, nearly constant, or excessively short synthetic clips. A small
amount of natural RGB variation is not a substitute for a good real face
signal; it merely keeps the numerical system defined.

When PBV fails with a solve, divide, or non-finite-value error, check channel
order, RGB scale, zero/near-zero means, and temporal variation. Do not swap
channels to hide a bad loader layout.

## OMIT

OMIT averages RGB, takes an orthogonal QR basis of the RGB-by-time matrix,
projects away the first basis vector, and selects the second projected channel
as BVP. It does not receive `FS`. The input needs at least three RGB channels
and enough frames for the QR operation; finite output alone does not establish
pulse quality. Short clips, rank deficiency, and bad channel dimensions are
common failure causes.

## Frequency and metric contract

Extraction and evaluation use different responsibilities:

1. POS/CHROM/ICA use `FS` during extraction; GREEN/LGI/PBV/OMIT do not.
2. The evaluator detrends and applies a first-order bandpass approximately
   0.6--3.3 Hz to BVP and labels.
3. `FFT` uses a next-power-of-two periodogram and selects the strongest bin in
   that band. `peak detection` finds local peaks and computes BPM from mean
   inter-peak spacing.
4. `SNR` compares power near the label's first and second harmonics with the
   remainder of the evaluation band. `MACC` is the maximum lagged correlation.
5. `MAE`, `RMSE`, `MAPE`, and `Pearson` compare predicted and label HR. A metric
   containing `BA` requests Bland--Altman plots.

A clip that passes an algorithm but produces no valid evaluation windows is not
an overall success. Report extraction and evaluation failures separately.
