# SpeechRecognition CLI and model setup reference

This reference covers the public entry points owned by setup work. It is
distilled from the package metadata, CLI implementation, module entry point,
README install notes, CI setup commands, and installed CLI help checks for
SpeechRecognition 3.17.0.

## Entry points

| Entry point | What it does | Use it when | Avoid it when |
| --- | --- | --- | --- |
| `sprc` | Console script registered by the `SpeechRecognition` distribution and implemented by `speech_recognition.cli:main`. | You need setup commands such as `sprc download vosk` or want to verify CLI help. | The package was imported directly from source without console-script installation; use the module CLI form as a fallback. |
| `python -m speech_recognition.cli` | Runs the same `sprc` argument parser through the module. | `sprc` is not on `PATH`, or you want to test the CLI with the current Python interpreter. | The package import itself is broken; fix install/import first. |
| `python -m speech_recognition` | Starts the package's interactive microphone demo. It constructs `Recognizer()` and `Microphone()`, calibrates ambient noise, listens repeatedly, and calls the default Google recognizer. | A human explicitly wants to try a microphone demo in an environment with PyAudio, a default input device, and network access. | Automated validation, CI, headless sessions, no-microphone machines, or pure model setup tasks. |

## Help commands that are safe to run

These commands inspect parser wiring only; they do not download a model:

```bash
sprc --help
sprc download --help
sprc download vosk --help
python -m speech_recognition.cli --help
python -m speech_recognition.cli download vosk --help
```

Expected top-level help has the shape `usage: sprc [-h] {download} ...`. The
`download` subcommand currently has one target, `vosk`. The Vosk target accepts
`--url URL`; if omitted, the CLI uses the built-in default Vosk small English
model URL.

If these help commands fail with a missing `tqdm` import, see
[troubleshooting](troubleshooting.md#sprc-help-fails-with-modulenotfounderror-no-module-named-tqdm).

## Vosk setup command

For Vosk recognition, the Python package dependency and the model directory are
both required:

```bash
python -m pip install "SpeechRecognition[vosk]"
python -m pip install tqdm
sprc download vosk
```

The separate `tqdm` install is listed because the 3.17.0 CLI imports `tqdm`
unconditionally, while the package metadata does not declare it as a base or
Vosk extra dependency.

A custom model zip can be selected:

```bash
sprc download vosk --url URL_TO_VOSK_ZIP
```

Only use a custom URL when the archive layout matches the CLI's expectation:
the zip basename without `.zip` must match the extracted top-level directory
name. Otherwise the downloader may finish the network step but fail while
copying the extracted model.

## Vosk side effects and model location

`sprc download vosk` is not a dry run. It:

1. downloads a model zip from the network into a temporary directory;
2. displays progress with `tqdm`;
3. unzips into the temporary directory;
4. removes any existing installed package model directory for Vosk; and
5. copies the extracted model to `speech_recognition/models/vosk` inside the
   installed package directory for the environment running the command.

For SpeechRecognition 3.17.0, the Vosk recognizer checks the installed package
model directory described above. Treat older wording that points to a generic
project `model` directory as insufficient for the integrated recognizer unless
you deliberately copy or symlink the model into the installed package's
`models/vosk` location.

Operational consequences:

- The model is per Python environment. Installing a new environment usually
  means downloading or copying the model again for that environment.
- The command needs permission to write inside the installed package directory.
  If that is not writable, use a user-writable virtual environment or install
  location.
- Existing Vosk model files at the package target are replaced, not merged.
- No authentication is needed for the default Vosk download, but network access is
  required unless the model is copied manually.

## Other model and cache side effects

The `sprc` CLI only prepares the bundled Vosk model location. Other engines have
separate setup behavior:

- Local Whisper and Faster-Whisper models are loaded by their upstream Python
  packages when `recognize_whisper` or `recognize_faster_whisper` is called.
  First use can download/cache model weights. Use the recognition-engine
  method options for custom download/cache roots.
- OpenAI, Groq, Cohere, Google Cloud, AssemblyAI, and legacy cloud methods do
  not use `sprc` model setup. They require their SDK extras plus authentication or
  service authentication parameters at call time.
- PocketSphinx uses the package's bundled English language data for the default
  language; custom language packs are a recognizer configuration concern, not a
  `sprc` command.

Route engine-specific method parameters to
[recognition-engines](../../recognition-engines/SKILL.md) after installation and
model setup are complete.

## Environment check workflow

Run the bundled checker before and after installing extras:

```bash
python scripts/check_speech_recognition_env.py
python scripts/check_speech_recognition_env.py --json
python scripts/check_speech_recognition_env.py --require-cli
```

The checker imports the package, reports distribution metadata, lists recognizer
methods wired onto `Recognizer`, probes `sprc` and module CLI help, checks
whether the package Vosk model directory exists, and groups optional module
availability by extra. It never calls `sprc download vosk`, never runs the
interactive microphone demo, and never verifies service authentication.
