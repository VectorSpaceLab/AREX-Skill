---
name: training-config-data
description: "Prepare Coqui TTS datasets, Coqpit configs, tokenizer or
  phonemizer settings, and safe training or fine-tuning plans without launching
  expensive training by default."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MPL 2.0
---

# Training, Configuration, and Data Sub-Skill

Use this sub-skill when a task asks how to prepare a Coqui TTS dataset, validate a TTS model config, adapt a training or fine-tuning workflow, inspect tokenizer/phonemizer coverage, or compute speaker embeddings/d-vectors safely.

## Read order

1. Start with [references/configuration.md](references/configuration.md) for Coqpit config hierarchy, model config registration, and the minimum fields to validate before training.
2. Use [references/data-formats.md](references/data-formats.md) for formatter schemas, LJSpeech/Common Voice/custom dataset layouts, and sample dictionaries returned by dataset loaders.
3. Use [references/training-workflows.md](references/training-workflows.md) to turn a validated config into a training command template and to interpret Trainer flags.
4. Use [references/fine-tuning.md](references/fine-tuning.md) for released-checkpoint fine-tuning, XTTS GPT fine-tuning caveats, and safe override patterns.
5. Use [references/api-reference.md](references/api-reference.md) for compact API/CLI signatures and bundled helper contracts.
6. Use [references/troubleshooting.md](references/troubleshooting.md) for workflow-specific failures; use [../../references/troubleshooting.md](../../references/troubleshooting.md) for package install/import/runtime issues.

## Safe bundled helpers

- `scripts/validate_tts_config.py`: load a JSON/YAML config with Coqpit, check model registration, inspect dataset/audio paths, and optionally load dataset samples. It never initializes a model or starts training.
- `scripts/find_unique_symbols.py`: inspect unique graphemes or phonemes from configured datasets. Phoneme mode reports missing phonemizer/espeak dependencies clearly.
- `scripts/compute_speaker_embeddings.py`: a safe wrapper around speaker embedding generation. It requires explicit encoder model/config/dataset arguments and only computes embeddings when `--run` is passed.

Run helpers with `--help` first and keep outputs in a user-chosen working directory, not in the skill tree.

## Boundaries and routing

- For vocoder training, audio statistics, resampling, silence trimming, spectrogram extraction, and vocoder-specific audio configuration, route to [../vocoder-and-audio-tools/SKILL.md](../vocoder-and-audio-tools/SKILL.md).
- For inference from a trained checkpoint through Python APIs or the model zoo, route to [../inference-and-model-zoo/SKILL.md](../inference-and-model-zoo/SKILL.md).
- For installed `tts` or `tts-server` command syntax, route to [../server-and-cli/SKILL.md](../server-and-cli/SKILL.md).
- For FreeVC source/target voice conversion workflows, route to [../voice-conversion/SKILL.md](../voice-conversion/SKILL.md).
- Maintainer documentation-sync utilities are excluded: they mutate package documentation and are not runtime training/config/data operations.

## Operating rules

- Do not run full training, fine-tuning, model downloads, or dataset downloads unless the user explicitly asks and accepts time, compute, disk, and network cost.
- Prefer config validation, formatter dry-runs, unique-symbol scans, and command construction as the default response.
- Treat Python `>=3.9,<3.12` as the supported package range.
- For phoneme workflows, expect optional language frontend/system dependencies such as `gruut`, `espeak`, or `espeak-ng`.
- Keep vocoder and inference concerns routed rather than duplicating those workflows here.
