# Server and App Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `marker_gui` fails with missing `streamlit` or a launcher `FileNotFoundError` | Streamlit is optional and not installed. | Install `streamlit`; install `streamlit-ace` too if using `marker_extract`. If no UI is needed, use the conversion CLI sub-skill instead. |
| `marker_extract` fails with missing `streamlit_ace` | The extraction editor dependency is optional. | Install `streamlit-ace`, then relaunch `marker_extract`. |
| `marker_server --help` or import fails with missing `fastapi`, `uvicorn`, or `python-multipart` | Server dependencies are optional for Marker users who only convert locally. | Install `fastapi uvicorn python-multipart`, then rerun `python scripts/server_cli_smoke.py --check-import`. |
| FastAPI reports form-data support is missing | `python-multipart` is missing. | Install `python-multipart`; it is required for `/marker/upload`. |
| Browser cannot connect to the server | Wrong host/port, blocked port, or server not started. | Start with `marker_server --host 127.0.0.1 --port 8000` for local-only testing; use a deliberate bind address for remote access. |
| `/marker` returns file-not-found or permission errors | The JSON `filepath` is evaluated on the server machine, not the client machine. | Use `/marker/upload` for client-local files, or mount/copy the file where the server process can read it. |
| Upload requests leave files under `uploads` | The local server writes uploads relative to its working directory and removes them after the normal success path. | Use unique filenames and cleanup logic in production adaptations; inspect and clean `uploads` after interrupted or invalid requests. |
| Invalid `output_format` causes an assertion/error instead of a clean response | The server asserts the format before conversion. | Prevalidate `markdown`, `json`, `html`, or `chunks` in clients; use the client template’s argparse choices. |
| First request or startup is slow | Marker model artifacts are loading or downloading. | Warm caches before user-facing demos; for Modal, run a model warmup function and use a persistent volume. |
| GPU out-of-memory or high latency under load | Multiple large documents or concurrent requests exceed GPU/VRAM capacity. | Limit request concurrency, reduce document/page ranges, choose a larger GPU, serialize conversions, or use a queue. |
| Streamlit extraction app is unsafe for public users | The Pydantic schema panel can execute schema code during conversion to a runtime class. | Keep it local/trusted or isolate it; do not expose it as a public service without hardening. |
| Modal deploy fails before app creation | Modal authentication/account setup or cloud environment selection is incomplete. | Complete Modal setup, confirm the target environment, and verify billing/quota before deploying. |
| Modal endpoint URL is unknown | The URL is assigned at deployment time. | Read deploy output, use Modal dashboard, or use Modal APIs from a local entrypoint after deployment. |
| Modal `local_entrypoint` cannot find the service | The app was not deployed, the app/class name changed, or the environment name differs. | Deploy first, keep app/class names aligned, and pass the intended Modal environment. |
| Hosted endpoint is not production-ready | The reference server is a demo and lacks hardening. | Add authentication, request size limits, validation, rate limits, timeouts, structured logging, monitoring, and error handling. |
| LLM-related request changes fail | LLM service setup is outside the local server’s default request model. | Route LLM service configuration and `use_llm` adaptation to `../llm-extraction-services/`. |
