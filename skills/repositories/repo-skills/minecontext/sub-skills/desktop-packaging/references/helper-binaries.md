# macOS helper binaries

MineContext's Electron app can bundle two small Python helper executables for
macOS window inspection and capture:

- `window_inspector`: lists and filters visible application windows, returning
  JSON window metadata.
- `window_capture`: captures a selected window and prints a base64 PNG payload.

Both helpers depend on macOS Quartz/PyObjC APIs. They are package-time helper
binaries, not the main backend service.

## Expected source layout and outputs

Expected helper project layout in a checkout:

```text
frontend/externals/python/window_inspector/
  README.md
  requirements.txt
  window_inspector.py
  window_inspector.spec

frontend/externals/python/window_capture/
  README.md
  requirements.txt
  window_capture.py
  window_capture.spec
```

Expected PyInstaller outputs before macOS Electron packaging:

```text
frontend/externals/python/window_inspector/dist/window_inspector/window_inspector
frontend/externals/python/window_capture/dist/window_capture/window_capture
```

`frontend/electron-builder.yml` copies those outputs into the packaged macOS app
as:

```text
bin/window_inspector
bin/window_capture
```

## Build paths

The primary helper build path during `pnpm run build` is:

```bash
cd frontend
node build-python.js
```

`pnpm run build` runs `node build-python.js` before typechecking and before
`electron-vite build`. The JavaScript builder:

1. Uses `frontend/externals/python` as the helper root.
2. Checks whether each helper executable already exists and skips it if so.
3. On macOS only, creates a per-helper `venv/`, installs that helper's
   `requirements.txt`, installs PyInstaller, and runs the matching `.spec`.
4. Verifies the helper executable under the helper `dist/` directory.
5. On any non-macOS platform, exits successfully after logging that the
   macOS-specific helpers are skipped.

There is also a shell helper builder:

```bash
cd frontend
bash build-python.sh
```

The shell version always tries to build both helpers and is therefore only safe
on macOS with working PyObjC dependencies. Prefer `node build-python.js` for
cross-platform packaging because it intentionally skips helpers off macOS.

## Dependency and spec details

Both helper requirement files declare PyObjC packages for Quartz/Cocoa and
related macOS frameworks. The inspector spec explicitly includes hidden imports
for Quartz, Quartz CoreGraphics, AppKit, Foundation, CoreFoundation, and
CoreServices. The capture spec is simpler and relies on the imports in
`window_capture.py`.

If a PyInstaller helper build fails on macOS with a missing framework import,
check the helper venv and requirements installation first. If it fails on Linux
or Windows with missing Quartz, the wrong helper build path was used.

## Why helpers are skipped on Linux

Synthetic case: the current host is Linux and a user asks why `window_capture`
was skipped during `pnpm run build`.

Correct diagnosis:

- `window_capture` and `window_inspector` are macOS-only because they import
  Quartz APIs.
- The JavaScript builder checks `process.platform !== 'darwin'` and exits
  successfully without building them.
- The log text mentions Windows even on other non-darwin platforms, but the
  skip applies to Linux too.
- Do not try to install PyObjC on Linux to fix this. Continue the Linux package
  flow, and only require helper binaries for macOS targets.

## Helper troubleshooting checklist

| Symptom | Likely cause | Response |
| --- | --- | --- |
| `ModuleNotFoundError: Quartz` on Linux or Windows | Helper build attempted on a non-macOS host | Use `node build-python.js` and accept the skip; helpers are macOS-only. |
| `ModuleNotFoundError: Quartz` on macOS | Helper venv missing PyObjC dependencies | Reinstall from the helper `requirements.txt` in that helper venv, then rerun the matching spec. |
| `electron-builder` cannot find `bin/window_capture` source | Helper `dist/window_capture/window_capture` was never built or was cleaned | Run `node build-python.js` on macOS and verify the expected helper output paths. |
| Helper script runs but returns `[]` or an error payload | Runtime window permission, no visible suitable windows, or Quartz access limitation | This is runtime behavior; route permission/API details to runtime-service unless the packaged binary itself is missing. |
| `build-python.sh` fails on Linux | Shell builder does not contain the non-macOS skip | Use the JavaScript builder or avoid helper builds on non-macOS. |
