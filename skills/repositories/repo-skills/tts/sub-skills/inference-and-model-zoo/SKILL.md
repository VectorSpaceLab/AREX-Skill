---
name: inference-and-model-zoo
description: "Use Coqui TTS Python APIs and model registry for released-model
  inference, custom checkpoint loading, speaker/language selection, and safe
  model download decisions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MPL 2.0
---

# Inference and Model Zoo

Use this sub-skill when a task asks for Python `TTS.api.TTS` inference, released model discovery, model registry queries, custom checkpoint loading for inference, speaker/language selection, or deciding whether it is safe to load/download a pretrained Coqui TTS model.

## Start here

1. For exact Python signatures and object responsibilities, read [references/api-reference.md](references/api-reference.md).
2. For model-name grammar, registry counts, default vocoders, dynamic Fairseq/XTTS names, and license/TOS handling, read [references/model-zoo.md](references/model-zoo.md).
3. For copyable Python workflows, custom checkpoint patterns, XTTS/YourTTS voice cloning, and high-level streaming notes, read [references/workflows.md](references/workflows.md).
4. For predictable failures and recovery actions, read [references/troubleshooting.md](references/troubleshooting.md).

## Safe helper scripts

- Run [scripts/inspect_tts_models.py](scripts/inspect_tts_models.py) to count, filter, or query the installed registry. It is read-only and does not download model weights.
- Run [scripts/synthesize_text.py](scripts/synthesize_text.py) only after choosing a model. It supports `--dry-run`; when using a released `--model-name`, it refuses to load until `--allow-download` acknowledges possible downloads, cache writes, and TOS prompts.

## Route boundaries

- CLI flag catalogs, `tts` command construction, and persistent/demo server workflows belong in [../server-and-cli/SKILL.md](../server-and-cli/SKILL.md).
- Training, fine-tuning, dataset formatting, and config creation belong in [../training-config-data/SKILL.md](../training-config-data/SKILL.md).
- FreeVC source/target conversion details belong in [../voice-conversion/SKILL.md](../voice-conversion/SKILL.md). This sub-skill only cross-links `tts_with_vc`/`tts_with_vc_to_file` as API entry points.
- Audio resampling, statistics, VAD, vocoder training, and deep vocoder troubleshooting belong in [../vocoder-and-audio-tools/SKILL.md](../vocoder-and-audio-tools/SKILL.md).

## Operating cautions

- Coqui TTS 0.22.0 supports Python `>=3.9,<3.12`; do not treat Python 3.12+ or 3.13+ import behavior as supported.
- Model listing and metadata queries are safe. Loading a released model can download large files, update the model cache, check hashes, and prompt for license/TOS acceptance.
- CUDA is optional for this skill. Use CPU for metadata and tiny validations; request/confirm GPU only for practical synthesis speed, XTTS/Bark/Tortoise workloads, or user-requested performance checks.
