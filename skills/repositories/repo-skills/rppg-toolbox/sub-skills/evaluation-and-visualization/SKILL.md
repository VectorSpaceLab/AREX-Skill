---
name: evaluation-and-visualization
description: "Evaluate rPPG and BigSmall outputs, inspect saved signals and
  preprocessed arrays, and choose portable motion-analysis visualizations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Evaluation and visualization

Use this sub-skill after a model or unsupervised method has produced signals. It
turns saved predictions into HR/RR metrics, compares traces, inspects cached
arrays, or summarizes OpenFace motion. It does not select or run a model, build
data caches, or reproduce training.

## Choose a path

1. **Metrics:** use the repository evaluator when the checkout and its config
   are available. Preserve `LABEL_TYPE`, test `FS`, evaluation method, and
   window settings. The exact contracts and known implementation edge cases
   are in [evaluation-api.md](references/evaluation-api.md).
2. **Saved signal inspection:** use
   [`scripts/plot_saved_predictions.py`](scripts/plot_saved_predictions.py) for
   a noninteractive PNG/SVG/PDF plot. The pickle must contain `predictions`,
   `labels`, `label_type`, and `fs`; see [visualization.md](references/visualization.md).
3. **Preprocessed-array inspection:** use
   [`scripts/plot_preprocessed_arrays.py`](scripts/plot_preprocessed_arrays.py)
   for a static frame plus label time/frequency plot. It is the portable
   replacement for the interactive notebook; it accepts one input `.npy` and
   its matching label `.npy`.
4. **Motion:** if MP4s are needed, use
   [`scripts/convert_frames_to_mp4.py`](scripts/convert_frames_to_mp4.py), then
   run an already installed OpenFace `FeatureExtraction` executable outside
   this skill. Summarize two OpenFace CSV directories with
   [`scripts/summarize_openface_motion.py`](scripts/summarize_openface_motion.py).

Do not use a notebook, source-checkout import, bundled model, sample output,
or vendor/OpenFace code as a runtime dependency. The original motion workflow
needs OpenFace installed separately; it is not replaced by the converter.

## Evaluation guardrails

- `DiffNormalized` labels/predictions set `diff_flag=True`: cumulatively sum
  before detrending. `Raw` and `Standardized` set it to `False`.
- Pass the test sampling rate (`FS`, commonly 30) rather than assuming it.
- The evaluator can use `FFT` or `peak detection` (spelling is case-sensitive
  in the repository config). FFT searches the configured band; peak detection
  uses peak spacing. A window shorter than **9 samples is ignored**.
- The post-processing default band is 0.6--3.3 Hz; the source comments
  recommend 0.75--2.5 Hz for paper-style results. Keep the chosen band in the
  report. MACC is maximum absolute lagged correlation and SNR is reported in dB.
- Request `MAE`, `RMSE`, `MAPE`, `Pearson`, `SNR`, `MACC`, and/or `BA` as
  appropriate. Do not report undefined values from empty, constant, or
  too-short arrays as successful evaluation; follow the failure guidance in
  [troubleshooting.md](references/troubleshooting.md).

## Output locations

Test output pickles are normally under the configured log path at the test
experiment's `saved_test_outputs` directory. Bland--Altman files are normally
under the log path, experiment name, and `bland_altman_plots`. Exact filenames,
including FFT/Peak variants, are listed in [evaluation-api.md](references/evaluation-api.md).
Static helper outputs go only where `--output` names them; existing files are
never overwritten unless `--force` is explicitly supplied.

## Cross-skill boundaries

- Use [supervised-models](../supervised-models/SKILL.md) for producing neural
  predictions and understanding trainer output timing.
- Use [data-preparation](../data-preparation/SKILL.md) for cache filenames,
  preprocessing schema, and input/label alignment.
- Use [unsupervised-methods](../unsupervised-methods/SKILL.md) for selecting
  signal-processing algorithms before evaluation.
- Keep this sub-skill focused on evaluation, inspection, plotting, and motion;
  do not duplicate those setup workflows.

## Portable commands

```bash
python scripts/plot_saved_predictions.py --help
python scripts/plot_saved_predictions.py --input outputs.pickle --output signal.png --trial 0 --chunk-size 180 --chunk 0
python scripts/plot_preprocessed_arrays.py --input 000_input0.npy --label 000_label0.npy --output cache.png
python scripts/convert_frames_to_mp4.py --help
python scripts/convert_frames_to_mp4.py --mode ubfc-rppg --input-dir <dataset-root>/UBFC --output-dir <scratch-dir>/ubfc-mp4
python scripts/summarize_openface_motion.py --input-dir <scratch-dir>/openface-a --compare-dir <scratch-dir>/openface-b --output motion.png
```

All commands are local-only and noninteractive. Read the linked references
before changing bands, label transforms, AU definitions, or output paths.
