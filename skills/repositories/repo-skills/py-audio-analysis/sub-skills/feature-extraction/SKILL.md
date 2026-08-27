---
name: feature-extraction
description: "Routes pyAudioAnalysis short-term, mid-term, spectrogram,
  chromagram, beat, and matrix export feature-extraction work."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# feature-extraction

Use this sub-skill when the user needs pyAudioAnalysis 0.3.14 acoustic feature extraction from an in-memory signal or audio file: short-term features, mid-term statistics, spectrograms, chromagrams, optional beat features, or matrix export to NPY/CSV.

## Route here for

- Reading a WAV/audio file into `(sampling_rate, signal)` and converting stereo to mono before feature extraction.
- `ShortTermFeatures.feature_extraction(...)` and its feature-name/shape contract.
- `ShortTermFeatures.spectrogram(...)` and `ShortTermFeatures.chromagram(...)` representations.
- `MidTermFeatures.mid_feature_extraction(...)`, directory-level mid-term feature matrices, and `mid_feature_extraction_to_file(...)` NPY/CSV outputs.
- Sanity-checking feature shapes, finite values, and feature-name row counts with the bundled smoke helper.

## Route elsewhere

- Classifier or regression training, model files, prediction, or evaluation: route to `classification-regression`.
- Segmentation, diarization, silence removal, thumbnailing, or HMM workflows: route to `segmentation-diarization`.
- Broad command-line usage, MP3/media conversion, resampling, or package I/O setup beyond feature extraction: route to `cli-and-io`.

## Read these bundled files

- [API reference](references/api-reference.md) for supported imports, signatures, units, return shapes, feature names, and export behavior.
- [Workflows](references/workflows.md) for copy-safe recipes that turn arrays or WAV files into short/mid/spectral/chroma matrices and NPY/CSV outputs.
- [Troubleshooting](references/troubleshooting.md) for window/step unit mistakes, stereo handling, too-short or silent audio, plot/display issues, MP3 dependencies, and unexpected shapes.

## Bundled helper

Run the smoke helper before relying on an environment or after changing parameters:

```bash
python scripts/feature_smoke.py --help
python scripts/feature_smoke.py --duration 2.0 --short-window 0.05 --short-step 0.05 --mid-window 1.0 --mid-step 1.0
python scripts/feature_smoke.py --input-wav example.wav --output-prefix features/example --store-csv
```

The helper synthesizes a tone or reads a WAV file, runs short-term and mid-term extraction, checks that feature rows match feature names, optionally writes matrices, and prints a JSON summary. It is a smoke/inspection utility, not a replacement for downstream classification or segmentation workflows.

## Evidence distilled

This sub-skill distills pyAudioAnalysis 0.3.14 package metadata, README feature-extraction examples, feature module signatures and behavior, legacy CLI wrappers for spectrogram/chromagram/feature extraction, and feature-extraction pytest expectations. Runtime guidance is self-contained; do not reopen or run the original repository to use this sub-skill.
