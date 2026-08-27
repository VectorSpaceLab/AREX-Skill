# Build and package MineContext desktop app

This reference is the self-contained packaging playbook for MineContext's
PyInstaller backend and Electron desktop app. It distills the repo's packaging
scripts and CI sequence into safe, repeatable steps for future agents.

## Directory and package-manager rules

- The repository root owns Python packaging and the backend executable build.
  It must contain `pyproject.toml`, `opencontext.spec`, `hook-opencontext.py`,
  `build.sh`, and usually `build.bat`.
- The Electron app is under `frontend/`. Run `pnpm`, `npm run`,
  `electron-vite`, and `electron-builder` commands from `frontend/`.
- The root `package.json` is not the Electron package; in the inspected
  version it only declared a single runtime dependency. If a user ran `npm` or
  `pnpm` at the root and Electron scripts are missing, switch to `frontend/`.
- Generated package outputs are mutable:
  - backend build output: root `dist/` and root `build/`;
  - frontend backend bundle input: `frontend/backend/`;
  - Electron output: `frontend/dist/`.

## Preflight before mutation

Run the bundled preflight first:

```bash
bash path/to/desktop-packaging/scripts/check_packaging_env.sh --repo-root .
```

It does not install dependencies. It reports required tools, platform-specific
helper expectations, path presence, whether root `dist/main/main` or
`dist/main/main.exe` exists, and whether `frontend/backend/` already contains a
copied backend.

Minimum tool expectations from the repo evidence:

| Need | Expected tool or file | Notes |
| --- | --- | --- |
| Backend Python build | Python >= 3.10, preferably `uv`, plus PyInstaller | `build.sh` uses `uv sync` when `uv` exists, otherwise `python3 -m pip install -e .`; it installs PyInstaller if missing. |
| Electron dependencies | Node.js, pnpm, `frontend/pnpm-lock.yaml` | CI used Node 20, Corepack, and pnpm 9.12.0; local builds should use the frontend lockfile. |
| macOS helper binaries | macOS plus Python venv support and PyObjC dependencies | `window_inspector` and `window_capture` use Quartz and are macOS-only. |
| Package metadata | `frontend/package.json`, `frontend/electron-builder.yml` | Electron scripts and `extraResources` are defined here. |

## Backend executable build

The repo backend build sequence is:

```bash
# from the repository root
uv sync                         # preferred when uv is available
# or: python3 -m pip install -e .
./build.sh
```

Use the bundled wrapper when possible:

```bash
bash path/to/desktop-packaging/scripts/build_backend.sh --repo-root . --yes
```

Important behavior of the underlying backend build:

1. Checks for `python3`.
2. Uses `uv sync` when `uv` is available; otherwise installs the package in
   editable mode with pip.
3. Ensures PyInstaller is importable in the selected Python/uv environment.
4. Deletes root `dist/` and root `build/`.
5. Runs PyInstaller with `opencontext.spec` using `--clean --noconfirm`.
6. Verifies `dist/main/main` on Unix-like systems or `dist/main/main.exe` on
   Windows.
7. On macOS, attempts an ad-hoc code signature on the backend executable.
8. Copies root `config/` into `dist/config/` when present.

The PyInstaller spec is named `opencontext.spec` but the produced executable is
named `main`. It analyzes `opencontext/cli.py`, includes `config/config.yaml`,
`opencontext/web/static`, and `opencontext/web/templates`, declares hidden
imports for uvicorn, ChromaDB, hnswlib, SQLite, SSL/hashlib, and uses the
runtime hook `hook-opencontext.py`. The runtime hook sets bundled resource
environment variables when the program is frozen.

Expected backend outputs after success:

```text
dist/main/main          # macOS/Linux
# or
dist/main/main.exe      # Windows

dist/config/            # copied config files when root config/ exists
```

## Copy backend into the Electron package input

Electron packaging expects a prebuilt backend under `frontend/backend/`. The
copy script is:

```bash
cd frontend
node scripts/copy-prebuilt-backend.js
# equivalent package script:
pnpm run copy-backend
```

What the copy script does:

1. Computes the source as root `dist/main/`.
2. Chooses executable name `main.exe` on Windows and `main` elsewhere.
3. Deletes any existing `frontend/backend/`.
4. Copies every entry from root `dist/main/` into `frontend/backend/`.
5. Verifies `frontend/backend/main` or `frontend/backend/main.exe`.
6. Makes the copied Unix executable executable.
7. Copies root `dist/config/*` into `frontend/backend/config/` when available.

If it fails with "Pre-built onedir executable not found", diagnose the missing
root backend build first. Do not start by reinstalling frontend dependencies.

## Install frontend dependencies

From `frontend/`:

```bash
pnpm install
```

For CI-like reproducibility:

```bash
corepack enable
corepack prepare pnpm@9.12.0 --activate
cd frontend
pnpm install --frozen-lockfile
```

If `--frozen-lockfile` fails, treat it as a lockfile/package metadata mismatch.
Do not delete the lockfile as a first response. Either use the pnpm version that
matches the lockfile or ask whether regenerating the lockfile is allowed.

## Electron build scripts

The relevant `frontend/package.json` scripts are:

| Script | Current behavior |
| --- | --- |
| `copy-backend` | Runs `node scripts/copy-prebuilt-backend.js`. |
| `build:externals` | On non-Windows, makes `build-python.sh` executable. |
| `build` | Runs `build:externals`, `node build-python.js`, typechecks, deletes `frontend/dist/`, then runs `electron-vite build`. |
| `build:mac` | Runs `copy-backend`, `build`, then `electron-builder --mac`. |
| `build:win` | Runs `copy-backend`, `build`, then `electron-builder --win`. |
| `build:linux` | Runs `build`, then `electron-builder --linux`; it does not currently run `copy-backend` itself. |
| `publish` | Runs backend copy, build, and publishing for macOS/Windows; do not use as a default packaging command. |

### macOS package

```bash
# repository root: backend first
bash path/to/desktop-packaging/scripts/build_backend.sh --repo-root . --yes --copy-to-frontend

# frontend: package
cd frontend
pnpm install
pnpm run build:mac
```

`build:mac` already runs `copy-backend`, so `--copy-to-frontend` is optional if
you trust the package script to do the copy. Keeping it in the wrapper is useful
when you want to verify `frontend/backend/` before invoking Electron.

macOS Electron configuration adds the helper binaries as extra resources:

```text
externals/python/window_inspector/dist/window_inspector/window_inspector -> bin/window_inspector
externals/python/window_capture/dist/window_capture/window_capture       -> bin/window_capture
```

The inspected `electron-builder.yml` has macOS notarization disabled while still
referencing an after-sign hook. Treat signed/notarized release builds as a
separate credentialed release flow, not as the default local build path.

### Windows package

Backend evidence includes a Windows batch build:

```bat
build.bat
```

It uses `py` or `python`, prefers `uv sync`, runs PyInstaller with
`opencontext.spec`, verifies `dist\main\main.exe`, and copies config into
`dist\config`. The frontend docs said Windows backend build was "not support
yet" while CI and package scripts include Windows paths; if a Windows build
fails, trust the concrete script output and keep the support-status mismatch in
mind.

Then from `frontend/`:

```powershell
pnpm install
pnpm run build:win
```

Windows does not use the macOS Quartz helper resources.

### Linux package

The release workflow builds the backend on Linux with `build.sh`, then invokes
`pnpm run build:linux`. In the inspected package scripts, `build:linux` does not
call `copy-backend`, so a robust local sequence is:

```bash
bash path/to/desktop-packaging/scripts/build_backend.sh --repo-root . --yes --copy-to-frontend
cd frontend
pnpm install
pnpm run build:linux
```

Linux helper builds are skipped by `build-python.js` because the helpers are
macOS Quartz tools. This is expected and should not be treated as a packaging
failure unless the command exits nonzero.

## CI sequence as reference only

The documented CI sequence used a matrix for macOS, Windows, and Linux:

1. Set the frontend package version from a release tag.
2. Install Node 20.
3. Enable Corepack and activate pnpm 9.12.0.
4. Set up Python 3.11.
5. Install/sync Python dependencies with `uv`.
6. Run `pnpm install --frozen-lockfile` in `frontend/`.
7. Build the backend with `build.sh` or `build.bat` depending on OS.
8. Build the Electron target with `pnpm run build:mac`, `build:win`, or
   `build:linux`.
9. Draft release artifacts from `frontend/dist/`.

Use this as a reproducibility reference only. Do not run release publication or
credentialed signing/notarization steps unless the user explicitly asks and has
provided the necessary release setup.
