# Building and PyInstaller packaging

This reference distills the repository packaging knowledge needed for safe planning. It is intentionally self-contained: use the bundled `scripts/build_preflight.py` to inspect a candidate source tree, and do not run the source `build.py` unless a future user explicitly approves the side effects.

## What the source build workflow does

The maintained packaging script is a PyInstaller release helper, not a safe diagnostic. Its top-level flow:

1. Optionally accepts one command-line argument: an Apple signing identity such as a Developer ID Application string. On macOS without an argument it prompts before continuing unsigned.
2. Runs a setup step equivalent to `pip install -r requirements.txt`.
3. Prompts interactively with a reminder to increment `app/version.py` and prints the current `Version(...)` value.
4. Builds with PyInstaller using the options below.
5. On macOS with a signing identity, runs `codesign`, creates an archive, submits it with `xcrun notarytool`, prompts the operator to inspect notarization history/logs, staples the app, then archives again.
6. Creates platform-specific zip archives under `dist/`.

Because this can install dependencies, invoke PyInstaller, create or overwrite `dist/`/`build` outputs, block on prompts, and use private Apple signing credentials, treat the original build script as manual and approval-required.

## Exact common PyInstaller options

The build script constructs a PyInstaller option list with these common options:

```text
--clean
--noconfirm
--name=Open Interface
--icon=app/resources/icon.png
--windowed
--paths=./env/lib/python3.12/site-packages
--hidden-import=pyautogui
--hidden-import=appdirs
--hidden-import=pyparsing
--hidden-import=ttkbootstrap
--hidden-import=openai
--hidden-import=google_genai
--hidden-import=google
--hidden-import=google.genai
--add-data=app/resources/*:resources
--add-data=app/*.py:.
--add-data=app/utils/*.py:utils
--add-data=app/models/*.py:models
app/app.py
```

Important details:

- The executable/application name is `Open Interface`. Shell commands in the release helper escape the space as `Open\ Interface` when addressing `dist/Open Interface...` paths.
- `--windowed` suppresses a console window. During build-debug work, removing it can be useful, but that is a manual build modification.
- The relative `--paths=./env/lib/python3.12/site-packages` assumes a repository-local virtual environment named `env` with Python 3.12 packages. If another environment layout is used, that option must be adapted for the actual build environment rather than copied blindly.
- The hidden imports are required because PyInstaller did not discover all dynamic/runtime imports from static analysis. The google-genai entries are present because the `google-genai` package was noted as not working cleanly with PyInstaller without explicit inclusion.
- `speech_recognition` is mentioned only as a commented historical/debug note; it is not enabled in the current option list.

## Platform-specific branches

The build helper adds or performs different steps by platform:

### Linux

Additional PyInstaller options:

```text
--hidden-import=PIL._tkinter_finder
--onefile
```

Build-script comments name system packages that might be needed before a full Linux build:

```text
sudo apt install portaudio19-dev
sudo apt-get install python3-tk python3-dev
```

The Linux archive name is `Open-Interface-v<version>-Linux.zip`, containing the built `Open Interface` executable. The README evidence says the Linux binary had been tested on Ubuntu 20.04.

### Windows

Additional PyInstaller option:

```text
--onefile
```

The Windows archive name is `Open-Interface-v<version>-Windows.zip`, created with PowerShell `Compress-Archive` over `Open Interface.exe`. The README evidence says the Windows binary had been tested on Windows 10.

A PyInstaller `--add-data` separator can be platform-sensitive in manual commands; the source helper uses the colon form shown above. If a manual Windows build reports add-data parsing errors, review PyInstaller's platform-specific separator expectations before changing source logic.

### macOS

The common PyInstaller options are used by default. If a signing key is provided, the build adds:

```text
--codesign-identity=<signing key>
```

After PyInstaller, a signed macOS release flow includes these public phases:

```text
codesign --deep --force --verbose --sign "<signing key>" dist/Open\ Interface.app --options runtime
xcrun notarytool submit --wait --keychain-profile "<profile>" --verbose dist/<zip-name>
xcrun stapler staple dist/Open\ Interface.app
ditto -c -k --sequesterRsrc --keepParent Open\ Interface.app <zip-name>
```

The keychain profile is derived in the helper from the signing identity prefix before `(`, but real signing identities, keychain profiles, Apple IDs, passwords, and API keys are private operator state. Never place them in a skill file, review note, shell history snippet, or release checklist.

The macOS archive name is `Open-Interface-v<version>-MacOS-M-Series.zip` when `platform.processor()` reports `arm`; otherwise it is `Open-Interface-v<version>-MacOS-Intel.zip`. The README also documents moving the app to Applications and granting Accessibility plus Screen Recording permissions after install; those are runtime/desktop concerns, not packaging preflight checks.

Build-script comments name macOS package prerequisites:

```text
brew install portaudio
```

They also warn that Python installed through pyenv may need separate Tkinter/Tcl-Tk setup.

## Included resources and source modules

The bundle is expected to include:

- `app/resources/*` at bundle destination `resources`.
- top-level `app/*.py` modules at bundle destination `.`.
- `app/utils/*.py` at bundle destination `utils`.
- `app/models/*.py` at bundle destination `models`.
- entry point `app/app.py`.

The resource set must include at least:

- `app/resources/icon.png`, used by `--icon`.
- `app/resources/context.txt`, read by the LLM component at runtime.

The app entry point calls `multiprocessing.freeze_support()` under its `__main__` guard, matching the PyInstaller multiprocessing pitfall noted in the source build comments.

## Version evidence

The build script imports `version` from `app/version.py`, prompts the operator to confirm a version bump, and uses that value in zip file names. At production time the source version evidence was `Version('0.9.0')`; treat that as a snapshot, not eternal truth. For any future release, inspect the current `app/version.py` value with the bundled preflight helper and confirm the intended tag, release title, and archive names match.

## Safe build-planning sequence

1. Run the bundled preflight helper in read-only mode:

   ```text
   python scripts/build_preflight.py --repo-root <repo-root> --json
   ```

2. If syntax confidence is needed, add `--compile`; this uses a temporary pycache prefix and does not create `dist/` or `build/` artifacts.
3. Resolve reported missing files, missing option tokens, resource globs with no matches, and version/release mismatches before considering a full build.
4. For manual builds, decide platform, Python 3.12 environment layout, whether `--paths` needs adaptation, and whether signing/notarization is in scope.
5. Obtain explicit approval before installing dependencies, running PyInstaller, deleting stale artifacts, or invoking signing/notarization tools.

## CI/static context

The repository's CI evidence is lint-only on Python 3.12. It installs `pylint`, runs `pylint $(git ls-files '*.py') --output=lint.txt || true`, prints the lint report, and uploads it as an artifact. Because the lint command is allowed to fail without failing the workflow, CI is useful context but is not proof that PyInstaller builds or packaged GUI runtime work.
