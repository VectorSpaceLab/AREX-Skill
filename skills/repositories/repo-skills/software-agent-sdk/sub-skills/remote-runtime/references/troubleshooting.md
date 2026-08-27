# Remote Runtime Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `python -m openhands.agent_server --help` fails | Packages not installed or import path broken. | Install the four OpenHands distributions or run `make build` in a checkout. |
| `/api/*` returns 503 | Deferred init is enabled and the server is still dormant. | Call `/api/init` with the bootstrap key header and body. |
| Authenticated requests fail with 401 | Missing or wrong session API key. | Send `X-Session-API-Key` matching the configured session key. |
| Browser check fails | Browser runtime unavailable. | Either install a browser or leave browser tooling out of the workflow. |
| Docker workspace does not start | Docker daemon, port, or image problem. | Check `docker version`, free the port, and verify the image/tag. |
| Apptainer workspace does not start | Apptainer CLI missing or invalid image. | Install Apptainer or switch to Docker/runtime API. |
| Remote custom tool cannot be imported | Module path not preloaded. | Use `--import-modules` or `OH_EXTRA_PYTHON_PATH` before the conversation starts. |
| WebSocket status looks finished but hooks still run | Status update is a hint, not the final server truth. | Wait for the authoritative state snapshot or REST confirmation. |
