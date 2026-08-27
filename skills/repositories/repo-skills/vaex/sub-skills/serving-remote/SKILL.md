---
name: serving-remote
description: "Run and inspect Vaex server, REST and PNG plot endpoints,
  WebSocket remote DataFrame, TestClient, token, base URL, and optional GraphQL
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# serving-remote

Use this sub-skill when a task is about Vaex serving or remote access: `vaex server`, `vaex.server.fastapi.app`, REST or PNG plot endpoints, WebSocket remote DataFrame URLs, TestClient smoke checks, base URLs, token/trusted-token caveats, or optional GraphQL.

## Load these references

- [references/server-workflows.md](references/server-workflows.md) for safe local workflows, `vaex server` invocation, dataset naming, TestClient checks, base URLs, and listener boundaries.
- [references/rest-api.md](references/rest-api.md) for endpoint paths, JSON payload shapes, expected response fields, status signals, headers, and non-Python client patterns.
- [references/graphql-and-remote.md](references/graphql-and-remote.md) for `vaex.open('vaex+ws://...')`, `vaex.server.connect`, remote aggregation semantics, tokens, trusted tokens, and optional GraphQL.
- [references/troubleshooting.md](references/troubleshooting.md) for missing packages, `httpx2`, example-data cache/download surprises, binding, dataset names, URL schemes, tokens, GraphQL dependencies, and cleanup boundaries.
- Run [scripts/server_smoke.py](scripts/server_smoke.py) for a safe installed-package FastAPI/TestClient smoke that does not start a public listener.

## Core operating rules

1. Prefer TestClient or local loopback over public services. Do not require an external Vaex service or external network for verification.
2. Avoid long-running listeners by default. If a listener is required, bind to `127.0.0.1`, choose an explicit port, record the process boundary, and stop it when the check ends.
3. Use `vaex server --help` for live option confirmation. The selected CLI surface is `vaex server [--add-example] [--host HOST] [--base-url BASE_URL] [--port PORT] [--verbose/-v] [--quiet/-q] [--graphql] [filename ...]`.
4. Use `name=path` command arguments for stable dataset IDs; bare paths derive names from file basenames.
5. Treat REST and remote DataFrames as different surfaces. REST uses HTTP JSON/PNG endpoints; Python remote DataFrames use WebSocket URLs such as `vaex+ws://127.0.0.1:8081/dataset` or `vaex+wss://host/dataset`.
6. Remote Vaex aggregations should ship compact scalar or grid results, not whole columns. Avoid unbounded `.evaluate()`, `.to_pandas_df()`, `.values`, or row extraction against remote DataFrames unless explicitly bounded.
7. Treat GraphQL as optional. Check imports and version compatibility before enabling `--graphql` or `/graphql`; GraphQL failures do not block ordinary REST/WebSocket serving.
8. Treat tokens as secrets. Prefer environment variables or Python kwargs over embedding tokens in logs, commands, notebooks, or saved URLs. Use trusted tokens only in private, fully trusted contexts.

## Boundaries

- Route general CLI command discovery, settings, aliases, and non-server command behavior to `../cli-settings/SKILL.md`.
- Route local dataset opening, conversion, HDF5/Arrow/CSV/FITS/cloud IO, and file-format troubleshooting to `../io-conversion/SKILL.md`.
- Route visualization meaning and rendering choices for REST plot outputs to `../visualization-jupyter/SKILL.md`; this sub-skill covers only REST plot endpoint mechanics.
- Route expression syntax, virtual columns, filters, histogram/heatmap aggregation semantics, and value validation to `../expressions-analytics/SKILL.md` when the task is not specifically about the service boundary.
