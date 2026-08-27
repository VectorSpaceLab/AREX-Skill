# Cross-Cutting Troubleshooting

## Startup and installation

### `WEBUI_SECRET_KEY` missing

- **Symptom**: direct backend startup fails early with a message that the secret key is required.
- **Likely cause**: the backend was started directly instead of through `open-webui serve` or the environment variable was not set.
- **Recovery**: use `open-webui serve`, or set `WEBUI_SECRET_KEY` to a long random value before invoking the backend.

### Editable install pulls frontend tooling

- **Symptom**: source install triggers Node/npm activity or frontend build output.
- **Likely cause**: the project build hook prepares frontend assets during editable/source installation.
- **Recovery**: ensure Node.js/npm are present and let the build finish; if you only need backend inspection, use the already-installed package rather than rerunning the build.

### Version / import confusion

- **Symptom**: the CLI help works, but a version flag or direct import behaves unexpectedly.
- **Likely cause**: version information is best read from `importlib.metadata.version('open-webui')`; the root CLI is not a bare `--version` command.
- **Recovery**: use `python -I -c "from importlib.metadata import version; print(version('open-webui'))"` and `open-webui --help`.

## Deployment and connectivity

### Ollama connection error

- **Symptom**: the UI cannot reach Ollama or the provider URL.
- **Likely cause**: `OLLAMA_BASE_URL` is wrong, the service is unreachable, or the Docker network does not expose the host correctly.
- **Recovery**: verify the URL, check host networking or `host.docker.internal`, and confirm the model backend is listening.

### Slow response / timeout

- **Symptom**: generation stalls or times out on long responses.
- **Likely cause**: upstream timeout defaults are too aggressive for the selected provider.
- **Recovery**: adjust the relevant `AIOHTTP_CLIENT_TIMEOUT*` setting for the deployment and the affected provider path.

### Docker overlay mismatch

- **Symptom**: a compose overlay fails to parse or the wrong service variant starts.
- **Likely cause**: the `gpu`, `playwright`, `data`, `api`, or `otel` overlay was combined incorrectly.
- **Recovery**: validate the compose config first, then add overlays one by one.

## Auth, admin, and identity

### Trusted header / SSO issues

- **Symptom**: login succeeds at the proxy but Open WebUI reports invalid or missing identity information.
- **Likely cause**: trusted headers, OAuth provider mapping, or SCIM settings do not match the upstream identity source.
- **Recovery**: verify the configured headers and provider names, then re-check the admin bootstrap variables.

### Existing users block auth changes

- **Symptom**: disabling authentication is rejected on a populated deployment.
- **Likely cause**: the database already contains users and the app protects against unsafe auth changes.
- **Recovery**: adjust the configuration on a fresh instance or keep auth enabled.

### Redis / storage / telemetry failures

- **Symptom**: sessions, uploads, or observability export fail.
- **Likely cause**: `REDIS_URL`, storage credentials, or `OTEL_*` endpoint settings are incorrect.
- **Recovery**: verify the service endpoint, credentials, and environment variables for the selected backend.

## Knowledge and extensions

### File or document processing fails

- **Symptom**: uploads appear to succeed but extraction or retrieval stays empty.
- **Likely cause**: unsupported format, size limit, loader dependency issue, or a retrieval backend mismatch.
- **Recovery**: check the file-format and size guidance in the knowledge-files sub-skill and re-run the loader with a smaller sample.

### Extension / tool-server errors

- **Symptom**: tool calls, Playwright helpers, or browser-backed extension workflows fail.
- **Likely cause**: browser helper unavailable, tool server timeout, SSL mismatch, or missing optional extension dependency.
- **Recovery**: confirm the helper service is reachable, then check the extension-specific reference and sub-skill troubleshooting page.

## Commands worth re-running

- `open-webui --help`
- `open-webui serve --help`
- `python -I -c "from importlib.metadata import version; print(version('open-webui'))"`
- `docker compose config` for the selected overlay set
