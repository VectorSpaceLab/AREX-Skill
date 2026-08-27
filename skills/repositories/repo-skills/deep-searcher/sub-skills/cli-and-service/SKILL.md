---
name: cli-and-service
description: "Use DeepSearcher through the console command or bundled FastAPI
  service helper, including flags, endpoints, startup checks, and deployment
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# CLI and Service

Use this sub-skill when the task is about the `deepsearcher` console command, command-line help, the HTTP service surface, or deployment-oriented checks. It covers the public command parser and a source-free FastAPI helper that mirrors the important endpoint shapes without depending on the original checkout's `main.py`.

## Route here for

- `deepsearcher query ...` and `deepsearcher load ...` flag usage.
- Deprecated `--query` / `--load` behavior.
- CLI help failures caused by early provider initialization.
- A bundled HTTP service helper that exposes `/set-provider-config/`, `/load-files/`, `/load-website/`, and `/query/`.
- Service startup checks, route checks, and lightweight deployment validation.

## Route elsewhere

- Provider selection, credentials, and optional packages: `provider-configuration`.
- Data loading, crawling, chunking, and collection creation: `data-ingestion`.
- Query/retrieve internals and RAG agent behavior: `rag-query`.
- Retrieval benchmarks and 2WikiMultiHopQA evaluation: `evaluation`.

## Reference map

- [CLI reference](references/cli-reference.md): exact command names, positional arguments, and flags.
- [Service reference](references/service-reference.md): endpoint payloads, response shapes, and startup options.
- [Troubleshooting](references/troubleshooting.md): help-time configuration failures, missing credentials, Milvus Lite locks, and source-free deployment checks.

## Safe bundled helpers

- [scripts/check_cli_help.py](scripts/check_cli_help.py): run CLI help in a temp working directory with optional dummy env injection and classify common initialization failures.
- [scripts/serve_deepsearcher_api.py](scripts/serve_deepsearcher_api.py): run a source-free FastAPI helper that uses installed DeepSearcher APIs and mirrors the service surface.
- [scripts/check_service_routes.py](scripts/check_service_routes.py): verify the bundled service helper exposes the expected routes.

## Operating rules

1. Do not tell future agents to run the original repository's `main.py`; use the bundled service helper instead.
2. Treat CLI help as potentially stateful. The inspected checkout initializes configuration before argparse finishes, so `--help` can fail if the default provider stack is not ready.
3. Use a temp working directory for help probes so the local Milvus default does not reuse an existing `./milvus.db` lock.
4. Keep provider setup, ingestion, query, and evaluation routed to the sibling sub-skills when the task is not specifically about the console command or HTTP endpoints.

## Minimal examples

```bash
python scripts/check_cli_help.py --command all
python scripts/check_service_routes.py --json
python scripts/serve_deepsearcher_api.py --host 127.0.0.1 --port 8000 --enable-cors
```
