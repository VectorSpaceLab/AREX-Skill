# Root Troubleshooting

Use this reference for cross-cutting txtai failures before routing to a sub-skill-specific troubleshooting page.

## Import or Package Metadata Fails

Symptoms:

- `ModuleNotFoundError: No module named 'txtai'`
- `importlib.metadata.PackageNotFoundError: txtai`
- `pip check` reports broken requirements

Actions:

1. Verify Python is 3.10 or newer.
2. Install or reinstall `txtai` in the active project environment, not a different shell or service environment.
3. Run:
   ```bash
   python -m pip check
   python scripts/check_txtai_environment.py --json
   ```
4. If only optional modules fail, install the focused extra from [installation-and-extras.md](installation-and-extras.md) rather than `txtai[all]`.

## Optional Extras Missing

| Symptom | Likely extra | Route |
| --- | --- | --- |
| `smolagents is not available` or `Agent` placeholder construction fails | `txtai[agent]` | `sub-skills/agents-and-llm-orchestration/references/troubleshooting.md` |
| `fastapi`, `uvicorn`, `fastapi_mcp`, upload, or API import errors | `txtai[api]` | `sub-skills/api-and-deployment/references/troubleshooting.md` |
| `docling`, `chonkie`, `pandas`, `tika`, document parsing errors | `txtai[pipeline-data]` | `sub-skills/pipelines-and-workflows/references/troubleshooting.md` |
| `litellm`, `llama_cpp`, hosted LLM backend errors | `txtai[pipeline-llm]` | `sub-skills/agents-and-llm-orchestration/references/backend-and-tooling.md` |
| graph/cypher/network errors | `txtai[graph]` | `sub-skills/embeddings-search/references/troubleshooting.md` |
| DuckDB/SQLAlchemy content database errors | `txtai[database]` | `sub-skills/embeddings-search/references/troubleshooting.md` |

## Model Download or Offline Failures

Symptoms:

- Hugging Face timeout, 401/403, or cache errors.
- A local service starts slowly because it downloads models.
- A no-network environment fails when constructing default pipelines.

Actions:

1. Prefer helpers in this skill tree for no-download checks.
2. Replace remote model paths with local paths when the user has pre-downloaded models.
3. Set required tokens or endpoint credentials outside source files.
4. For production services, mount model caches and run a warm-up check before exposing traffic.
5. Route retrieval store construction to `embeddings-search`, deterministic pipeline downloads to `pipelines-and-workflows`, and LLM/RAG backend selection to `agents-and-llm-orchestration`.

## GPU or Heavy Wheel Problems

Symptoms:

- PyTorch installs large CUDA wheels on a CPU-only machine.
- CUDA imports succeed but `torch.cuda.is_available()` is false.
- Optional quantization/ONNX/llama/audio/image packages fail to build.

Actions:

1. Decide whether the user actually needs GPU for the task.
2. For CPU-only inspection or small smoke tests, use CPU wheels and avoid GPU-only extras.
3. For GPU tasks, verify driver, CUDA wheel tag, hardware architecture, and a tiny backend operation before claiming success.
4. Treat long training, benchmarks, full notebook execution, and model downloads as explicit user-approved work.

## Config and Runtime Surface Confusion

- If a user has YAML with `embeddings`, `workflow`, `agent`, `llm`, `rag`, or pipeline sections, route to `api-and-deployment` for service startup and to the owning sub-skill for workflow internals.
- If `Workflow(...)` returns nothing, check whether the generator was consumed; route to `pipelines-and-workflows`.
- If SQL search returns tuple ids/scores instead of dict rows, check whether `content=True` was set before indexing; route to `embeddings-search`.
- If `python -m txtai.console --help` fails, this is expected console path semantics, not argparse help; route to `api-and-deployment`.
- If an agent or RAG flow hallucinates, inspect retrieval quality, template variables, output mode, and backend credentials; route to `agents-and-llm-orchestration`.

## Self-Containment Reminder

Do not solve user tasks by asking them to open the original txtai repository docs, examples, tests, notebooks, or Docker scripts. Use this generated skill tree as the runtime guide and create any project-local files the user needs from the bundled references/scripts.
