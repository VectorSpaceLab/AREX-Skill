---
name: py-audio-analysis
description: "Use pyAudioAnalysis for audio feature extraction, classical audio
  classification/regression, segmentation, diarization, legacy CLI commands, and
  audio I/O troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# py-audio-analysis

Use this repo skill when a task involves pyAudioAnalysis, classical audio/speech/music analysis, short- or mid-term acoustic features, sklearn-backed audio classifiers/regressors, segmentation, silence removal, speaker diarization, audio thumbnails, or pyAudioAnalysis command-line tasks.

## First checks

1. Confirm the package is installed. Public package name: `pyAudioAnalysis`; import package: `pyAudioAnalysis`.
2. For a safe installation and dependency check, run:
   ```bash
   python scripts/check_pyaudioanalysis_env.py --pretty
   ```
   Run it from this skill directory or give the script path explicitly.
3. If a task asks whether this skill matches a particular checkout or package version, read [`references/repo-provenance.md`](references/repo-provenance.md).
4. For the package/module map, dependency summary, and workflow overview, read [`references/package-overview.md`](references/package-overview.md).
5. For cross-cutting install/import, dependency, plotting, and legacy CLI failures, read [`references/troubleshooting.md`](references/troubleshooting.md).

Minimal import/API smoke for user environments:

```python
from pyAudioAnalysis import ShortTermFeatures, MidTermFeatures, audioBasicIO
```

Do not use `python -m pyAudioAnalysis.audioAnalysis` as the default CLI path: version 0.3.14 has legacy top-level imports in `audioAnalysis.py`. Use the `cli-and-io` sub-skill for safe installed-package CLI inspection or prefer Python APIs when possible.

## Route by task

### Feature extraction, spectrograms, chromagrams, beats

Read [`sub-skills/feature-extraction/SKILL.md`](sub-skills/feature-extraction/SKILL.md) when the user asks to:

- read audio and convert stereo to mono before analysis;
- compute `ShortTermFeatures.feature_extraction(...)` rows/names;
- compute `MidTermFeatures.mid_feature_extraction(...)` or directory feature matrices;
- generate spectrogram/chromagram arrays without GUI side effects;
- write feature matrices to NPY/CSV or debug unexpected feature shapes.

### Classification and regression

Read [`sub-skills/classification-regression/SKILL.md`](sub-skills/classification-regression/SKILL.md) when the user asks to:

- train a pyAudioAnalysis classifier from class-folder WAV data;
- classify one file or a folder with `svm`, `svm_rbf`, `knn`, `randomforest`, `gradientboosting`, or `extratrees`;
- train or apply audio regression models;
- understand model artifact files, `MEANS` sidecars, pickle safety, or sklearn compatibility;
- build a bounded synthetic smoke test for a classifier workflow.

### Segmentation, diarization, silence removal, thumbnails

Read [`sub-skills/segmentation-diarization/SKILL.md`](sub-skills/segmentation-diarization/SKILL.md) when the user asks to:

- train/use HMM segmentation from WAV + segment annotations;
- run mid-term classifier-based segmentation over an audio file;
- remove silence and interpret kept time spans;
- run speaker diarization or evaluate diarization purity;
- generate music thumbnails;
- split Audacity-style labels into per-label audio clips.

### Legacy CLI, audio formats, conversion, visualization, dependency probes

Read [`sub-skills/cli-and-io/SKILL.md`](sub-skills/cli-and-io/SKILL.md) when the user asks to:

- construct or inspect `audioAnalysis.py` commands and flags;
- troubleshoot `ModuleNotFoundError: ShortTermFeatures` from legacy CLI imports;
- check WAV/AIFF/MP3/AU/OGG support, `pydub`, `eyeD3`, `ffmpeg`, or `avconv`;
- convert media to WAV or reason about conversion side effects;
- run feature-visualization commands safely in a headless environment.

## Important operating constraints

- Required backend is CPU. The selected pyAudioAnalysis workflows are NumPy/SciPy/scikit-learn/hmmlearn workflows; no GPU/accelerator backend is required.
- MP3/media conversion is a system-dependency concern. WAV workflows can pass while MP3 conversion still needs `ffmpeg` or `avconv`.
- Many legacy CLI commands plot with Matplotlib or write files beside the input/model path. Prefer API calls with `plot=False` and explicit temporary output directories when automating.
- Training and model-loading APIs use pickle artifacts. Load only trusted model files.
- Time windows are usually seconds in high-level APIs/CLI arguments, but lower-level feature functions accept sample counts. The feature sub-skill calls this out explicitly.
- Several maintainer shell commands assume external datasets. Treat them as evidence for command shape, not as default runtime checks.

## Bundled helper scripts

- [`scripts/check_pyaudioanalysis_env.py`](scripts/check_pyaudioanalysis_env.py): shared import/dependency/legacy-CLI/feature smoke check.
- [`sub-skills/feature-extraction/scripts/feature_smoke.py`](sub-skills/feature-extraction/scripts/feature_smoke.py): synthetic or WAV-based feature matrix smoke.
- [`sub-skills/classification-regression/scripts/classification_smoke.py`](sub-skills/classification-regression/scripts/classification_smoke.py): bounded synthetic classifier train/classify smoke.
- [`sub-skills/segmentation-diarization/scripts/segmentation_smoke.py`](sub-skills/segmentation-diarization/scripts/segmentation_smoke.py): safe silence-removal and optional HMM/diarization smoke.
- [`sub-skills/cli-and-io/scripts/inspect_cli.py`](sub-skills/cli-and-io/scripts/inspect_cli.py): installed-package legacy CLI inspector.
- [`sub-skills/cli-and-io/scripts/audio_io_smoke.py`](sub-skills/cli-and-io/scripts/audio_io_smoke.py): audio I/O and optional media-tool probe.

## Avoid this skill when

- The task is deep neural audio training/inference (for example Whisper, NeMo, CLAP, PyTorch TTS, or diffusion audio); use a model-family-specific skill instead.
- The task is only generic NumPy/SciPy signal processing without pyAudioAnalysis APIs, model artifacts, data formats, or CLI behavior.
- The user is asking to edit this repository's source code, package metadata, or tests rather than use pyAudioAnalysis as a library; route to a Python repository-maintenance skill.
