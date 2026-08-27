---
name: vocoder-and-audio-tools
description: "Use Coqui TTS vocoder configs, training routes, and safe audio
  preprocessing helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MPL 2.0
---

# Vocoder and Audio Tools

Use this sub-skill when a task is about Coqui TTS vocoder configuration,
vocoder checkpoint compatibility, vocoder training preparation, or reusable
audio preprocessing/analysis utilities.

## Route by task

| If the user needs... | Read/use |
| --- | --- |
| Vocoder model names, config classes, `setup_model`, default pairing, or mel compatibility checks | [references/vocoder-reference.md](references/vocoder-reference.md) and [`scripts/validate_vocoder_config.py`](scripts/validate_vocoder_config.py) |
| AudioProcessor settings, dataset statistics, safe resampling, VAD trimming, or spectrogram preconditions | [references/audio-tools.md](references/audio-tools.md) and the bundled audio helper scripts |
| Vocoder training command construction, HifiGAN recipe patterns, resume/restore semantics, or Trainer flags | [references/training-workflows.md](references/training-workflows.md) |
| Audio/vocoder failure diagnosis | [references/troubleshooting.md](references/troubleshooting.md), then the root cross-cutting troubleshooting reference when present |

## Bundled helper scripts

Run helpers from the generated TTS skill tree; they use the installed `TTS`
package and user-provided configs/data, not the original repository checkout.

- [`scripts/validate_vocoder_config.py`](scripts/validate_vocoder_config.py): load a vocoder config, validate audio/data/feature/statistics fields, optionally compare against a TTS config, and optionally instantiate the vocoder model without training.
- [`scripts/compute_audio_stats.py`](scripts/compute_audio_stats.py): compute bounded mel/linear mean-variance statistics for a wav directory using a Coqui audio config.
- [`scripts/resample_audio_dir.py`](scripts/resample_audio_dir.py): safely resample a directory into a separate output tree by default; in-place mutation requires `--in-place`.
- [`scripts/trim_silence_vad.py`](scripts/trim_silence_vad.py): wrap Silero/Coqui VAD trimming with explicit cache/network acknowledgement; `--help` does not download a model.

## Boundaries

- Route TTS model config, dataset formatter, tokenizer, phonemizer, speaker embedding, and TTS training tasks to [../training-config-data/SKILL.md](../training-config-data/SKILL.md).
- Route installed `tts` synthesis commands, server commands, and command-line synthesis with a selected vocoder to [../server-and-cli/SKILL.md](../server-and-cli/SKILL.md).
- Route Python model-registry and public `TTS.api.TTS` inference tasks to [../inference-and-model-zoo/SKILL.md](../inference-and-model-zoo/SKILL.md).
- Route FreeVC and source/target/reference voice-conversion workflows to [../voice-conversion/SKILL.md](../voice-conversion/SKILL.md).

Do not run full vocoder training, model-zoo downloads, VAD first-download runs, or native repository tests unless a later verification task explicitly authorizes that cost.
