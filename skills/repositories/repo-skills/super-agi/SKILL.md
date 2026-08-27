---
name: super-agi
description: "Routes SuperAGI autonomous-agent framework tasks across
  deployment, FastAPI service, agent workflows, toolkits, model providers,
  resources, and vector-store operations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SuperAGI Repo Skill

Use this skill when a task involves SuperAGI, the open-source autonomous-agent
framework for building, managing, and running tool-using AI agents. It is a
router for future Researcher sessions; read the focused sub-skill before taking
action.

## First Checks

1. If a checkout is available, confirm it is a SuperAGI checkout by looking for
   a top-level `superagi/` package, `main.py`, `config_template.yaml`, and one
   or more `docker-compose*.yaml` files.
2. Read [references/repo-provenance.md](references/repo-provenance.md) before
   deciding whether this skill matches the checkout. If the commit, dirty state,
   or major source layout differs, refresh the repo skill.
3. Read [references/overview.md](references/overview.md) for the architecture
   map, service names, and core terminology.
4. Use [scripts/summarize_superagi_checkout.py](scripts/summarize_superagi_checkout.py)
   when you need a safe static summary of a provided checkout.
5. Use [scripts/check_superagi_config.py](scripts/check_superagi_config.py) to
   validate a `config.yaml`-style file without contacting external providers.

## Route by Task

- **Install, Docker, local runtime, configuration, migrations, GUI, or GPU/local
  LLM deployment:** read
  [sub-skills/deployment-configuration/SKILL.md](sub-skills/deployment-configuration/SKILL.md).
- **FastAPI routes, public API usage, `/v1/agent` API-key endpoints, auth,
  webhooks, migrations, or data model questions:** read
  [sub-skills/api-service/SKILL.md](sub-skills/api-service/SKILL.md).
- **Agent creation, workflow selection, prompt/output parsing, task queues,
  scheduling, wait-for-permission, or Celery execution loops:** read
  [sub-skills/agents-workflows/SKILL.md](sub-skills/agents-workflows/SKILL.md).
- **Built-in tools, custom toolkits, marketplace/external tools, tool config
  keys, secret handling, or tool execution errors:** read
  [sub-skills/toolkits-integrations/SKILL.md](sub-skills/toolkits-integrations/SKILL.md).
- **LLM providers, model API keys, local LLM settings, resource uploads,
  knowledge bases, FILE/S3 storage, vector DBs, or embedding stores:** read
  [sub-skills/models-resources-vector/SKILL.md](sub-skills/models-resources-vector/SKILL.md).

## Minimal Operating Context

SuperAGI is not a small import-only package. Typical local operation uses a
multi-service stack:

- Python FastAPI backend served from `main:app`.
- Celery worker/beat tasks from `superagi.worker`.
- PostgreSQL for application state and Alembic migrations.
- Redis for Celery and task queue state.
- Next.js GUI behind an nginx proxy.
- Optional GPU/local LLM deployment via a separate CUDA Dockerfile/compose path.

The Python source root is `superagi`. The checkout has no standard
`pyproject.toml`, `setup.py`, or `setup.cfg`; prefer Docker or explicit checkout
imports over assuming `pip install superagi` works.

## Minimal Setup and Verification

For a user's own SuperAGI checkout, the public local path is Docker-first:

```bash
cp config_template.yaml config.yaml
# edit config.yaml for DB/Redis/provider/storage settings before startup
docker compose -f docker-compose.yaml config
```

Use `docker compose ... config` as a safe parse/topology check. Start the stack
only when the downstream user authorizes the build, migrations, volumes, and
long-running services. For source-only inspection, check that `python -c "import
superagi"` works from an environment where the checkout root is on `PYTHONPATH`;
do not claim a packaged `pip install superagi` workflow for this snapshot.

## Safe Defaults for Future Agents

- Prefer static inspection, config validation, and helper `--help` checks before
  starting services.
- Do not run full `docker compose up`, `run.sh`, `entrypoint.sh`, marketplace
  downloads, or provider key validation unless the downstream user explicitly
  wants those side effects and has supplied the required services/credentials.
- Treat API keys, OAuth credentials, S3 keys, vector DB credentials, and provider
  tokens as user secrets. Never hard-code values from examples.
- For Docker operation, create `config.yaml` from the checkout's template and
  adjust DB/Redis hosts to match the deployment target before starting services.
- For local Python operation outside Docker, expect extra setup work: Python
  3.10, requirements, PostgreSQL, Redis, NLTK data, and frontend dependencies.

## Verification and Troubleshooting

- For cross-cutting failures, read
  [references/troubleshooting.md](references/troubleshooting.md).
- For service and config failures, read the deployment sub-skill's
  `references/troubleshooting.md`.
- For route/auth/database failures, read the API sub-skill's troubleshooting
  reference.
- For parser/tool/workflow failures, read the agents-workflows and
  toolkits-integrations troubleshooting references.
- For provider/vector/resource failures, read the models-resources-vector
  troubleshooting reference.

## Repository Skill Metadata

Structured router metadata lives in
[references/repo-routing-metadata.json](references/repo-routing-metadata.json).
It is consumed by the managed repo-skill importer when import is approved in a
separate workflow.
