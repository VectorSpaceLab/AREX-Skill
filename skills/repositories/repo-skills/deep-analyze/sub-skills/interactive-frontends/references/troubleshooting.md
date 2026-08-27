# Troubleshooting

Start with [scripts/check_webui_prereqs.py](../scripts/check_webui_prereqs.py); it reports ports, env, Node/npm, Python deps, Docker image presence, and PDF prereqs without starting or stopping anything.

## Port conflicts

**Symptoms**

- The browser demo refuses to start.
- Jupyter says its port is already in use.
- You see stale backend or frontend listeners.

**Likely cause**

- Another process already owns `4000`, `8200`, `8100`, or the configured Jupyter port.

**What to do**

- Confirm whether the current process is the one you want to keep.
- If not, choose a different port or stop the conflicting service with care.
- Do not rely on the start script to fix an unknown process tree blindly.

## API or model service unavailable

**Symptoms**

- The CLI reports that the API server is offline.
- The WebUI cannot fetch workspace or chat data.
- Jupyter startup fails when the model client tries to list models.

**Likely cause**

- The backend API is not running, the model endpoint is wrong, or the model service itself is down.

**What to do**

- Verify the model service first.
- Verify that the backend base URL and model base URL match the expected ports.
- If a UI starts but chat fails, the model base is usually the first thing to check.

## Node/npm install or build problems

**Symptoms**

- `npm run dev` fails.
- The frontend build complains about missing packages.
- The Jupyter MCP bridge cannot launch.

**Likely cause**

- `node`, `npm`, `npx`, or the installed frontend packages are missing.

**What to do**

- Install Node.js.
- Run `npm install` in the browser frontend.
- Re-run the checker to confirm the frontend packages and executables are present.
- For Jupyter, make sure `npx` can launch the MCP bridge command.

## Docker execution mode without a built image

**Symptoms**

- Code execution fails immediately in browser mode.
- The demo says Docker execution is enabled but nothing runs.

**Likely cause**

- `DEEPANALYZE_EXECUTION_MODE=docker` is set, but the execution image does not exist yet.

**What to do**

- Build the image manually from `Dockerfile.exec` before trying Docker execution.
- Make sure `DEEPANALYZE_DOCKER_IMAGE` matches the built tag.
- Treat missing-image failures as expected until the image is built.

## PDF export or Chinese report problems

**Symptoms**

- Export fails at PDF stage.
- The export falls back to Markdown only.
- Chinese labels or chart text look garbled.

**Likely cause**

- `pypandoc`, `pandoc`, or `xelatex` is missing.
- The CJK font is not installed or not selected.

**What to do**

- Install `xelatex` manually.
- Let the backend auto-download `pandoc` if that is enabled.
- Set `DEEPANALYZE_PDF_CJK_MAINFONT` to an installed CJK font such as `SimHei` or `WenQuanYi Zen Hei`.
- If Matplotlib text is still garbled, clear the Matplotlib cache and refresh the font installation.
- Remember that the Docker execution image already includes a font alias for SimHei-style rendering, but host setups still need the right fonts.

## Jupyter MCP or uv failures

**Symptoms**

- `uv run CLI.py` exits early.
- The notebook never appears.
- MCP calls fail even though Jupyter Lab is open.

**Likely cause**

- `.env` or `config.toml` is missing.
- `uv` or the Python environment is broken.
- `START_JUPYTER=false` was chosen without a live Lab server.
- The configured Jupyter port is already occupied.

**What to do**

- Recreate `.env` and confirm `config.toml` exists.
- Re-run dependency sync.
- Check whether Jupyter Lab is actually serving on the configured port.
- Make sure Node.js is available for the MCP bridge.

## Unsupported file preview

**Symptoms**

- The preview panel says the file is unsupported.
- The UI falls back to a binary view.
- Uploading a Python script is rejected.

**Likely cause**

- The file type is outside the preview matrix, or the backend blocks the upload extension.

**What to do**

- Download the file instead of previewing it.
- Convert the file to a preview-friendly type such as text, CSV, Excel, SQLite, image, or PDF.
- Remember that `workspace/download-bundle` only packages generated outputs, not every uploaded input file.
- If the upload is a `.py` file, move the code into the workspace by another means instead of uploading it.
