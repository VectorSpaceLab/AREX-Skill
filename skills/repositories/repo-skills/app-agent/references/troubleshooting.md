# AppAgent troubleshooting

## Installation and import
- **Symptom:** `ModuleNotFoundError` for `dashscope`, `cv2`, `yaml`, `requests`, or `pyshine`.
  - **Cause:** dependencies from `requirements.txt` are missing in the active environment.
  - **Fix:** reinstall with `python -m pip install -r requirements.txt` in the private inspection environment.
- **Symptom:** `pyshine` prints warnings for `sounddevice`, `matplotlib`, or `keras`.
  - **Cause:** optional extras are absent.
  - **Fix:** usually ignore these warnings; the repo still imported successfully in inspection.

## Config and backend selection
- **Symptom:** `Unsupported model type`.
  - **Cause:** `MODEL` in `config.yaml` is neither `OpenAI` nor `Qwen`.
  - **Fix:** set `MODEL` to one of those values and fill the matching key set.
- **Symptom:** OpenAI/Qwen requests fail immediately.
  - **Cause:** missing or invalid API key, wrong endpoint, or rate limits.
  - **Fix:** edit `config.yaml` directly and confirm the selected backend has the correct credentials.
- **Symptom:** changing shell env vars seems to have no effect.
  - **Cause:** `load_config()` applies YAML values after environment values.
  - **Fix:** edit `config.yaml`, not just the shell environment.

## Device and adb
- **Symptom:** `ERROR: No device found!`
  - **Cause:** `adb devices` returned an empty list.
  - **Fix:** connect a phone, enable USB debugging, or start an Android Studio emulator.
- **Symptom:** `ERROR: Invalid device size!`
  - **Cause:** adb could not read the device's screen resolution.
  - **Fix:** confirm the device is online and that `adb shell wm size` works.
- **Symptom:** adb command failures during screenshot/XML capture or input.
  - **Cause:** device disconnected, permissions issue, or adb not on `PATH`.
  - **Fix:** rerun `adb devices`, reconnect the target, and verify platform-tools installation.

## Workflow-specific failures
- **Symptom:** deployment says no docs were found.
  - **Cause:** neither `apps/<app>/auto_docs/` nor `apps/<app>/demo_docs/` exists.
  - **Fix:** run exploration first, or explicitly choose the no-doc path if you accept lower reliability.
- **Symptom:** a UI action response cannot be parsed.
  - **Cause:** the multimodal backend returned a format that does not match the expected `Observation/Thought/Action/Summary` or reflection schema.
  - **Fix:** tighten prompts, confirm the selected model is actually multimodal, and inspect the raw log under the session directory.
- **Symptom:** grid-based swipes misbehave.
  - **Cause:** `swipe_precise()` currently uses the start X coordinate twice when forming the adb command.
  - **Fix:** prefer the regular non-grid swipe path, or patch the helper before relying on precise grid swipes.
- **Symptom:** direct source launchers behave oddly with paths.
  - **Cause:** the repository's original launchers use `os.system(...)` and shell-string construction.
  - **Fix:** use the bundled wrappers from the generated skill, which pass arguments through `subprocess`.

## Output/layout issues
- **Symptom:** docs are not generated for a repeated element.
  - **Cause:** the exploration pipeline skips already-documented UIDs unless `DOC_REFINE=true`.
  - **Fix:** enable `DOC_REFINE` when you want to update existing docs.
- **Symptom:** generated files land in the checkout.
  - **Cause:** `root_dir` defaults to `./`.
  - **Fix:** pass a separate writable output directory outside the repository.
