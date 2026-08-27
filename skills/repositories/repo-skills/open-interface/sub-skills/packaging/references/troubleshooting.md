# Packaging troubleshooting

Start with safe diagnostics. Run `python scripts/build_preflight.py --repo-root <repo-root> --json` before any manual PyInstaller build, dependency installation, signing, notarization, or artifact cleanup.

## Common symptoms

| Symptom | Likely cause | Automated-safe diagnostic | Resolution / route |
|---|---|---|---|
| `ModuleNotFoundError` in a PyInstaller build or packaged app for `pyautogui`, `appdirs`, `pyparsing`, `ttkbootstrap`, `openai`, `google_genai`, `google`, or `google.genai` | Hidden import missing or package absent from build environment | Preflight reports whether each expected hidden-import token is present in the build script; inspect dependency pins without importing packages | Restore the hidden import, install the matching dependency in the approved build environment, or update the packaging strategy intentionally. Do not remove hidden imports just because source imports look static. |
| Linux packaged app fails around Tk/PIL discovery | Linux-specific `PIL._tkinter_finder` hidden import or Tk system libraries missing | Preflight checks the Linux branch for `--hidden-import=PIL._tkinter_finder` and `--onefile` | Confirm `python3-tk` and `python3-dev` are installed on the build host; keep the Linux hidden import unless a newer tested PyInstaller hook makes it unnecessary. |
| `pip install -r requirements.txt` fails while building PyAudio | Missing PortAudio headers/libraries | Requirements include `PyAudio`; build comments name platform packages | On Linux install `portaudio19-dev`; on macOS install `portaudio` with Homebrew. This is a manual system-package action requiring approval. |
| `_tkinter` import errors, Tcl/Tk initialization errors, or Tk window failures | Tkinter is missing from Python or OS packages | Preflight can only report platform notes; it does not launch GUI or import Tk | Linux: install `python3-tk` and `python3-dev`. macOS with pyenv may need a Python built against Tcl/Tk. Runtime GUI troubleshooting belongs in `../desktop-runtime/`. |
| Packaged app cannot find `context.txt`, icon, or other bundled resources | Add-data entry missing, source resource missing, or runtime path calculation incompatible with bundle layout | Preflight checks `app/resources/icon.png`, `app/resources/context.txt`, `app/resources/*`, and `--add-data=app/resources/*:resources` | Restore the resource file or add-data entry. If the resource exists but fails only in the bundle, review how file reads resolve next to bundled modules and consider a PyInstaller-aware resource helper. |
| App starts but model calls fail due to API keys | Runtime configuration issue, not a packaging build failure | Packaging preflight does not read or validate credentials | Route to `../desktop-runtime/`. Do not put API keys in build scripts, release notes, preflight JSON, or packaged artifacts. |
| App starts but screenshots/keyboard/mouse automation fail | Missing display server or OS permissions | Packaging preflight cannot grant Accessibility, Screen Recording, or desktop automation permissions | Route to `../desktop-runtime/`. macOS requires Accessibility and Screen Recording permissions; Linux may require a real display/session; headless CI is not enough. |
| App loops or crashes after an LLM response | Malformed JSON, unsupported pyautogui function name, or runtime interpreter issue | Packaging checks cannot validate live model responses | Route to `../desktop-runtime/` for JSON schema/action contract diagnostics. Packaging only owns whether bundled `context.txt` and relevant modules were included. |
| Multiprocessing-related errors in a frozen executable | Missing or misplaced `multiprocessing.freeze_support()` | Preflight checks for `freeze_support` in the app entry point | Keep the `freeze_support()` call under the entry-point guard. If packaging entry points change, re-check the frozen multiprocessing guidance before building. |
| Google Gemini backend missing in packaged app | PyInstaller did not collect google-genai namespace/package modules | Preflight checks for `--hidden-import=google_genai`, `--hidden-import=google`, and `--hidden-import=google.genai` | Keep explicit google hidden imports and confirm `google-genai` is installed in the build environment. Namespace packages are a known PyInstaller failure surface. |
| Full build fails with hundreds of PyInstaller messages | The critical error is often earlier than final cleanup logs | Use preflight to rule out missing files/options first | Scroll upward from the bottom to find the first real import/path error before PyInstaller cleanup. Capture that message, then map it to hidden imports/resources/platform packages. |
| Stale or confusing `dist/`, `build/`, or `.spec` output | Previous build artifacts remain; repository ignores these paths | `.gitignore` evidence lists `dist/`, `build/`, and `*.spec`; preflight does not delete them | Ask before deleting or overwriting artifacts. `--clean` is in the build options, but manual cleanup is still a mutating action. |
| macOS `codesign` says identity not found or cannot sign nested files | Signing identity/keychain not available, wrong identity string, hardened runtime issue, or unsigned collected binary | Preflight only reports that signing/notarization phases exist; it never invokes codesign | Verify Developer ID Application certificate and keychain access on the release machine. Do not expose private identity/profile details in logs beyond what the user authorizes. |
| `xcrun notarytool submit` fails or `stapler` cannot staple | Notary profile missing, rejected notarization, network/account issue, or stapling before acceptance | Manual operator checks notary history/logs; preflight never submits | Inspect notary history/logs on the release machine, fix rejected binaries/metadata, re-submit, then staple only after acceptance. Keep credential-bearing logs private. |
| macOS archive invalidates signature | Zip tool did not preserve bundle metadata | Build reference names the expected `ditto -c -k --sequesterRsrc --keepParent` flow | Use the macOS `ditto` archive method for signed `.app` bundles rather than generic zip tools. |
| Windows command-line add-data or archive command fails around spaces/separators | Shell quoting, path with spaces, or PyInstaller add-data separator mismatch | Preflight reports the source helper's expected tokens but does not emulate Windows shells | Quote `Open Interface.exe` carefully and consult PyInstaller's Windows add-data syntax if manually invoking commands outside the source helper. |
| `--paths=./env/lib/python3.12/site-packages` does not point to packages | Build environment is not a relative `env` Python 3.12 environment | Preflight reports whether the assumed relative path exists | Adapt the PyInstaller path option for the approved build environment or recreate the documented environment layout. Do not leak private environment paths into skill/runtime files. |
| CLI misuse: source build blocks on prompts or installs unexpected packages | The source helper is interactive and calls setup before build | Use preflight instead for non-mutating checks | For any full build, obtain approval for prompts, dependency install, artifact writes, and platform-specific signing steps. |

## Triage order

1. Run the preflight helper without `--compile`; resolve hard missing-file or missing-token failures.
2. Re-run with `--compile` if Python syntax changed. Compilation is safe but does not prove imports, GUI behavior, or PyInstaller success.
3. Confirm platform package prerequisites: PortAudio for PyAudio; Tk/Tcl for GUI/Tkinter; Python 3.12-compatible dependencies.
4. If a manual PyInstaller build fails, identify the first actionable import/path error before cleanup logs.
5. For runtime-only failures in the packaged app, split packaging inclusion problems from desktop/API issues:
   - Missing module/resource only in the bundle → packaging owns it.
   - API key, display permission, screenshot, LLM JSON, or pyautogui action behavior → route to `../desktop-runtime/`.
6. For macOS release failures, separate public checklist facts from credential-bearing commands and logs.

## Optional/development dependency notes

- `moviepy` appears in requirements but the demo media conversion helper is intentionally excluded from this sub-skill because it is hard-coded and destructive. Do not install or run media conversion as part of packaging preflight.
- macOS-only pyobjc packages are platform-marked in requirements and should not be forced onto non-macOS hosts.
- PyInstaller and pyinstaller-hooks-contrib are release/build dependencies; safe preflight intentionally does not import them.

## When to stop and ask

Ask the user before:

- Installing or upgrading dependencies or system packages.
- Running the source build helper or any PyInstaller command.
- Removing `dist/`, `build/`, `.spec`, zip, app, or executable artifacts.
- Using any signing identity, keychain profile, or notarization credential.
- Launching the packaged GUI or granting desktop automation permissions.
- Sending test requests to OpenAI, Gemini, or a custom model endpoint.
