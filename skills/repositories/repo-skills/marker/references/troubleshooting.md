# Marker Cross-Cutting Troubleshooting

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError: marker` or console scripts missing | `marker-pdf` is not installed in the active Python environment | Install `marker-pdf`, then run `python scripts/marker_environment_check.py --check-cli`. |
| Non-PDF files fail to open | Optional document dependencies are missing | Install `marker-pdf[full]` only if those document types are in scope. |
| First conversion is slow or appears to download files | Model/cache initialization | Preload/cache models for production, and use CLI help or dry-run scripts for environment smoke tests. |
| CUDA out of memory or slow batch conversion | Too many workers, high page/image resolution, or wrong device | Lower `--workers`, set `TORCH_DEVICE`, use smaller batches/config keys, or convert fewer files at once. |
| `marker_gui` or `marker_extract` fails before opening UI | Streamlit app dependencies are absent | Install the Streamlit dependencies or use `marker_single`/Python API instead. |
| `marker_server` import or upload support fails | FastAPI server dependencies are absent | Install `fastapi`, `uvicorn`, and `python-multipart`; read `sub-skills/server-deployment/SKILL.md`. |
| LLM flags do nothing | `--use_llm` was omitted | Set `--use_llm`; `llm_service` alone does not create a service. |
| LLM request fails with auth/rate/JSON errors | Provider credential, endpoint, model, or response schema issue | Route to `sub-skills/llm-extraction-services/SKILL.md` and use its dry-run probes. |
| Class path import error for converter/processor/renderer | Full module path is wrong or dependency is missing | Route to `sub-skills/configuration-extension/SKILL.md` and inspect config/class loading. |
| Output format surprises | Markdown, JSON, HTML, and chunks have different result models | Route to `sub-skills/conversion-cli-api/references/output-formats.md`. |

## Routing Recovery

- If the user asks for commands or Python snippets to convert files, use `conversion-cli-api`.
- If the user asks why config/class loading/debug output behaves a certain way, use `configuration-extension`.
- If the user mentions `use_llm`, provider names, API keys, schemas, extraction, or JSON response validation, use `llm-extraction-services`.
- If the user mentions local servers, uploads, Streamlit, Modal, endpoints, or clients, use `server-deployment`.
