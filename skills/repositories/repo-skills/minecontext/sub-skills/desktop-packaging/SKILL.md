---
name: desktop-packaging
description: "Build and troubleshoot MineContext desktop packaging, including
  the PyInstaller backend, Electron packages, frontend backend copy, and macOS
  helper binaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# desktop-packaging

Use this sub-skill when a task asks to build or troubleshoot the MineContext
standalone desktop application: the PyInstaller `opencontext` backend
executable, copying that backend into `frontend/backend/`, Electron packaging
from the `frontend/` package, macOS helper binaries, signing/notarization
preflight, or failures in the build scripts.

Route backend server startup, FastAPI routes, runtime configuration, and
`opencontext start` behavior to [runtime-service](../runtime-service/SKILL.md)
instead of diagnosing them here. This sub-skill only owns build/package
mechanics and package-time file placement.

## Natural triggers

Use this sub-skill for requests that mention:

- "build MineContext app", `pnpm build:mac`, `pnpm build:win`, `pnpm build:linux`, or Electron packaging;
- "build backend", `build.sh`, `build.bat`, `PyInstaller`, or `opencontext.spec`;
- `copy-prebuilt-backend`, missing `frontend/backend/main`, missing `dist/main/main`, or backend executable copy failures;
- `window_inspector`, `window_capture`, Quartz, macOS helper binaries, screen helper build skips, or helper `dist/` outputs;
- signing, notarization, Gatekeeper, keychain, `electron-builder`, frozen-lockfile failures, or build script failures.

## First checks

1. Confirm the agent is operating from a MineContext checkout or has a repo root
   path. Package scripts expect a root containing `opencontext.spec`,
   `hook-opencontext.py`, `build.sh`, and `frontend/package.json`.
2. Run the bundled preflight before any mutating build:

   ```bash
   bash path/to/desktop-packaging/scripts/check_packaging_env.sh --repo-root .
   ```

   [scripts/check_packaging_env.sh](scripts/check_packaging_env.sh) reports
   Python, uv, Node, pnpm, platform, required packaging files, helper-binary
   paths, and backend-copy readiness without installing anything.
3. If the task is only to produce the backend executable, use the safer backend
   wrapper and explicitly acknowledge its mutation of build outputs:

   ```bash
   bash path/to/desktop-packaging/scripts/build_backend.sh --repo-root . --yes
   ```

   [scripts/build_backend.sh](scripts/build_backend.sh) wraps the repo backend
   PyInstaller build, verifies `dist/main/main` or `dist/main/main.exe`, and can
   optionally copy the built backend into `frontend/backend/`.
4. If the task needs packaged app artifacts, read
   [references/build-and-package.md](references/build-and-package.md) for the
   exact backend, dependency, frontend copy, and Electron command sequence.
5. If the failure involves `window_inspector`, `window_capture`, Quartz, or a
   non-macOS helper skip, read
   [references/helper-binaries.md](references/helper-binaries.md).
6. If a command failed, map the symptom in
   [references/troubleshooting.md](references/troubleshooting.md) before
   reinstalling dependencies or deleting outputs.

## Build ownership map

| Surface | Owned here | Key expectation |
| --- | --- | --- |
| Backend executable | Yes | Root `build.sh`/`build.bat` invoke PyInstaller with `opencontext.spec` and produce `dist/main/main` or `dist/main/main.exe`. |
| Frontend backend copy | Yes | `frontend/scripts/copy-prebuilt-backend.js` deletes and recreates `frontend/backend/` from root `dist/main/` plus `dist/config/`. |
| Electron package | Yes | Run package scripts from `frontend/`, not the root `package.json`. macOS/Windows package scripts copy the backend first; Linux currently requires an explicit backend copy before packaging. |
| macOS helpers | Yes | `window_inspector` and `window_capture` are Quartz/PyObjC helpers copied into the macOS app as `bin/window_inspector` and `bin/window_capture`. |
| Server behavior | No | Route CLI flags, FastAPI health/API behavior, backend logs at runtime, and config semantics to [runtime-service](../runtime-service/SKILL.md). |

## Safe operating rules

- Treat `build.sh`, `build.bat`, `pnpm run build*`, `electron-builder`, and
  backend copy commands as mutating. They may delete or recreate root `dist/`,
  root `build/`, `frontend/dist/`, and `frontend/backend/`.
- Do not run release/publish commands or signing/notarization flows by default.
  Packaging can be tested unsigned; signed release builds require the user's
  explicit credential setup and approval.
- Do not fix `copy-prebuilt-backend` failures by reinstalling frontend
  dependencies first. Check whether the root backend executable exists.
- On Linux or Windows, a skipped `window_inspector`/`window_capture` build is
  expected for the JavaScript helper build path because those helpers use macOS
  Quartz APIs.
- Keep runtime API/config/document-processing questions in
  [runtime-service](../runtime-service/SKILL.md); use this sub-skill only for
  package-time mechanics.
