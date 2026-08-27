---
name: audio-asr
description: "Routes AXLearn audio feature extraction, ASR, Conformer,
  LibriSpeech, and WER workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# audio-asr

Use this sub-skill for AXLearn's speech and ASR workflows.

Typical triggers:

- Conformer, LibriSpeech, `ASREncoder`, `ASRModel`, or speech feature extraction.
- `LogMelFrontend`, `SpeechFeatureLayer`, `speech_input`, `text_input`, or `WordErrorRateMetricCalculator`.
- Streaming layer helpers or ASR decode / evaluation utilities.

If the task is only about the shared trainer runtime, use `../training-core/` first.
If the task is about `axlearn gcp ...`, use `../cli-cloud/`.

## What to read

- `references/workflows.md` for LibriSpeech and ASR workflow structure.
- `references/troubleshooting.md` for tokenizer, fake-data, and feature-extraction failures.
- `scripts/inspect_audio_configs.py` for a safe config-inspection helper.

## Common routes

### Inspect the LibriSpeech trainer catalog

```bash
python scripts/inspect_audio_configs.py --module axlearn.experiments.audio.conformer.librispeech_trainer --config conformer-test-ctc --data-dir FAKE
```

### Run a CPU-safe fake-data probe

Set `DATA_DIR=FAKE` so the LibriSpeech helpers use synthetic speech/text examples instead of TFDS-backed data.

### Inspect ASR building blocks

The core pieces are:

- `LogMelFrontend` for log-mel feature extraction.
- `SpeechFeatureLayer` for feature extraction + subsampling.
- `ASREncoder` and `ASRModel` for the encoder-decoder stack.
- `WordErrorRateMetricCalculator` for decoding-based evaluation.

## Decision points

- Choose this sub-skill when the task names speech, ASR, Conformer, LibriSpeech, or WER.
- Keep shared trainer mechanics in `training-core`.
- Do not route GPT or vision questions here just because they also use `SpmdTrainer`.
