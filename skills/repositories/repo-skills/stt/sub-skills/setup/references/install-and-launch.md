# Install and Launch

This guide covers the normal path from a clean checkout to a running local server.

## Recommended environment

- Use Python 3.11 when possible. The documented support range is Python 3.9 to 3.11.
- Create a fresh virtual environment for the project.
- Keep `devtype=cpu` for a CPU-only launch, or switch to `devtype=cuda` only after CUDA and cuDNN are ready.

Example:

```bash
python -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, activate the environment with `venv\Scripts\activate`.

If the dependency resolver reports conflicts, retry with:

```bash
python -m pip install -r requirements.txt --no-deps
```

If you want CUDA acceleration, replace the CPU torch wheel with the CUDA wheel after the base install:

```bash
python -m pip uninstall -y torch
python -m pip install torch --index-url https://download.pytorch.org/whl/cu121
```

The verified environment also worked cleanly after pinning `numpy<2`.

## Runtime binaries

`ffmpeg` and `ffprobe` must be available at runtime. The app checks for both commands and also prepends the project root and a local `ffmpeg/` folder to `PATH` during startup, so any of these layouts work:

- system-wide installation on `PATH`
- binaries placed beside the project files
- binaries placed in a local `ffmpeg/` directory

## Model placement

Model files belong under `models/`.

- Pre-downloaded model folders can be copied into `models/` before launch.
- If `models/` is empty, the first time a selected model is needed the app may try to download it automatically.
- Keep the selected model name consistent with the folder or Hub ID you expect Faster-Whisper to resolve.

## Smoke checks before launch

Use the bundled checks against the app checkout:

```bash
python ../../../scripts/check-runtime.py --repo-root <checkout>
python ../scripts/check-cuda.py
```

Use the CUDA check only when you plan to run with `devtype=cuda` or when GPU readiness is unclear. Add `--strict` if a missing CUDA stack should fail the command.

## Launch sequence

Prefer the bundled wrapper:

```bash
python ../scripts/launch-server.py --repo-root <checkout>
```

The native Windows batch launcher follows the same pattern by calling the virtual environment's Python executable on the app launcher from the project root. The bundled Python launcher keeps that behavior cross-platform and adds preflight checks.

## What `start.py` does on launch

- Reads `set.ini` and applies the runtime defaults.
- Starts a background update-check thread.
- Starts a transcription worker thread.
- Creates a gevent WSGI server on `web_address`.
- Opens the local browser automatically.
- Prints a CPU-mode notice when `devtype=cpu` and a CUDA hint is available.

The default address is `127.0.0.1:9977`.

## Expected launch behavior

A successful launch should look like this:

1. The helper finishes its preflight checks.
2. `start.py` binds the local address from `set.ini`.
3. The browser opens automatically, or the printed URL can be opened manually.
4. The web UI shows the upload area and model selector.

## CPU vs CUDA

- Use `devtype=cpu` when you want the safest first launch or the host has no working CUDA stack.
- Use `devtype=cuda` only after `scripts/check-cuda.py` reports that CUDA and cuDNN are ready.
- If the host has CUDA but you want CPU mode, keep `devtype=cpu`; the launcher does not override that choice.

## After launch

Once the server is reachable, switch to [`transcription`](../../transcription/SKILL.md) for browser uploads, API usage, and client behavior.
