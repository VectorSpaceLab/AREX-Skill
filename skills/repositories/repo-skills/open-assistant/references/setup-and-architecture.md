# Setup and architecture

Use this root reference when you need to choose an Open-Assistant subsystem, select a local stack, or understand why a symptom belongs to backend, website, or inference.

## Repository shape covered by this skill

| Area | Main paths | Responsibility | Route |
| --- | --- | --- | --- |
| Backend API | `backend/`, `oasst-shared/`, `scripts/backend-development/` | FastAPI data-collection API, task/message/user endpoints, SQLModel settings, Redis rate limits, Celery worker, shared protocol schemas, async Python API client. | `sub-skills/backend/` |
| OA data utilities | `oasst-data/`, backend `export.py` and `import.py` | Exported message tree/message JSONL schemas, traversal, flattening, filtering, and import/export preparation. | `sub-skills/backend/` |
| Website | `website/`, `scripts/frontend-development/` | Next.js app, Chakra UI, contribution task pages, chat UI, frontend API client, Prisma/NextAuth support DB, Jest/Cypress/Storybook/localization checks. | `sub-skills/website/` |
| Inference | `inference/server/`, `inference/worker/`, `inference/text-client/`, `inference/safety/` | FastAPI inference server, websocket workers, model config registry, SSE chat API, text client, safety server, load tests. | `sub-skills/inference/` |
| Shared infrastructure | `docker-compose.yaml`, `redis.conf`, `docker/` | Local databases, Redis, backend/frontend/inference profiles, observability services. | Start here, then route by failing service. |

## Fast orientation checklist

From a user's checkout:

```bash
python scripts/check_open_assistant_stack.py --repo-root <repo-root>
```

Then inspect the layer-specific files before changing code:

- Backend: `backend/main.py`, `backend/oasst_backend/api/v1/api.py`, route module named by the failing endpoint, `backend/oasst_backend/config.py`, and `backend/oasst_backend/tree_manager.py` for task selection behavior.
- Shared Python: `oasst-shared/oasst_shared/schemas/protocol.py`, `oasst-shared/oasst_shared/schemas/inference.py`, `oasst-shared/oasst_shared/api_client.py`, and `oasst-shared/oasst_shared/model_configs.py`.
- Data: `oasst-data/oasst_data/schemas.py`, `reader.py`, `writer.py`, and `traversal.py`.
- Website: `website/package.json`, `website/src/lib/oasst_api_client.ts`, `website/src/components/Tasks/TaskTypes.tsx`, task components under `website/src/components/Tasks/`, and chat components under `website/src/components/Chat/`.
- Inference: `inference/server/main.py`, route modules under `inference/server/oasst_inference_server/routes/`, support modules such as `chat_repository.py` and `worker_utils.py`, `inference/worker/__main__.py`, `inference/worker/work.py`, `inference/worker/chat_chain.py`, and `inference/text-client/`.

## Local stack profiles

`docker-compose.yaml` uses profiles. Pick the smallest profile that matches the task and avoid unrelated services.

| Profile | Typical command shape | Starts | Use when |
| --- | --- | --- | --- |
| `backend-dev` | `docker compose --profile backend-dev up --build --attach-dependencies` | Backend Postgres, Redis, backend API, Celery/backend workers, Adminer/RedisInsight helpers. | Working on backend API, DB migrations, task lifecycle, backend import/export, or API-client integration. |
| `frontend-dev` | `docker compose --profile frontend-dev up --build --attach-dependencies` | Backend support services plus website support DB, MailDev, website-facing backend pieces. | Running the website against local backend/auth/mail/database dependencies. |
| `ci` | `docker compose --profile ci up --build --attach-dependencies` | CI-oriented backend/frontend services and web app image. | Reproducing Cypress or full-stack CI failures. |
| `inference` | `docker compose --profile inference up --build --attach-dependencies` | Inference Postgres/Redis/server/worker. | Testing inference server-worker protocol or chat generation. This may pull models or use GPUs depending on worker config. |
| `inference-dev` | Used by compose services as support profile | Backend and website support DBs for inference development. | Only when a documented inference development workflow asks for it. |
| `inference-safety` | `docker compose --profile inference-safety up --build --attach-dependencies` | Safety server. | Testing safety endpoints/guardrails. |
| `observability` | `docker compose --profile observability up --build --attach-dependencies` | Prometheus, Grafana, Netdata. | Observability-only work after primary services are healthy. |

Prefer dry checks first. Starting profiles can create containers, bind local ports, initialize databases, and pull images.

## Python environment notes

The verified construction environment used Python 3.10 and pip 24.0. For a fresh local environment:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install 'pip<24.1'
python -m pip install -r backend/requirements.txt
python -m pip install -e 'oasst-shared[dev]' -e 'oasst-data[dev]'
```

The `pip<24.1` constraint is important for this historical checkout because `Celery==5.2.0` metadata can be rejected by newer pip releases.

Add inference server support only when needed:

```bash
python -m pip install -r inference/server/requirements.txt
```

Do not install `inference/worker/requirements.txt` casually: it includes model-serving dependencies and a source `transformers` install that can be slower or more fragile. Use the inference sub-skill to decide whether `_lorem`, `distilgpt2`, or a real OpenAssistant model worker is appropriate.

## Website environment notes

Website work happens under `website/`:

```bash
cd website
npm ci
npm run lint
npm run typecheck
npm run jest -- --runInBand
```

The packaged helper wraps common checks:

```bash
bash scripts/run_frontend_checks.sh --repo-root <repo-root> lint typecheck jest
```

Some checks require service dependencies:

- Cypress contract/e2e checks expect backend/frontend support services and seeded/auth state described by the website and Cypress docs.
- NextAuth and Prisma flows need the web database and relevant env vars.
- Localization checks depend on translation files under `website/public/locales` or the configured inlang project.

## Service boundaries and handoffs

- A browser page renders the wrong task type or submits the wrong payload: start in website; compare emitted request against backend protocol if the route rejects it.
- Backend returns a task lifecycle error (`TASK_NOT_ACK`, `TASK_ALREADY_DONE`, `TASK_MESSAGE_TOO_LONG`, etc.): start in backend; inspect user/session/task state before changing website code.
- Chat UI opens but streamed generation fails: split the issue into website SSE rendering, inference `/chats` SSE behavior, worker websocket availability, and model backend readiness.
- `_lorem` works but a real model fails: inference model config/download/GPU issue, not backend or website.
- JSONL file fails before DB import: backend data-format issue. DB import failure after schema-valid JSONL may be DB state, migrations, or backend import script behavior.

## Excluded heavy areas

This skill does not provide operating instructions for `model/` training/evaluation/pretokenizer workflows, RLHF experiments, DeepSpeed/FlashAttention setup, large dataset acquisition, Ansible/deployment, or infrastructure production operations. If the user asks for those, state that this skill covers only backend/website/inference/data and recommend creating or extending a model/deployment skill.
