# CLI, model, and optional-dependency troubleshooting

Start with the bundled environment checker:

```bash
python scripts/check_speech_recognition_env.py
python scripts/check_speech_recognition_env.py --require-cli
```

The checker is non-invasive: it does not download models, run the interactive
microphone demo, or verify authentication.

## `sprc --help` fails with `ModuleNotFoundError: No module named 'tqdm'`

**Likely cause.** SpeechRecognition 3.17.0's CLI imports `tqdm` unconditionally,
but `tqdm` is not listed in the package's base dependencies or official extras.
This was observed during installed CLI verification: base install succeeded,
then CLI help failed until `tqdm` was installed.

**Fix.** Install `tqdm` in the same Python environment as SpeechRecognition:

```bash
python -m pip install tqdm
sprc --help
python -m speech_recognition.cli --help
```

If package APIs work but CLI help fails, this `tqdm` issue is the first thing to
check.

## `sprc: command not found`

**Likely cause.** The console script was not installed into the active command
path, or the user is running a different Python environment than the one where
SpeechRecognition was installed.

**Fix.** Use the module CLI with the intended interpreter:

```bash
python -m speech_recognition.cli --help
```

If the module CLI works, reinstall or expose the console entry point for that
environment. If both forms fail, diagnose package import first.

## Import fails for `aifc` or `audioop` on Python 3.13+

**Likely cause.** The package is being imported without its metadata-resolved
compatibility requirements. SpeechRecognition metadata adds `standard-aifc` and
`audioop-lts` for Python 3.13 and newer.

**Fix.** Install through package metadata rather than importing a raw source
folder:

```bash
python -m pip install --upgrade SpeechRecognition
python - <<'PY'
import speech_recognition
print("import ok")
PY
```

If a checkout is being edited, install it with `python -m pip install -e .` from
that checkout so the compatibility requirements resolve.

## `sprc download vosk` cannot reach the network

**Likely cause.** The Vosk downloader fetches a model zip from a public URL and
has no offline cache mode.

**Fix options.**

- Run the download in an environment with network access after the user approves
  the side effects.
- Download the model out of band, then copy or symlink the unpacked model into
  the installed package's `speech_recognition/models/vosk` directory.
- Postpone Vosk recognition and use another engine route until a model is
  available.

Do not treat a missing network download as a base package failure; it blocks
only Vosk model-backed recognition.

## Vosk recognizer reports that the model was not found

**Likely cause.** The `vosk` Python package may be installed, but the model
directory expected by SpeechRecognition is absent. In 3.17.0, the integrated
Vosk recognizer checks `speech_recognition/models/vosk` inside the installed
package directory for the active environment.

**Fix.** In that same environment:

```bash
python -m pip install "SpeechRecognition[vosk]" tqdm
sprc download vosk
python scripts/check_speech_recognition_env.py --require-cli
```

If the environment is read-only, create or use a user-writable environment and
install SpeechRecognition there before running the downloader. Remember that
`sprc download vosk` replaces an existing package Vosk model directory.

## Custom Vosk URL downloads but setup still fails

**Likely cause.** The CLI derives the extracted directory name from the zip
filename. If `my-model.zip` extracts to a top-level directory with a different
name, the copy step cannot find the expected extracted path.

**Fix.** Use an official Vosk zip whose top-level directory matches the zip
basename, or unpack manually and place the final model directory at
`speech_recognition/models/vosk` inside the installed package.

## Optional extra import errors

**Symptom examples.** Missing `pyaudio`, `pocketsphinx`, `google.cloud.speech`,
`vosk`, `whisper`, `faster_whisper`, `openai`, `groq`, `cohere`, `requests`,
`librosa`, or `numpy`.

**Fix.** Install only the extra that matches the workflow:

```bash
python -m pip install "SpeechRecognition[audio]"          # pyaudio / microphone
python -m pip install "SpeechRecognition[pocketsphinx]"   # PocketSphinx
python -m pip install "SpeechRecognition[vosk]"           # Vosk Python package
python -m pip install "SpeechRecognition[whisper-local]"  # local Whisper
python -m pip install "SpeechRecognition[faster-whisper]" # Faster-Whisper
python -m pip install "SpeechRecognition[openai]"         # OpenAI-compatible API
python -m pip install "SpeechRecognition[groq]"           # Groq API
python -m pip install "SpeechRecognition[cohere-api]"     # Cohere API
python -m pip install "SpeechRecognition[assemblyai]"     # AssemblyAI method
python -m pip install "SpeechRecognition[audio-split]"    # silence-aware split
```

After installation, rerun:

```bash
python scripts/check_speech_recognition_env.py --json
```

Import availability proves only that Python modules are present. It does not
prove microphones, model weights, network access, service authentication, billing,
or transcription quality.

## Extra is installed but cloud/API recognition still fails

**Likely cause.** SDK import is only the first gate. Cloud/API methods also need
network access, authentication, account permissions, and sometimes explicit API
arguments.

**Fix.** Route to [recognition-engines](../../recognition-engines/SKILL.md) for the
specific recognizer's parameters, authentication expectations, response shapes, and
`RequestError`/`UnknownValueError` handling. Never paste authentication into skill
files or shared logs.

## `python -m speech_recognition` blocks or fails on a headless machine

**Likely cause.** This entry point is an interactive microphone demo. It creates
`Microphone()`, performs ambient-noise calibration, listens in a loop, and then
uses the default Google recognizer. Missing PyAudio, no default input device,
OS audio noise, or lack of network access can all stop it.

**Fix.** Do not use this command for automated validation. For microphone setup,
install `SpeechRecognition[audio]` and route to
[capture-listening](../../capture-listening/SKILL.md). For recognition engine
selection, route to [recognition-engines](../../recognition-engines/SKILL.md).

## Local Whisper on Python 3.14

**Likely cause.** The project metadata notes that `openai-whisper` does not
support Python 3.14 yet, and the repository's Python 3.14 all-extras CI install
omits local Whisper/Faster-Whisper and audio-split groups.

**Fix.** Use Python 3.10-3.13 for `SpeechRecognition[whisper-local]` work unless
you have independently verified the upstream stack. For Python 3.14, prefer
cloud/API recognizers or Vosk/PocketSphinx if they satisfy the user's task.

## PyAudio build or device failures

**Likely cause.** `SpeechRecognition[audio]` installs the Python wrapper, but the
host may still need PortAudio development headers/runtime and an actual input
device.

**Fix.** Install host PortAudio support appropriate for the user's OS, then use
[capture-listening](../../capture-listening/SKILL.md) to list devices, select an
explicit device index, and calibrate ambient noise.

## FLAC converter errors on unusual platforms

**Likely cause.** SpeechRecognition bundles FLAC binaries for common x86 Windows,
Linux, and Intel macOS cases. Other platforms may need a system `flac` command
available on `PATH`.

**Fix.** Install a system FLAC encoder, then route audio conversion and upload
payload issues to [audio-data](../../audio-data/SKILL.md).
