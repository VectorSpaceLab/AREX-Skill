# SpeechRecognition Cross-Cutting Troubleshooting

Use this reference when a problem cuts across package install, import, FLAC conversion, optional dependencies, credentials, or CLI setup. For workflow-specific failures, route to the nearest sub-skill troubleshooting file.

## Import or package metadata failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: aifc` or `audioop` on Python 3.13+ | The package was imported without metadata-resolved compatibility dependencies. | Install with `python -m pip install SpeechRecognition` or `python -m pip install -e .` for an editable checkout so `standard-aifc` and `audioop-lts` resolve. |
| `import speech_recognition` works from a checkout but distribution metadata is missing | The current directory is shadowing an uninstalled package. | Install the distribution into the intended environment and re-run import from a neutral directory. |
| A recognizer method is missing from `Recognizer()` | Module attachment failed during import, often due a broken dependency import path. | Run `python scripts/check_install.py --json` from this skill root and inspect method wiring plus optional imports. |

## FLAC converter issues

SpeechRecognition uses FLAC conversion when loading native FLAC and when creating FLAC payloads for recognizer APIs. Lookup prefers a system `flac` command, then package-bundled platform binaries for supported x86 Windows/Linux/macOS.

Fixes:

```bash
flac --version
python - <<'PY'
from speech_recognition.audio import get_flac_converter
print(get_flac_converter())
PY
```

If no converter is available on the user's platform, install a system FLAC encoder. On macOS, prefer `brew install flac`. On unusual CPU/OS combinations, bundled binaries may not apply.

## Optional dependency and backend confusion

A base install supports audio file handling and default method wiring, but many workflows need extras:

- Microphone: `SpeechRecognition[audio]` plus host PortAudio and real input hardware.
- Offline PocketSphinx: `SpeechRecognition[pocketsphinx]`.
- Offline Vosk: `SpeechRecognition[vosk]` plus a model directory.
- Cloud/API engines: the matching SDK extra plus credentials/network access.
- Local Whisper/Faster-Whisper: the matching local extra and model/cache resources.
- Silence-aware split: `SpeechRecognition[audio-split]`.

Do not install every extra as a default repair. Use `cli-model-setup` to select and probe the one that matches the user task.

## Credential and network safety

- Never paste API keys into shared scripts, generated skill files, or logs.
- Prefer environment variables or an approved secret manager.
- Treat `UnknownValueError` as no usable transcript, not necessarily a credential problem.
- Treat `RequestError` and SDK exceptions as network, credential, service, or optional dependency problems.
- Cloud/API mock tests prove wrapper behavior but do not prove live credentials, billing, or transcription quality.

## CLI issues

If `sprc --help` fails with `ModuleNotFoundError: No module named 'tqdm'`, install `tqdm` in the same environment. This is a known setup pitfall for SpeechRecognition 3.17.0 because the CLI imports `tqdm` but package metadata does not install it by default.

Do not run these commands automatically without user approval:

- `sprc download vosk`: downloads, unzips, and overwrites model files in the installed package directory.
- `python -m speech_recognition`: starts an interactive microphone demo and may call a network recognizer.

## Where to go next

- File decoding, conversion, splitting, FLAC payloads: [audio-data troubleshooting](../sub-skills/audio-data/references/troubleshooting.md).
- Microphone and live capture: [capture-listening troubleshooting](../sub-skills/capture-listening/references/troubleshooting.md).
- Recognizer method and engine failures: [recognition-engines troubleshooting](../sub-skills/recognition-engines/references/troubleshooting.md).
- CLI, extras, and Vosk model setup: [cli-model-setup troubleshooting](../sub-skills/cli-model-setup/references/troubleshooting.md).
- Repository editing and CI failures: [repo-development troubleshooting](../sub-skills/repo-development/references/troubleshooting.md).
