---
name: python-and-cli
description: "Enables Porcupine Python SDK usage, low-level engine control, file
  and microphone demo patterns, device enumeration, and safe local checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# python-and-cli

Use this sub-skill when you need to:

- install `pvporcupine` and confirm the import
- create a Porcupine engine in Python
- inspect `version`, `frame_length`, or `sample_rate`
- process a `.wav` file for wake-word detections
- enumerate inference devices safely
- read `PorcupineError` and `message_stack` failures
- adapt the packaged Python file demo into a reusable checker

## Included workflow

- Python SDK install and import.
- Low-level engine creation, processing, and cleanup.
- Built-in keyword selection and custom keyword paths.
- Sensitivity handling and frame/sample-rate validation.
- File-based detection.
- Device enumeration and safe preflight checks.
- Reference-only microphone recipe.

## Excluded workflow

- Custom wake-word training and asset selection.
- Language/platform matching for `.ppn` and `.pv` files.
- Node, web, React Native, Android, iOS, Flutter, Java, .NET, or C SDK details.

If the task is about training or model/keyword asset selection, route it to `../custom-keywords-and-assets/SKILL.md`.

## Read first

- `references/python-api-reference.md` for verified signatures, object behavior, device strings, and exception classes.
- `references/python-workflows.md` for the file recipe, optional demo CLI notes, and the hardware-required microphone flow.
- `references/troubleshooting.md` for import, AccessKey, model, keyword, WAV, frame, device, and cleanup failures.

## Run the bundled helper

- `scripts/porcupine_file_check.py --help` shows the safe parser without requiring an AccessKey.
- `scripts/porcupine_file_check.py --list-devices` prints the inference devices advertised by the native library.
- `scripts/porcupine_file_check.py --access-key "$ACCESS_KEY" --input-wav sample.wav --keyword picovoice` scans a file with a built-in keyword.
- `scripts/porcupine_file_check.py --access-key "$ACCESS_KEY" --input-wav sample.wav --keyword-path /path/to/custom.ppn --model-path /path/to/porcupine_params.pv` scans a file with custom assets.

## Practical boundaries

- `pvporcupine.create` still needs a valid AccessKey at initialization.
- `Porcupine.process` only accepts 16-bit, single-channel PCM frames sized exactly to `frame_length`.
- `available_devices()` is the safe no-AccessKey check for loading the native library and discovering inference targets.
- If you need to choose `.ppn` / `.pv` assets or train a wake word, move to the sibling asset skill before coming back here.
- If a task only needs the packaged demo CLI, the bundled helper and workflow notes are usually enough; you do not need the original repository checkout.

## Quick routing guide

- Ask for `scripts/porcupine_file_check.py` when the user wants a file-based wake-word check, a parser/help smoke test, or a path-safe example for the Python binding.
- Ask for `references/python-workflows.md` when the user wants the microphone recipe, `available_devices()` usage, or a command-line comparison point.
- Ask for `references/troubleshooting.md` when the user reports an import failure, a bad AccessKey, a model or keyword path problem, a sensitivity mismatch, a WAV format issue, or an invalid device selector.
- Ask for `references/python-api-reference.md` when the user needs exact signatures, `Porcupine` attributes, or the `message_stack` behavior of `PorcupineError` subclasses.
- Prefer the helper script over ad hoc code when the task is only to confirm that Porcupine can load a file and emit detections.
- Keep cleanup explicit: if you create the engine yourself, delete it in `finally`.
