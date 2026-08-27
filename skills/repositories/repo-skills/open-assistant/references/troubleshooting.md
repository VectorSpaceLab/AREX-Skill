# Troubleshooting

Use this root reference when you know the symptom but not the layer. It helps route the problem to the correct Open-Assistant sub-skill without mixing backend, website, and inference failures.

## Symptom to layer map

| Symptom | First layer to inspect | Why |
| --- | --- | --- |
| `ImportError`, missing package, settings load failure, or task endpoint traceback | Backend | Backend and shared Python packages own the FastAPI app, SQLModel settings, and protocol schemas. |
| Wrong task payload, bad request/response JSON, or JSONL export/import issue | Backend | Task lifecycle and OA JSONL tooling live in backend/shared/data. |
| Page loads but task UI, chat UI, login, localization, or Cypress/Jest tests fail | Website | The Next.js app and frontend helpers own these failures. |
| `500`/`401`/`403` from inference server, websocket disconnect, worker timeout, or SSE parse failure | Inference | The server/worker/text-client layer owns those routes and protocols. |
| `_lorem` works but real model configs fail | Inference | That usually means model download, GPU, or worker configuration trouble. |
| Docker compose starts the wrong services or binds the wrong ports | Root stack | The compose profile or environment variable selection is wrong. |

## Safe retry order

1. Re-read the routing table in `SKILL.md` and the relevant sub-skill reference.
2. Run the read-only checker for the suspected layer if a checkout is available.
3. Verify the service boundary before changing code or env files.
4. Only then retry the service or test command.

## Common backend failures

### App or settings import failures

- Check `backend/requirements.txt` against the chosen Python environment.
- Confirm `python -m pip check` is clean in the inspection environment.
- Inspect `backend/oasst_backend/config.py` for required env values such as database, Redis, auth, or rate-limit settings.
- If the failure appears during test startup, confirm `PYTHONPATH=backend` or the equivalent editable install is in effect.

### Task or message lifecycle errors

Common backend error codes include `TASK_NOT_FOUND`, `TASK_NOT_ACK`, `TASK_ALREADY_DONE`, `TASK_ALREADY_UPDATED`, `TASK_MESSAGE_TOO_LONG`, `TASK_MESSAGE_TEXT_EMPTY`, `TASK_MESSAGE_DUPLICATED`, `TASK_MESSAGE_DUPLICATE_REPLY`, `BROKEN_CONVERSATION`, `TREE_IN_ABORTED_STATE`, and `INVALID_CURSOR_VALUE`.

Typical causes:

- The user session does not own the task or has already finished it.
- A message is longer than the configured limit.
- The cursor format does not match the expected ISO timestamp or `uuid$iso_datetime` form.
- A tree is not in the expected state for the requested lifecycle action.

### JSONL problems

- Use `scripts/oasst_jsonl_tool.py inspect` or `tree-to-messages` before any DB import/export work.
- Verify tree/message required fields against [`sub-skills/backend/references/data-formats.md`](../sub-skills/backend/references/data-formats.md) in the backend sub-skill.
- If a file is compressed, confirm the helper accepts the extension and that the file is valid gzip JSONL.
- Do not overwrite existing data files without an explicit `--overwrite` or equivalent acknowledgement.

## Common website failures

- Run `npm ci` in `website/` before `npm run lint`, `npm run typecheck`, or Jest/Cypress checks.
- If a check fails on a missing env var, inspect the NextAuth/Prisma/localization setup in `website/README.md` and the website sub-skill references.
- If a task page is wrong but the API response looks correct, focus on frontend state, component mapping, or localization rather than backend handlers.
- If Cypress contract tests fail, determine whether the API contract changed or the fixture/server state is wrong before editing the UI.

## Common inference failures

- `_lorem` smoke failures usually mean the Python package graph, route wiring, or protocol handling is broken, not that a model download failed.
- Real model configs may require large downloads, GPU memory, or a specific worker backend. Treat them as optional unless the user explicitly needs a real model run.
- Websocket or SSE failures often split into server protocol, worker availability, and frontend rendering. Identify the exact hop before making changes.
- A model config listed by name but missing at runtime may indicate a registry mismatch between `oasst_shared.model_configs` and inference worker code.
- Safety-server or plugin issues should be checked in the inference sub-skill before changing chat-generation logic.

## Docker and environment failures

- If compose complains about missing env vars, inspect the relevant `.env` sample or README for that layer and keep the missing variable scoped to the service that needs it.
- If a profile starts more services than needed, choose the narrowest compose profile that still includes the failing service.
- Do not debug deployment/Ansible or production observability problems through this repo skill; those are outside the generated scope.

## Escalation hints

- If a backend smoke check passes but the website still fails, escalate to the website sub-skill rather than continuing to edit backend code.
- If `_lorem` passes but real inference fails, escalate to the inference sub-skill and gather the exact model name, worker backend, and GPU/runtime error.
- If all read-only checks pass and only a live DB or Docker stack fails, the remaining issue is environmental; collect the exact compose profile and service logs before making code changes.
