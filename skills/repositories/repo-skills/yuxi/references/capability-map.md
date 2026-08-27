# Yuxi capability map

Use this map to route work and choose verification depth without re-reading all sub-skills.

## Capability ownership

| Capability | Owner | Primary references | Verification style |
| --- | --- | --- | --- |
| Docker Compose dev/Lite/prod startup, service topology, ports, logs, health, sandbox-provisioner, OCR service profiles | `deployment-and-configuration` | `runtime-topology.md`, `configuration-and-secrets.md`, `troubleshooting.md` | Read-only health script; service-required native checks only when stack is running. |
| `.env`, `.env.prod`, model-provider/system options, API keys, CORS/proxy, MinIO public assets, registry image pulls | `deployment-and-configuration` | `configuration-and-secrets.md` | Config review plus optional model-provider connectivity when credentials are available. |
| Agent context/config, run submission, request queue, steer, worker/SSE streaming, summary/offload, attachments | `agent-runtime` | `agent-runtime-map.md` | CPU-safe unit candidates first; e2e streaming only with live services. |
| Built-in tools, `install_skill`, personal Skills, MCP, subagents, sandbox path semantics | `agent-runtime` | `tools-skills-mcp-subagents.md`, `troubleshooting.md` | Skill router/service, sandbox, MCP/subagent unit/e2e candidates. |
| Knowledge-base creation, data sources, upload/import, parse/chunk/index/retrieve, graph, mindmap, evaluation | `knowledge-and-ocr` | `knowledge-workflows.md` | Parser facade/unit checks plus service-required KB/OCR/eval checks. |
| OCR engine selection, health/config center, RapidOCR, MinerU, PP-Structure, DeepSeek OCR, PaddleOCR APIs, read_file OCR fallback | `knowledge-and-ocr` | `ocr-engine-matrix.md`, `troubleshooting.md` | Local RapidOCR CPU checks; service/cloud engines only with configured services/credentials. |
| CLI remotes/login/status/logout/chat/agent/kb/eval, external API-key/SSE clients | `cli-and-external-integration` | `cli-command-map.md`, `external-api-and-eval.md` | Offline `check-cli.sh` and CLI unit tests; live remote/Langfuse only with explicit opt-in. |
| Code edits, monorepo layout, test/lint selection, docs/changelog, version/release policy | `repo-development` | `development-workflows.md`, `testing-and-release.md` | `run-selected-checks.sh` chooses bounded safe/service-required checks. |

## Backend criticality summary

- **Required CPU/any:** backend package import, agent context/tool/skill/sandbox modules, knowledge parser registry/facade, CLI import/help/config behavior.
- **Optional service-required:** Docker Compose runtime health, API integration, backend e2e, subagent stream e2e, personal skill agent e2e, OCR config center e2e, multimodal read_file e2e.
- **Optional external credentials/network:** real model-provider connectivity, Langfuse datasets/eval, external API-key calls, remote `yuxi-cli` operations, non-local OCR engines.
- **Optional GPU/accelerator:** not required for core skill extraction. Treat OCR/GPU acceleration as an alternative deployment profile, not as verified by CPU imports.

## Native candidate summary

| Candidate id | Owner | Requirement | Notes |
| --- | --- | --- | --- |
| `backend-package-import` | `repo-development` | CPU/any, required | Fast backend package import smoke. |
| `backend-skill-router-unit` | `agent-runtime` | CPU/any, required | Skill router contracts. |
| `backend-skill-service-unit` | `agent-runtime` | CPU/any, required | Personal skill storage/install/load behavior. |
| `backend-sandbox-unit` | `agent-runtime` | CPU/any, required | Sandbox path/backend semantics. |
| `agent-request-queue-units` | `agent-runtime` | CPU/any, required | Queue and steer behavior. |
| `knowledge-parser-facade` | `knowledge-and-ocr` | CPU/any, required | Parser/OCR registry and safe engine selection. |
| `cli-unit-suite` | `cli-and-external-integration` | CPU/any, required | CLI command/config/client/KB/eval unit behavior. |
| `frontend-unit-suite` | `repo-development` | Node/pnpm, optional | Vue store/API/UI behavior. |
| `docker-dev-runtime` | `deployment-and-configuration` | Docker services, optional | Running development stack health. |
| `docker-prod-runtime` | `deployment-and-configuration` | Docker/prod secrets, optional | Production topology reference check; usually not run in verification. |
| `subagent-stream-e2e` | `agent-runtime` | Docker services, optional | Streaming subagent behavior. |
| `personal-skill-agent-e2e` | `agent-runtime` | Docker services + sandbox, optional | Personal skill runtime behavior. |
| `ocr-config-center-e2e` | `knowledge-and-ocr` | Docker services, optional | OCR config and temporary attachment parsing. |
| `read-file-multimodal-e2e` | `knowledge-and-ocr` | Services + model/OCR, optional | Image/read_file/OCR fallback behavior. |
| `model-provider-connectivity` | `deployment-and-configuration` | Credentials/network, optional | Real provider connectivity only when enabled. |
| `langfuse-agent-eval` | `cli-and-external-integration` | Langfuse credentials/network, optional | Dataset/eval side effects require explicit approval. |

For full construction-only details, see the review artifacts under `skills/tests/yuxi/reports/integration/` in the generating checkout.
