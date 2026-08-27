---
name: superduper
description: "Use Superduper to build database-integrated AI applications,
  component workflows, listeners, vector indexes, and first-party plugin
  integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Superduper

Use this repo skill when a task names Superduper, `superduper-framework`, or APIs such as `superduper(...)`, `Datalayer`, `ObjectModel`, `Listener`, `VectorIndex`, first-party `superduper_*` plugins, database-integrated AI apps, RAG-style component graphs, or vector search over backend records.

## Before using this skill

- Install the base package with Python 3.10+:

  ```bash
  python -m pip install superduper-framework
  ```

- Install at least one data-backend plugin for real `Datalayer` work. For a no-service local smoke, install the MongoDB plugin and use `mongomock://...`:

  ```bash
  python -m pip install superduper_mongodb
  python - <<'PY'
  from superduper import superduper
  db = superduper("mongomock://skill-smoke", initialize_cluster=False, force_apply=True)
  print(type(db).__name__)
  PY
  ```

- Do not rely on the `superduper` console command for this source snapshot. The package metadata declares a console script, but this version lacks `superduper.__main__`; use the Python API and bundled helper scripts instead.

## Route by task

| Task or signal | Read |
| --- | --- |
| Connection strings, config files, `SUPERDUPER_*` env vars, backend URI mapping, `Datalayer`, `Document`, `Schema`, `Table`, query operations, or safe scratch DB checks | [datalayer-and-config](sub-skills/datalayer-and-config/SKILL.md) |
| `Component`, `ObjectModel`, custom callable models, `Listener`, `Dataset`, `Metric`, `Validation`, `Trainer`, `Application`, cron/Streamlit components, or RAG-like workflow composition | [components-and-workflows](sub-skills/components-and-workflows/SKILL.md) |
| Embedding listeners, `VectorIndex`, vector datatypes, `table.like(..., vector_index=...)`, compatible query listeners, local vector search, nearest-neighbor troubleshooting | [vector-search-and-retrieval](sub-skills/vector-search-and-retrieval/SKILL.md) |
| Choosing/installing/importing `superduper_*` plugins for MongoDB, SQL, Snowflake, Redis, vector DBs, OpenAI/Anthropic/Cohere/Jina, Pillow, sklearn, Torch, Transformers, vLLM, or custom plugins | [plugins-and-integrations](sub-skills/plugins-and-integrations/SKILL.md) |

## Shared references and scripts

- Read [references/api-overview.md](references/api-overview.md) for the public import surface, verified signatures, backend URI map, and where each API family is covered.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import/plugin/backend/CLI/config failures.
- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a checkout or package version.
- Run [scripts/check_superduper_env.py](scripts/check_superduper_env.py) for a safe import/version/plugin/CLI diagnostic that does not open network connections or install packages.

## Operating rules

1. Prefer Python API snippets over CLI commands for this repo snapshot.
2. Choose the minimum plugin for the user's backend or model provider; do not install every plugin unless the user explicitly asks for broad optional coverage.
3. Treat cloud/API/vector DB/LLM/GPU plugin paths as optional until credentials, services, model weights, and hardware are explicitly available.
4. Use scratch `mongomock://...` or other user-approved test URIs for destructive checks. Never call `db.drop(force=True, data=True)` against user or production data.
5. If a task combines routes, start with setup (`datalayer-and-config`), then component/model wiring (`components-and-workflows`), then retrieval (`vector-search-and-retrieval`), and finally provider/backend-specific plugin details (`plugins-and-integrations`).
