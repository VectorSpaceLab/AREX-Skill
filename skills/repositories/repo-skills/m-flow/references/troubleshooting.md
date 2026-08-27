# M-flow Troubleshooting

## When to read

Use this reference for cross-cutting M-flow failures before diving into a
workflow-specific sub-skill. For task-specific recovery, also read the nearest
sub-skill troubleshooting file.

## Fast triage

```bash
python -c "import m_flow; print(m_flow.__version__)"
mflow --help
python scripts/check_mflow_env.py --json
```

If the package imports but a workflow fails, identify which layer is failing:
installation/import, credentials, storage service, ingestion pipeline, retrieval
mode, API service, UI/MCP, or destructive operation safeguards.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'm_flow'` | `mflow-ai` is not installed in the active Python | Install `mflow-ai` or use the Python environment where it is installed; rerun the import check. |
| `mflow: command not found` | Console script not on `PATH`, or wrong environment | Run `python -m m_flow --help` or use the environment's script directory; confirm the `mflow` entry point exists. |
| Version prints `*-dev` | Running from an editable/source layout | This is normal for source installs; compare package metadata and provenance when deciding staleness. |
| Optional loader/backend imports are missing | The selected extra was not installed | Install only the needed extra/client and rerun the relevant sub-skill probe. |

## Credentials and provider failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| LLM API key error during `memorize()` or triplet answer generation | `LLM_API_KEY` or provider-specific key is unset/invalid | Set `LLM_API_KEY`, `LLM_PROVIDER`, `LLM_MODEL`, and optional endpoint/version; use `EPISODIC` context retrieval only after data is already memorized. |
| Structured output returns raw text or schema errors | Provider does not honor the selected Instructor mode | Try `LLM_INSTRUCTOR_MODE=markdown_json_mode` or provider-specific JSON/tool mode. |
| `Model not found` or LiteLLM registry errors | Model name is not mapped for the provider | Prefix OpenAI-compatible custom models with `openai/` or verify the provider endpoint/model spelling. |
| Rate limit / timeout errors | Provider quota or network instability | Lower concurrency variables, add provider-side quota, or retry after the provider recovers. |

## Local storage and locks

- Defaults are local file-backed SQLite, LanceDB, and Kuzu. They are convenient
  but can lock if multiple long-running processes mutate the same dataset.
- Use graceful service shutdown. Avoid `kill -9` while a memorization job is
  writing graph/vector data.
- If a query returns no data after `add()`, check whether `memorize()` actually
  completed; raw added data is not queryable until graph/vector memory is built.
- With `ENABLE_BACKEND_ACCESS_CONTROL=true`, per-user/dataset isolation may hide
  data created before access control was enabled. Use the same user context or
  disable isolation only when the user explicitly wants single-user behavior.

## Empty or noisy retrieval

Start with the retrieval sub-skill. Common causes:

- querying before `memorize()` completes;
- querying the wrong dataset or user context;
- choosing `TRIPLET_COMPLETION` when only context retrieval is needed;
- broad queries that match Episode summaries instead of precise FacetPoint or
  Entity anchors;
- external backend config points to an empty or unreachable service.

Use `EPISODIC` for event/context recall, `PROCEDURAL` for how-to memory,
`CHUNKS_LEXICAL` for exact text, `CYPHER` only when raw graph queries are safe,
and `TRIPLET_COMPLETION` when an LLM answer over graph context is required.

## Destructive operations

Never run these without explicit user confirmation and scope:

- `m_flow.delete(...)`, CLI `mflow delete`, hard-delete modes;
- `m_flow.prune.prune_data()` or `m_flow.prune.prune_system(...)`;
- DB/vector timestamp migrations;
- service stop/kill operations;
- Docker volume removal or cache deletion.

Prefer preview/status commands and dry-run guidance before mutation.

## Service and UI issues

- Backend health: check `/health` and `/health/detailed` when running the API.
- Port conflicts: default ports are 8000 (API), 3000 (frontend), 8001 or 8000
  depending on MCP deployment mode, 5001 for face-recognition companion.
- Production auth warnings: set real FastAPI/JWT token secrets outside local/dev.
- Frontend/MCP failures often mean wrong transport/port/API URL rather than a
  core memory bug; use the service-integrations sub-skill.

## Optional hardware and external services

M-flow base package does not require CUDA. Visible GPUs do not imply GPU support
is selected or verified. Optional capabilities need their own evidence:

- browser scraping: browser/runtime packages and possibly browser install;
- face-aware playground: camera access, external face-recognition service, shared key;
- cloud sync: cloud URL/token and reachable remote backend;
- Modal workers: Modal account/token and selected distributed code path;
- external DBs: installed client extra plus a healthy service.

Do not claim an optional backend works until both the Python client and the
service/device are verified.
