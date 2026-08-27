# Yuxi cross-cutting troubleshooting

Use this index before changing code, credentials, or service state. Each row points to the owning sub-skill for deeper guidance.

| Symptom | Likely owner | First safe checks | Do not do |
| --- | --- | --- | --- |
| Web/API not reachable, ports conflict, containers unhealthy, worker not consuming requests | `deployment-and-configuration` | Run the read-only runtime health script; inspect Compose service names, `docker compose ps`, bounded logs, and health endpoints. | Do not run init, pull images, restart services, or edit env files without approval. |
| Login/admin/model provider settings fail | `deployment-and-configuration` | Confirm correct stack mode, env keys, admin/system option location, provider enablement, and masked credentials. | Do not print secrets or run real provider calls unless approved. |
| Agent run hangs, stream is empty, steer does not interrupt, queue status is inconsistent | `agent-runtime` | Check run submission, request queue/steer service, worker logs, SSE serialization, and unit candidates before e2e. | Do not bypass the queue through shell/API hacks. |
| Skill install/load, MCP, subagent task, or sandbox file access fails | `agent-runtime` | Check slug/path rules, personal skill storage, dependency map, MCP endpoint config, sandbox health, and subagent run status. | Do not install remote Skills, call MCP tools, or mutate sandbox files without understanding side effects. |
| Knowledge-base upload/query is empty or wrong | `knowledge-and-ocr` | Check source type, parser result, chunking/index status, vector/reranker config, file-name filters, and KB tool arguments. | Do not rebuild/delete indexes until the failed stage is identified. |
| OCR or document parsing fails | `knowledge-and-ocr` | Identify selected OCR engine, file suffix, parser health/config, local vs service/cloud prerequisites, and sandbox path rules. | Do not treat CPU import as proof that cloud/GPU/service OCR works. |
| CLI cannot find remote, login fails, SSE stream parsing fails, KB CLI command errors | `cli-and-external-integration` | Run the offline CLI script, inspect config/remotes, then opt into a live remote ping only with a URL. | Do not write or upload data to a remote/Langfuse dataset unless explicitly requested. |
| Tests fail or the right check set is unclear | `repo-development` | Use the check-selection reference; start with package/CLI/frontend unit checks, then escalate to service-required checks. | Do not claim integration/e2e coverage if Compose was not running. |
| Docs/changelog/navigation drift | `repo-development` | Check user-visible change policy, VitePress nav, changelog entry, and docs build. | Do not add formal docs without navigation or changelog when required. |

## Backend and credential gates

- **CPU/any:** package imports, many unit tests, CLI help/config/unit tests, parser registry/facade.
- **Service-required:** Docker Compose stack, API/worker/web, Postgres, Redis, MinIO, Milvus, Neo4j, sandbox-provisioner, OCR service profiles.
- **External credentials/network:** model providers, Langfuse, cloud OCR services, remote Yuxi API-key calls.
- **Optional GPU/accelerator:** not required for default Yuxi skill use; only relevant for selected OCR/deployment profiles.

## Staleness response

If the current checkout has changed substantially from `repo-provenance.md`, prefer refresh over patching this skill mentally. High-risk drift areas are agent middleware, tool registry, skill service, subagent service, knowledge parser/OCR registry, CLI command registration, Compose service names, and test layout.
