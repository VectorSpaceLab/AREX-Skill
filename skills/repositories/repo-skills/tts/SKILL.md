---
name: tts
description: "Use Coqui TTS for released-model inference, the tts and tts-server
  commands, training and fine-tuning plans, vocoder/audio tooling, and FreeVC
  voice conversion workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MPL 2.0
---

# Coqui TTS

Use this skill for the Coqui TTS Python package and its installed console commands. It routes future agents to the right workflow without reopening the original repository.

## Start here

1. Read [references/package-overview.md](references/package-overview.md) for the package shape, public entry points, supported Python range, and verified runtime facts.
2. Run [scripts/check_tts_environment.py](scripts/check_tts_environment.py) to confirm the installed package, CLI help, registry access, and optional CUDA smoke in the current environment.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import/version/audio/cache/backend failures.
4. If the repo snapshot may be stale, read [references/repo-provenance.md](references/repo-provenance.md) before using or refreshing this skill.

## Install and import check

- Supported Python: `>=3.9, <3.12`.
- Recommended install for a released environment: `python -m pip install TTS==0.22.0`.
- If you are actively maintaining a matching checkout, an editable install such as `python -m pip install -e .` is acceptable, but the runtime skill itself must not depend on the checkout remaining present.
- Minimal smoke check:

```bash
python -c "import TTS; from TTS.api import TTS as TTSApi; print(TTS.__version__); print(TTSApi)"
```

- Safer full smoke check:

```bash
python skills/disco/tts/scripts/check_tts_environment.py
```

## Route map

- **Python inference and model zoo**: `TTS.api.TTS`, `ModelManager`, released-model loading, model-name grammar, custom checkpoint inference, `tts_with_vc`, XTTS/Fairseq/Bark/Tortoise naming cautions. Read [sub-skills/inference-and-model-zoo/SKILL.md](sub-skills/inference-and-model-zoo/SKILL.md).
- **Installed CLI and demo server**: `tts`, `tts-server`, command construction, parser flags, pipe output, model metadata, and safe local server usage. Read [sub-skills/server-and-cli/SKILL.md](sub-skills/server-and-cli/SKILL.md).
- **Training, configuration, and data**: dataset formatters, Coqpit configs, tokenizer/phonemizer setup, TTS training and fine-tuning plans, speaker embeddings, and recipe adaptation. Read [sub-skills/training-config-data/SKILL.md](sub-skills/training-config-data/SKILL.md).
- **Vocoder and audio tools**: vocoder configs/training, audio preprocessing, statistics, resampling, VAD trimming, and mel/audio compatibility. Read [sub-skills/vocoder-and-audio-tools/SKILL.md](sub-skills/vocoder-and-audio-tools/SKILL.md).
- **Voice conversion**: FreeVC and TTS-with-VC workflows using source/target/reference wavs. Read [sub-skills/voice-conversion/SKILL.md](sub-skills/voice-conversion/SKILL.md).

## When to read this skill versus a sub-skill

- Start at the root when the user only says "Coqui TTS", "TTS", `tts`, `tts-server`, `XTTS`, `FreeVC`, "voice cloning", "vocoder", "training", or "dataset formatting" and you need to route the request.
- Go directly to a sub-skill when the workflow is already specific, for example "run the CLI", "use the Python API", "prepare a training config", or "convert a voice with FreeVC".
- Use the root only for cross-cutting install/import checks, package provenance, and choosing the correct route.

## Cross-cutting notes

- Released models, model downloads, and some training workflows can touch network, cache, disk, or license/TOS prompts. Treat them as explicit user-acknowledged actions.
- CUDA is available on some hosts and can accelerate many workflows, but it is not required for the default package/import smoke checks in this skill.
- If a workflow needs audio-format repair, resampling, statistics, or VAD, route to the vocoder/audio sub-skill instead of duplicating that logic here.
- If a workflow needs speaker/language selection, custom checkpoint inference, or registry lookup, route to the inference/model-zoo sub-skill instead of rebuilding those rules here.
- If the repository snapshot changed, compare against [references/repo-provenance.md](references/repo-provenance.md) before relying on this skill.
