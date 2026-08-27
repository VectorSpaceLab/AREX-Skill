---
name: unsupervised-methods
description: "Author and run rPPG-Toolbox unsupervised_method configurations
  with POS, CHROM, ICA, GREEN, LGI, PBV, or OMIT, then diagnose signal, shape,
  sampling-rate, and evaluation-window failures."
disable-model-invocation: true
metadata: { disco-role: operating }
license: NOASSERTION
---

# Unsupervised rPPG methods

Use this skill when the toolbox must extract a blood-volume-pulse (BVP) signal
from face-video color data without a trained neural model. This is an
inference workflow: it selects one or more supported algorithms, obtains
preprocessed clips through the dataset loader, computes a BVP, and evaluates
heart rate against the loader's label signal. It does not train a model or
replace dataset/cache preparation.

## Fast route

1. Follow [data preparation](../data-preparation/SKILL.md) to create or reuse a
   valid cached clip/file-list set. Do not hand-build loader batches unless
   debugging the algorithm boundary.
2. Set `TOOLBOX_MODE: "unsupervised_method"`, a non-empty
   `UNSUPERVISED.METHOD` list, a supported dataset, and the actual video
   sampling rate (`UNSUPERVISED.DATA.FS`). Use `DATA_FORMAT: NDHWC`.
3. Start with `DATA_TYPE: ['Raw']`, a label representation appropriate for the
   dataset, `USE_PSUEDO_PPG_LABEL: False`, and a clip long enough for the
   selected method and evaluation filter. See [workflows](references/workflows.md).
4. Select `INFERENCE.EVALUATION_METHOD: "FFT"` or the exact string
   `"peak detection"`; choose only supported metrics. Use the smoke script
   before spending time on a dataset run:
   `python scripts/unsupervised_smoke.py --help`.
5. Run one method first. Add methods only after the first BVP and evaluation
   window are valid; dispatch runs the complete unsupervised dataloader once
   per method in list order.
6. If no windows reach evaluation, inspect shape, frame count, `FS`, label
   length, and the failure matrix in [troubleshooting](references/troubleshooting.md).
   For plots/formulas, follow [evaluation and visualization](../evaluation-and-visualization/SKILL.md).

## Contract at the algorithm boundary

The loader returns a batched tensor. For the supported NDHWC convention, an
individual item is `D x H x W x C` (frames/depth, height, width, channels).
The predictor converts it to an array and passes `data[..., :3]` to the chosen
method. Therefore the method input is RGB frames shaped `(frames, height,
width, 3)`, with the first three channels being the RGB video. Do not pass a
label, a batch dimension, CHW data, or a time-major three-channel array.

`DATA_TYPE` controls video preprocessing, not the evaluation algorithm. `Raw`
keeps frames; `DiffNormalized` computes frame differences and normalizes them;
`Standardized` z-scores the video. Multiple entries are concatenated along the
channel axis, but this predictor intentionally takes only the first three
channels. For reliable traditional methods, use `['Raw']`; if another type is
needed for a controlled experiment, verify that its first three channels are
still the intended RGB signal.

`LABEL_TYPE` controls only the label loaded for comparison (`Raw`,
`DiffNormalized`, or `Standardized`). It is not passed to POS/CHROM/ICA/GREEN/
LGI/PBV/OMIT. Unsupervised mode rejects pseudo-PPG labels, so keep
`USE_PSUEDO_PPG_LABEL` false. Labels and BVP must cover the same time interval;
preprocessing and chunking should preserve that alignment.

## Method selection

The exact accepted names and dispatch arguments are:

| `UNSUPERVISED.METHOD` | Dispatch | `FS` passed to method | Practical choice |
| --- | --- | --- | --- |
| `POS` | `POS_WANG(frames, fs)` | yes | RGB projection with rolling 1.6-second windows |
| `CHROM` | `CHROME_DEHAAN(frames, FS)` | yes | chrominance projection with 1.6-second windows |
| `ICA` | `ICA_POH(frames, FS)` | yes | blind source separation; needs non-degenerate RGB variation |
| `GREEN` | `GREEN(frames)` | no | direct green-channel trace; simplest smoke baseline |
| `LGI` | `LGI(frames)` | no | local group-invariant projection; RGB rank matters |
| `PBV` | `PBV(frames)` | no | blood-volume-pulse signature; covariance must be solvable |
| `OMIT` | `OMIT(frames)` | no | orthogonal projection; at least three RGB observations are needed |

Names are case-sensitive. The list must contain one or more of these exact
strings. An empty list raises a configuration error; any other string raises
`Not supported unsupervised method!`. The optional `OMIT` method is dispatched
like the others even though some older examples list only six methods.

POS and CHROM/ICA use the configured `FS` internally. CHROM and ICA bandpass
around 0.7--2.5 Hz; POS filters around 0.75--3 Hz. `FS` must be positive and
high enough that the filter upper edge is below Nyquist (normal dataset
configurations use 30 or 35 Hz). GREEN, LGI, PBV, and OMIT do not receive `FS`
during extraction, but their outputs are still evaluated at that sampling
rate. These methods assume meaningful, finite, positive-ish RGB averages and
sufficient temporal variation; a constant, empty, NaN, or nearly zero signal
is not a valid algorithm test.

## Evaluation and outputs

The predictor extracts one BVP per clip, then evaluates windows. With
`USE_SMALLER_WINDOW: false`, it uses the available video length; with true, the
window is `WINDOW_SIZE * FS` frames, capped at the video length. The loop also
uses the BVP length, which can be shorter than the input for CHROM. Windows with
fewer than 9 frames are explicitly ignored, and very short windows can still
fail the downstream `filtfilt`/peak-detection requirements. Prefer more than
nine frames after extraction and substantially longer clips for meaningful HR
resolution; the 1.6-second POS/CHROM windows and FFT bins make short clips
especially fragile.

`FFT` uses a periodogram and selects the strongest frequency in approximately
0.6--3.3 Hz before converting to BPM. Exact `peak detection` uses detected
sample peaks and mean inter-peak spacing. FFT is generally the safer first
check on short/noisy clips; peak detection requires at least two plausible
peaks and clean enough morphology. Shared evaluation detrends and bandpasses
both BVP and labels before computing metrics.

Supported metrics are `MAE`, `RMSE`, `MAPE`, `Pearson`, `SNR`, `MACC`, and any
metric containing `BA` (normally `BA`). An unknown metric raises an error.
`SNR` and `MACC` are computed alongside HR; `BA` creates Bland--Altman plots.
The configuration derives `UNSUPERVISED.OUTPUT_SAVE_DIR` under the experiment's
log path with a `saved_outputs` suffix, but the predictor's visible unsupervised
artifact is the method/dataset-named Bland--Altman plot directory under the
same experiment when `BA` is requested. Do not assume a per-video BVP file is
written there.

## Boundaries and recovery

This sub-skill deliberately does not describe loader internals, raw dataset
layouts, face detection, cache generation, or visualization formulas. Use the
linked sibling skills for those concerns. When a method fails, preserve the
original exception and identify the method, clip shape, `FS`, and effective
window before changing preprocessing. Do not “fix” an invalid RGB layout by
silently transposing it.

See [algorithm details](references/algorithms.md) for method assumptions and
failure signatures, [workflow details](references/workflows.md) for config and
run sequencing, and [troubleshooting](references/troubleshooting.md) for a
failure-oriented decision tree. The bundled smoke check is intentionally
source-independent and deterministic; it checks the RGB/FS/output contract,
not scientific accuracy or parity with a real dataset.
