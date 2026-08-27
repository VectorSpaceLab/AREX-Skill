# Unsupervised workflows

## Minimal configuration shape

Start from a dataset-specific inference configuration, then make the paths and
sampling rate local to the run. The essential contract is:

```yaml
TOOLBOX_MODE: "unsupervised_method"
UNSUPERVISED:
  METHOD: ["POS"]
  METRICS: ["MAE", "RMSE", "SNR"]
  DATA:
    FS: 30
    DATASET: "<supported dataset>"
    DATA_FORMAT: "NDHWC"
    DATA_PATH: "<raw data path>"
    CACHED_PATH: "<cache root>"
    DO_PREPROCESS: false
    PREPROCESS:
      DATA_TYPE: ["Raw"]
      LABEL_TYPE: "Raw"
      USE_PSUEDO_PPG_LABEL: false
      DO_CHUNK: false
INFERENCE:
  EVALUATION_METHOD: "FFT"
  EVALUATION_WINDOW:
    USE_SMALLER_WINDOW: false
    WINDOW_SIZE: 10
```

`DATASET` selects one of the toolbox's dataset loader families: `UBFC-rPPG`,
`PURE`, `SCAMPS`, `MMPD`, `BP4DPlus`, `UBFC-PHYS`, or `iBVP`. The loader/cache
and dataset-specific preprocessing rules belong to the data-preparation
skill. Do not copy a raw dataset layout into this workflow.

The visible example configurations use `FS: 30` for PURE, UBFC-rPPG, MMPD,
and iBVP, and `FS: 35` for UBFC-PHYS. Use the actual source video's frame
rate, not a convenient default. `WINDOW_SIZE` is seconds and is multiplied by
`FS` at runtime.

## First-run sequence

1. **Prepare cache.** Follow the data-preparation skill. If preprocessing is
   requested, ensure the raw path, face detector backend, and cache are valid.
   On later runs set `DO_PREPROCESS: false` and reuse the generated file list.
2. **Validate shape.** The unsupervised predictor expects each item in NDHWC
   order and truncates to RGB with `[..., :3]`. Confirm the first three
   channels are finite RGB and that labels have the same frame interval.
3. **Smoke the numerical boundary.** Run
   `python scripts/unsupervised_smoke.py --frames 180 --fs 30`. This uses no
   dataset, download, credential, or output file. Use a larger `--frames`
   value if testing a long evaluation window.
4. **Run one method.** Choose `GREEN` to check basic frame/channel flow, then
   choose POS, CHROM, ICA, LGI, PBV, or OMIT according to the signal and
   numerical assumptions in [algorithms](algorithms.md).
5. **Select evaluation.** Use `FFT` for the first sanity run. Use exact
   `peak detection` only when the BVP and label have enough discernible peaks.
6. **Expand method list.** Once one method completes, set a list such as
   `["ICA", "POS", "CHROM", "GREEN", "LGI", "PBV", "OMIT"]`. The dispatcher
   runs methods serially in list order; one exception stops the run, so isolate
   a failing method by reducing the list.
7. **Read artifacts.** HR/quality values are printed. If `BA` is selected,
   Bland--Altman scatter and difference PDFs are created under the experiment's
   method/dataset plot directory. `saved_outputs` is configured, but this
   predictor does not promise per-video BVP files there.

## Windowing decisions

With `USE_SMALLER_WINDOW: false`, the effective window is the video length.
With true, each window is `WINDOW_SIZE * FS` frames, capped at the video
length. The evaluator iterates over the BVP length and slices labels to the
same interval. CHROM may return fewer samples than the input due to its
overlap-add allocation.

The implementation prints and ignores windows shorter than 9 frames. That is a
code guard, not a guarantee that nine frames can pass every `filtfilt`, FFT, or
peak operation. For a stable HR estimate, use substantially longer windows:
roughly several heart cycles and enough samples for a useful frequency bin.
When exploring short clips, disable BA and use a single finite metric only
after confirming that at least one window survives.

Smaller windows are useful for localized quality checks, but changing
`WINDOW_SIZE` changes FFT resolution, peak count, SNR harmonics, and the number
of observations used for aggregate metrics. Record `FS`, window seconds, and
whether the BVP was truncated when comparing runs.

## Data representation choices

- `DATA_FORMAT: NDHWC` is the compatible predictor boundary. Other loader
  formats are valid elsewhere in the toolbox but are not safe assumptions for
  this dispatch path.
- `DATA_TYPE: ['Raw']` preserves RGB intensities and matches all seven
  traditional methods. Concatenated types are sliced back to the first three
  channels, so do not expect transformed channels to be used unless you have
  explicitly verified their order.
- `LABEL_TYPE: Raw`, `DiffNormalized`, and `Standardized` affect only the
  evaluation target. Select the representation appropriate to the dataset and
  maintain time alignment with the clip.
- `USE_PSUEDO_PPG_LABEL: true` is invalid in unsupervised mode and is rejected
  during config update.
- `DO_CHUNK: false` keeps a complete video; `true` can be useful for bounded
  runs, but `CHUNK_LENGTH` must leave enough frames for the algorithm and
  evaluation. Dataset-specific examples use values such as 160--210 frames.

## Method isolation and diagnosis

When a multi-method run stops, rerun the same config with only the method named
in the last progress message. Record:

```text
method, dataset, FS, input shape, finite RGB?, extracted BVP length,
finite BVP?, evaluation method, effective window frames, first exception
```

If GREEN succeeds but a filtered method fails, investigate `FS`, length, and
channel variation. If all methods fail, investigate cache output, NDHWC shape,
first-three-channel selection, and empty/NaN clips before algorithm details.
If extraction succeeds but evaluation fails, use the evaluation-and-visualization
skill for metric formulas and inspect the nine-frame guard, filter padding,
peak count, and label alignment.
