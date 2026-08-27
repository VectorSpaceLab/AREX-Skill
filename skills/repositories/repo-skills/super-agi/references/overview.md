# SuperAGI Overview

## When to Read

Read this for a quick mental model of SuperAGI before choosing a sub-skill. It
summarizes the repository evidence used by this skill and the relationships
between services, packages, and user-facing workflows.

## What SuperAGI Provides

SuperAGI is a developer-first autonomous-agent application. It combines:

- agent definitions, execution records, workflow templates, task queues, and
  permission checkpoints;
- model-provider wrappers for OpenAI, Google Palm, Replicate, Hugging Face, and
  local LLM endpoints;
- built-in and downloadable toolkits for file, web/search, email, GitHub, Jira,
  Slack, calendar, social, coding, thinking, knowledge search, resources, and
  image generation tasks;
- FastAPI controllers for GUI and API-key clients;
- PostgreSQL, Redis, Celery worker/beat jobs, a Next.js GUI, and nginx proxying;
- resource and knowledge ingestion with optional vector DB backends.

## Main Runtime Pieces

| Piece | Responsibility | Evidence |
|---|---|---|
| `main:app` FastAPI app | Registers controller routers, auth, login, provider-key validation, and startup seed tasks. | `main.py`, `superagi/controllers/**` |
| PostgreSQL | Stores users, organizations, agents, executions, configs, tools, vector DBs, resources, templates, webhooks, and workflow steps. | `superagi/models/**`, `migrations/**` |
| Redis | Backs Celery broker/result state and `TaskQueue` list/status storage. | `superagi/worker.py`, `superagi/agent/task_queue.py` |
| Celery worker/beat | Runs agent execution, scheduled agents, waiting workflows, resource summarization, and webhook callbacks. | `superagi/worker.py`, `superagi/jobs/**` |
| Next.js GUI | Dashboard, agents, marketplace, knowledge, models, toolkits, settings, and APM pages. | `gui/package.json`, `gui/pages/**` |
| nginx proxy | Exposes the composed UI/API stack through the public web port. | `nginx/default.conf`, compose files |
| Optional local LLM/GPU stack | Uses a CUDA Dockerfile and a text-generation-webui service target for local model serving. | `Dockerfile-gpu`, `docker-compose-gpu.yml`, `config_template.yaml` |

## Source Areas and Skill Ownership

- Deployment and service startup live in `deployment-configuration`.
- HTTP routes, auth, API keys, webhooks, schemas, and migrations live in
  `api-service`.
- Agent workflow execution, prompts, output parsing, scheduling, and task queues
  live in `agents-workflows`.
- Tool/toolkit contracts, built-ins, custom tools, marketplace downloads, and
  tool execution live in `toolkits-integrations`.
- Model providers, resources, knowledge, vector DBs, embeddings, and storage
  live in `models-resources-vector`.

## Important Constraints

- There is no standard Python package metadata in the inspected checkout. Treat
  `superagi` as a source package in a checkout rather than assuming a published
  installable distribution.
- Many operations are side-effectful: downloading marketplace tools, installing
  apt/pip requirements, running migrations, starting Docker services, validating
  provider keys, and connecting to vector DBs.
- `config.yaml` values are merged with environment variables; environment
  variables can override template-file settings.
- Credential placeholders in the template are not usable secrets. Provider,
  OAuth, S3, email, social, Jira, Slack, search, and vector DB integrations need
  real user-provided credentials.
- Optional GPU/local LLM support is a deployment branch, not a default
  requirement for ordinary source inspection.

## Safe Inspection Helpers

- Root `scripts/summarize_superagi_checkout.py` gives a static repo summary.
- Root `scripts/check_superagi_config.py` validates config shape and placeholder
  values without contacting services.
- `api-service/scripts/inspect_superagi_routes.py` extracts FastAPI route
  decorators without importing `main.py`.
- `toolkits-integrations/scripts/inspect_builtin_toolkits.py` summarizes tool
  classes statically and avoids marketplace downloads.
