---
name: segmentation-diarization
description: "HMM and classifier-based segmentation, silence removal, speaker
  diarization, music thumbnailing, and Audacity annotation splitting for
  pyAudioAnalysis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Segmentation and diarization

Use this sub-skill when the task lives in time-aligned segmentation, speaker
clustering, silence pruning, thumbnailing, or annotation slicing.

## Route here
- Train or reuse HMM segmentation from labeled WAVs or annotated folders.
- Run mid-term classifier-based segmentation and folder-level evaluation.
- Remove silence from a signal and inspect the kept spans.
- Run speaker diarization and score cluster purity.
- Find music thumbnails from self-similarity.
- Split Audacity-style annotations into per-label WAV clips.

## Route elsewhere
- Clip-level classifier or regressor training -> `classification-regression`.
- Raw short- or mid-term feature extraction -> `feature-extraction`.
- CLI flag catalogs, media conversion, or legacy wrapper plumbing -> `cli-and-io`.

## Covered APIs
- `train_hmm_from_file`
- `train_hmm_from_directory`
- `hmm_segmentation`
- `mid_term_file_classification`
- `evaluate_segmentation_classification_dir`
- `silence_removal`
- `speaker_diarization`
- `speaker_diarization_evaluation`
- `music_thumbnailing`
- `annotation2files`
- `annotation2folders`
- `folderAnnotation2folders`

## Read next
- [API reference](references/api-reference.md)
- [Workflows](references/workflows.md)
- [Data formats](references/data-formats.md)
- [Troubleshooting](references/troubleshooting.md)
- [Smoke script](scripts/segmentation_smoke.py)

## Operating notes
- Prefer WAV inputs and tab-separated `.segments` sidecars with seconds as the
  time unit.
- Keep plotting flags off in headless or batch runs.
- HMM model files are the pickle stream written by the HMM trainers.
- Silence-removal and thumbnail CLI wrappers emit derived audio files; use the
  API directly when you want no file side effects.
- The legacy `audioAnalysis.py` and `audacityAnnotation2WAVs.py` entry points
  are summarized in the references; this skill tree uses bundled package
  imports and the smoke script instead.
