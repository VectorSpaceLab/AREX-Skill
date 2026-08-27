---
name: mmspeech
description: "Guides OFA MMSpeech staged ASR pretraining, evaluation, and
  audio-manifest validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# mmspeech

Use this sub-skill when a user wants to run OFA's MMSpeech speech-text pretraining or evaluation workflow, or validate the speech manifest and fbank configuration first.

## Trigger phrases

- "Run MMSpeech"
- "Validate a speech manifest"
- "What does the fbank YAML need?"
- "How do I set `train_stage` or `eval_wer`?"
- "Why does the speech workflow need phone dictionaries?"

## What this sub-skill owns

- MMSpeech stage-based training and evaluation,
- three-column speech/text/audio manifest layout,
- fbank configuration checks,
- phone dictionary and text-to-phone path guidance,
- WER troubleshooting.

## What it excludes

- caption, VQA, RefCOCO, OCR, ImageNet -> `vision-language-tasks`,
- Gigaword and GLUE -> `language-tasks`,
- pretraining vision-language mixtures -> `pretraining`,
- general launch mechanics -> `setup-and-command-building`.

## Read these files

- [references/workflows.md](references/workflows.md) for the stage layout and manifest shape.
- [references/troubleshooting.md](references/troubleshooting.md) for sample-rate, manifest, and backend problems.
- [scripts/validate_mmspeech_manifest.py](scripts/validate_mmspeech_manifest.py) for a safe preflight check.

## Typical workflow

1. Confirm the speech manifest and audio paths.
2. Check the fbank configuration against the expected sample rate.
3. Decide which stage of MMSpeech you are running.
4. Run the validator before the GPU job.

## Notes

- The workflow expects a speech-manifest contract, not a generic TSV.
- Audio processing depends on torchaudio/librosa/soundfile-style support.
- The evaluation path can report WER, so the manifest and text normalization matter.
