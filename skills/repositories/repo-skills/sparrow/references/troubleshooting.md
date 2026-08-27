# Cross-cutting troubleshooting

Use this page when a Sparrow task fails before the problem clearly belongs to one sub-skill.

## Installation/import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `python -m sparrow_parse` fails | `sparrow-parse` package not installed in the active Python | Install `sparrow-parse` in the target environment; verify Python version is 3.12-compatible. |
| `sparrow-parse` console command fails with `cannot import name 'main'` | Upstream package metadata points the console script at the wrong object | Do not use that console command as proof of failure for extraction. Use package imports or Sparrow LLM engine/API. |
| PDF conversion fails or `pdftoppm` missing | Poppler is not installed or not on `PATH` | Install Poppler for the platform, then rerun a tiny PDF conversion check before model inference. |
| `torch`, `transformers`, `vllm`, `mlx_vlm`, `paddleocr`, `prefect`, or `oracledb` import fails | Optional workflow dependencies are missing | Install only the dependency group needed for the chosen workflow; do not install all backends unless the user asks. |

## Backend failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| MLX backend selected on Linux/Windows | MLX path is Apple Silicon-specific | Choose Ollama, vLLM/CUDA, HF, Mistral, or a CPU/cloud alternative. |
| vLLM/CUDA backend imports but model inference fails | Model not downloaded/served, insufficient VRAM, driver/wheel mismatch, or unsupported compute capability | Run a small torch CUDA check, verify vLLM version/model path, and start with a smaller model or single-page input. |
| Ollama backend reports connection/model error | Ollama daemon not running or model not pulled | Run an Ollama list/connection check, start the daemon, and pull the exact model name before extraction. |
| Mistral/HF backend returns auth/network errors | Missing token, invalid endpoint, or blocked network | Confirm credentials outside generated files and retry with a minimal text/image request. |
| PaddleOCR startup is slow or downloads weights | First full OCR invocation initializes model assets | Use OCR response fixture smoke first; run full OCR only after dependency/model readiness is expected. |

## Query/schema failures

- Validate query JSON before calling a model.
- Use simple schemas first: strings, numbers, `str or null`, or arrays of objects.
- Use `"*"` only for generic extraction or page-type classification; it bypasses normal schema validation paths.
- If model output is prose/markdown instead of JSON, add a stricter prompt or use markdown-first/table-template workflows when the document is table-heavy.
- Distinguish invalid user query, invalid model output, and schema-validation mismatch; each has different recovery steps.

## API/service failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| API docs path unavailable | Wrong port/service not running | Verify the service root endpoint and the `/api/v1/.../docs` path on the configured port. |
| Multipart request rejected | Wrong field name, boolean string, comma-separated `options`, invalid `crop_size`, or file form field missing | Use the API/CLI request builder and compare against the endpoint field table. |
| Protected access returns 403 | `protected_access=true` and missing/invalid `sparrow_key` or usage limit exceeded | Check config source and decide whether config-based or DB-backed validation is active. |
| Database errors during API startup/logging | DB enabled without reachable Oracle settings | Disable DB paths for local smoke checks or verify DB config before starting dashboard/logging flows. |
| Agent async task never progresses | Redis/Celery worker not running or wrong queue/worker registration | Use sync endpoint first; then verify Redis, worker queues, and registered agents. |

## UI failures

- If upload validation fails before network traffic, inspect UI accepted types and file size/type logic.
- If valid upload reaches backend but fails, test the LLM/OCR/agent API directly before debugging frontend state.
- If dashboard/feedback data is missing, separate frontend rendering from API logging and Oracle DB availability.
- If Next and Gradio accept different file types, align UI validation with backend-supported image/PDF types before promising support.

## Safe first commands

```bash
python scripts/check_sparrow_environment.py --json
python scripts/sparrow_request_builder.py extraction --query '{"field":"str"}' --backend ollama --model my-model --file-path sample.pdf
python sub-skills/api-engine-and-cli/scripts/json_validation_smoke.py --help
python sub-skills/ocr-service/scripts/ocr_response_smoke.py --dump-json
python sub-skills/agent-workflows/scripts/agent_payload_smoke.py --case all
python sub-skills/ui-and-deployment/scripts/ui_config_check.py --embedded
```

Run these from the generated skill directory. They do not start long-running services or call external model APIs.
