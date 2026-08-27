# Release planning notes

Use this reference to plan Open Interface releases without exposing credentials or running side-effectful packaging steps. Pair it with `scripts/build_preflight.py` for current source facts.

## Release readiness checklist

Before a full build or release upload, confirm:

- Target platform(s): Linux, Windows, macOS Intel, macOS Apple Silicon, or a subset.
- Python/runtime basis: Python 3.12 is the documented build/CI baseline; the source build helper expects a relative `env` environment with Python 3.12 site-packages unless manually adapted.
- Dependency plan: `requirements.txt` includes PyInstaller 6.11.0, pyinstaller-hooks-contrib 2024.9, OpenAI 1.66.3, google-genai 1.5.0, PyAutoGUI, PyAudio, pillow, ttkbootstrap, packaging, and macOS-only pyobjc packages. Platform system packages such as portaudio and Tk may still be required.
- Version: inspect the current `app/version.py`; production evidence saw `Version('0.9.0')`, but every new release must verify the current value rather than copying that snapshot.
- Archive naming: ensure the version, Git tag/release title, and generated archive names agree.
- Resource inclusion: icon, context, top-level app modules, `utils`, and `models` are represented in the PyInstaller add-data plan.
- Hidden imports: pyautogui, appdirs, pyparsing, ttkbootstrap, openai, google_genai, google, google.genai, and Linux-only `PIL._tkinter_finder` are still represented or deliberately replaced by a new packaging strategy.
- Runtime manual test plan: packaged GUI launches only in an approved desktop session with display permissions and API credentials available; route runtime behavior to `../desktop-runtime/`.
- Private material boundary: no OpenAI/Gemini keys, Apple signing identities, keychain profiles, passwords, app-specific passwords, certificates, or notarization logs containing secrets are written into skill files or public release notes.

## Version and archive names

The source build helper builds the zip name from `Open-Interface-v` plus `str(version)`, where `version` comes from `app/version.py`.

Expected platform suffixes:

| Platform branch | Archive suffix |
|---|---|
| macOS with `platform.processor() == 'arm'` | `-MacOS-M-Series.zip` |
| macOS otherwise | `-MacOS-Intel.zip` |
| Linux | `-Linux.zip` |
| Windows | `-Windows.zip` |

The source helper prompts with a reminder to increment `app/version.py` before packaging. Treat that prompt as a manual release gate: the preflight helper can report the current version, but it cannot decide whether a version bump is semantically correct.

## Public install promises to keep consistent

The README install evidence describes:

- macOS: download latest release, unzip, move Open Interface to Applications, grant Accessibility and Screen Recording permissions if prompted or through System Settings.
- Linux: Linux binary download from latest release; evidence says Ubuntu 20.04 had been tested.
- Windows: Windows zip download from latest release; evidence says Windows 10 had been tested.
- Script mode: Python 3.12 or newer, optional virtual environment, install dependencies from `requirements.txt`, and run the app entry point.
- Setup after install: add OpenAI or Gemini API key through the app settings and restart the app; custom OpenAI-style backends can use a custom base URL/model with a restart.

Packaging release notes should not overclaim beyond those tested platform statements unless a future manual verification expands the support matrix.

## CI and static checks

The GitHub Actions workflow is named `Pylint` and runs on pushes to `main` with Python 3.12 on Ubuntu. It:

1. Checks out the repository.
2. Sets up Python 3.12.
3. Installs `pylint` only.
4. Runs `pylint $(git ls-files '*.py') --output=lint.txt || true`.
5. Prints and uploads `lint.txt`.

Implications:

- CI does not install the application requirements, does not run PyInstaller, and does not launch the GUI.
- Because `|| true` suppresses a failing exit status, uploaded lint output must be inspected before claiming lint health.
- A safe local/static release gate can include the bundled preflight helper plus syntax compilation, but packaged desktop behavior remains a separate manual workflow.

## macOS signing and notarization boundary

Public checklist items that may be documented:

- Decide whether the macOS release will be signed and notarized.
- Confirm a valid Developer ID Application certificate is available on the release machine.
- Confirm the notarytool keychain profile exists before submission.
- Confirm hardened runtime/signing options are appropriate for the app.
- After notarization, inspect notary history/logs and staple the accepted app before final archiving.
- Use `ditto -c -k --sequesterRsrc --keepParent` for macOS app archives to preserve metadata required by signing.

Private or approval-required material that must not be embedded:

- Actual signing identity strings when they identify private accounts.
- Apple ID, team ID, app-specific passwords, API keys, certificate exports, keychain profile secrets, or raw notarization logs containing account details.
- One-line commands that combine private credentials with `codesign` or `notarytool` unless the user explicitly provides them for an ephemeral manual operation.

## What a release note should say when verification is partial

If only static packaging checks were run, say so explicitly. Example wording:

```text
Packaging preflight and source compilation passed for the selected source tree. Full PyInstaller execution, macOS signing/notarization, GUI launch, desktop permissions, and live API-key behavior were not exercised in this automated check.
```

If a platform package or signing prerequisite is missing, mark the release as blocked for that platform rather than silently dropping the platform from the support claim.
