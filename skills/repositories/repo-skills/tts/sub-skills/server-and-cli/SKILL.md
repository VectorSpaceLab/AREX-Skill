---
name: server-and-cli
description: "Operate Coqui TTS installed console commands and the safe local demo server."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MPL 2.0
---

# Server And CLI

Use this sub-skill when the task is about the installed `tts` or `tts-server` console commands: checking availability, listing models, querying model metadata, building synthesis or voice-conversion commands, routing custom checkpoint paths, using pipe output, or safely starting the local demo server.

Do not use this sub-skill for Python API details, training commands, vocoder/audio preprocessing utilities, or production deployment design.

## Fast route

1. For `tts` flag syntax and command templates, read [references/cli-reference.md](references/cli-reference.md).
2. For `tts-server` help/list/run patterns and demo-server safety, read [references/server-workflows.md](references/server-workflows.md).
3. For command failures and parser/runtime diagnoses, read [references/troubleshooting.md](references/troubleshooting.md). For install/import problems, also use the root troubleshooting reference at [../../references/troubleshooting.md](../../references/troubleshooting.md).
4. Prefer bundled helpers before composing commands by hand:
   - [scripts/check_tts_cli.py](scripts/check_tts_cli.py) checks `tts` help/list/model-info paths without synthesis.
   - [scripts/build_tts_command.py](scripts/build_tts_command.py) prints shell-quoted `tts` commands from validated inputs.
   - [scripts/check_tts_server_cli.py](scripts/check_tts_server_cli.py) checks `tts-server` help/list paths without binding a server.

## Boundaries

- Model registry semantics, Python `TTS.api.TTS`, `ModelManager`, and `Synthesizer` usage belong in [../inference-and-model-zoo/SKILL.md](../inference-and-model-zoo/SKILL.md).
- FreeVC source/target audio semantics and Python voice-conversion workflows belong in [../voice-conversion/SKILL.md](../voice-conversion/SKILL.md). This sub-skill only covers the `tts --source_wav --target_wav` CLI surface.
- Training CLIs and dataset/config preparation belong in [../training-config-data/SKILL.md](../training-config-data/SKILL.md) and vocoder/audio tools belong in [../vocoder-and-audio-tools/SKILL.md](../vocoder-and-audio-tools/SKILL.md).
- Treat `tts-server` as a local demo interface. It can bind a port, run Flask debug mode, load large models, and download released checkpoints. Do not present it as a hardened persistent service.

## Safe operating policy

- `tts --help`, `tts --list_models`, `tts --model_info_by_name ...`, `tts --model_info_by_idx ...`, `tts-server --help`, and `tts-server --list_models` are the preferred low-side-effect checks.
- Commands that load released models can create cache/network/disk side effects. Validate model names, output paths, device choice, and speaker/language requirements before running them.
- Commands that start `tts-server` must be opt-in. Choose a port deliberately, check whether it is free, avoid debug mode unless actively debugging, and remember that this version binds the Flask app to the unspecified host `::`.
