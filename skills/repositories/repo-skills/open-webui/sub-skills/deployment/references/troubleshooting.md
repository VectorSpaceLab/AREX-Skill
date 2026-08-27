# Deployment Troubleshooting

## Secret key and startup failures

### Missing `WEBUI_SECRET_KEY`

- **Symptom**: direct backend startup exits with a message that the secret key is required.
- **Cause**: the backend was launched directly instead of through the app's normal startup path.
- **Fix**: use `open-webui serve`, or provide `WEBUI_SECRET_KEY` before launching the backend.

### `open-webui main --version` or other non-service startup paths fail

- **Symptom**: the command parses but then complains about the secret key.
- **Cause**: `main` is not the safe version-check path; it still exercises the startup stack.
- **Fix**: use `python -I -c "from importlib.metadata import version; print(version('open-webui'))"` for version checks and `open-webui --help` for CLI routing.

## Docker and container issues

### Container starts but the UI cannot connect to Ollama

- **Symptom**: the WebUI loads but model access or chat generation fails.
- **Cause**: `OLLAMA_BASE_URL` does not point to a reachable backend, or the host/container network is wrong.
- **Fix**: verify the URL and the network mode; use `host.docker.internal` or a reachable service name.

### Wrong image tag or runtime variant

- **Symptom**: GPU features are missing, or Ollama is not bundled as expected.
- **Cause**: the wrong public image tag was selected.
- **Fix**: use `:main` for the default image, `:cuda` for NVIDIA GPU hosts, and `:ollama` for the bundled Ollama path.

### Data disappears after restart

- **Symptom**: chats, uploads, or config vanish after the container is recreated.
- **Cause**: the data volume was not mounted or the wrong mount target was used.
- **Fix**: mount persistent storage to `/app/backend/data`.

## Browser and multimodal deployment helpers

### Playwright-backed loaders fail

- **Symptom**: browser-assisted loaders or web-page helpers do not start.
- **Cause**: the browser helper service is missing or `WEB_LOADER_ENGINE=playwright` was set without the companion service.
- **Fix**: check the browser helper endpoint and the loader-engine setting together.

### GPU runtime not detected

- **Symptom**: the CUDA image runs, but GPU acceleration is not available inside the container.
- **Cause**: the host driver or container runtime is not exposing NVIDIA GPUs correctly.
- **Fix**: validate the host with `nvidia-smi`, then confirm the container runtime exposes the device.

## Source install and build-hook issues

### Editable install pulls frontend tooling

- **Symptom**: `pip install -e .` downloads or builds frontend dependencies.
- **Cause**: the project build hook prepares frontend assets as part of source installation.
- **Fix**: ensure Node.js/npm are present and let the build finish.

### Development server fails immediately

- **Symptom**: `open-webui dev` or the dev wrapper exits before listening.
- **Cause**: missing secret key, port conflict, or a bad runtime variable.
- **Fix**: check the secret-key requirement, free the port, and re-run the install smoke script.

## Recovery checklist

1. Run `../../../scripts/check-install.sh`.
2. Verify the selected image tag or startup command.
3. Check `WEBUI_SECRET_KEY`, `OLLAMA_BASE_URL`, and the data mount.
4. Retry with `open-webui serve` before dropping to a direct backend invocation.
