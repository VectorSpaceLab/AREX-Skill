# Desktop packaging troubleshooting

Use this matrix before deleting build outputs, reinstalling dependencies, or
changing package scripts. Packaging failures are often caused by running a
command from the wrong directory or by missing the root backend executable before
copying into the Electron app.

## Fast diagnosis flow

1. Identify the command and directory:
   - backend build commands run from the repository root;
   - Electron commands run from `frontend/`;
   - the root `package.json` is not the Electron package.
2. Run the preflight:

   ```bash
   bash path/to/desktop-packaging/scripts/check_packaging_env.sh --repo-root .
   ```

3. If `copy-prebuilt-backend` failed, check root `dist/main/main` or
   `dist/main/main.exe` before touching frontend dependencies.
4. If `pnpm run build` failed during helper binaries, decide whether the target
   host is macOS. Linux/Windows helper skips are expected for the JavaScript
   build path.
5. If `electron-builder` failed, check `frontend/backend/`, helper outputs for
   macOS, icon/build resources, and target-specific settings.
6. Route backend server startup, API health, port conflicts after launch, and
   config semantics to `runtime-service`.

## Symptom matrix

| Symptom | Most likely cause | Action |
| --- | --- | --- |
| `python3 is not found` during `build.sh` | Python unavailable on PATH | Install or select Python >= 3.10 before building; rerun preflight. |
| `uv: command not found` | `uv` is absent | `build.sh` can fall back to `python3 -m pip install -e .`; if reproducibility matters, ask before installing `uv`. |
| PyInstaller command missing | PyInstaller not installed in selected backend environment | Let `build.sh` install it, or install it into the active uv/pip environment with user approval. |
| PyInstaller fails on hidden imports such as ChromaDB, hnswlib, uvicorn, SSL, or SQLite | Frozen dependency not collected | Check `opencontext.spec` hidden imports and installed package versions; add the missing hidden import only after confirming the module exists in the environment. |
| Frozen backend cannot find config/static/templates | Data files or runtime hook missing | Verify `opencontext.spec` includes config and web data, and that `hook-opencontext.py` is present. |
| `dist/main/main` missing after backend build | PyInstaller failed or output was cleaned | Read the PyInstaller log; do not continue to frontend copy until the root backend executable exists. |
| `Pre-built onedir executable not found` in `copy-prebuilt-backend` | Root backend was not built, or `dist/` was deleted | Run the backend build from the repository root, then rerun `pnpm run copy-backend`. |
| `Backend executable missing after copy` | Partial copy, wrong executable name for platform, or source output incomplete | Verify root `dist/main/` contains `main` or `main.exe`; rerun copy after a clean backend build. |
| `frontend/backend/` disappears | Copy script intentionally deletes and recreates it | This is expected; verify it is repopulated from root `dist/main/`. |
| `pnpm: command not found` | pnpm unavailable | Use Corepack or install pnpm with user approval; run commands from `frontend/`. |
| `Missing script: build:mac` or Electron scripts absent | Command run against root `package.json` | Change to `frontend/` and rerun. |
| `pnpm install --frozen-lockfile` fails | Lockfile/package metadata mismatch or incompatible pnpm version | Use the pnpm version expected by the lockfile/CI, or ask before regenerating the lockfile. |
| TypeScript typecheck fails during `pnpm run build` | Frontend code issue, dependency mismatch, or generated types mismatch | Fix the reported TypeScript error; do not bypass typecheck for release packaging unless the user accepts a dev-only artifact. |
| `frontend/dist/` vanished | `pnpm run build` deletes it before `electron-vite build` | Expected mutation; inspect the later `electron-vite` or `electron-builder` error. |
| Linux package lacks backend resources | `build:linux` does not currently run `copy-backend` | Run `pnpm run copy-backend` after the root backend build and before `pnpm run build:linux`. |
| `window_capture` or `window_inspector` skipped on Linux | JavaScript helper builder skips all non-darwin platforms | Expected; these helpers are macOS-only Quartz binaries. |
| Helper build fails with Quartz import errors on macOS | Missing PyObjC dependencies in helper venv | Install the helper `requirements.txt` in that helper venv and rebuild with the matching spec. |
| Helper build fails with Quartz import errors on Linux/Windows | Wrong builder path; helpers cannot build there | Use the JavaScript builder skip path and package without macOS helpers for non-macOS targets. |
| macOS app signing, Gatekeeper, or notarization fails | Missing signing identity, keychain setup, or notarization account configuration | Treat as a release/signing setup problem. Unsigned local packaging can still be used for build validation; ask before using credentialed signing flows. |
| PyInstaller signing is skipped on macOS | Signing environment was not configured for the backend build | Expected for local unsigned builds; only release flows should require configured signing material. |
| `electron-builder` tries to publish or asks for release token | Release/publish command was used | Use `build:mac`, `build:win`, `build:linux`, or `build:unpack` for local package validation; do not use `publish` by default. |
| Windows path uses `main` instead of `main.exe` | Platform executable name mismatch | On Windows, expect `dist\main\main.exe` and `frontend\backend\main.exe`. |
| macOS/Linux executable is not runnable after copy | Executable bit missing or copy interrupted | `copy-prebuilt-backend.js` runs `chmod +x`; rerun the copy and verify file mode. |

## Difficult synthetic usability cases

Use these when verifying this sub-skill beyond native scripts:

1. **Linux helper skip explanation**: On a Linux host, a user sees the helper
   build log skip `window_capture`/`window_inspector` and asks whether the build
   is broken. The agent should explain Quartz/macOS exclusivity, note the
   misleading non-darwin log wording, and continue with Linux packaging instead
   of trying to install PyObjC.
2. **Backend copy without backend build**: `cd frontend && pnpm run copy-backend`
   fails because root `dist/main/main` or `dist/main/main.exe` is missing. The
   agent should diagnose the absent PyInstaller backend output and run or ask to
   run the backend build before reinstalling frontend dependencies.

## When to stop and ask

Ask the user before:

- installing or upgrading host-level Python, Node, pnpm, uv, Xcode tools,
  Homebrew, Corepack-managed package managers, or signing toolchains;
- deleting or regenerating lockfiles;
- running release publication, signing, notarization, or credentialed upload
  commands;
- bypassing TypeScript checks, PyInstaller verification, or missing backend
  resources for a user-facing artifact.
