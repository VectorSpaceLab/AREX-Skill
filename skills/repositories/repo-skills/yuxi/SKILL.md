---
name: yuxi
description: "Operate and maintain Yuxi, a Docker Compose managed FastAPI,
  LangGraph, Vue, RAG, OCR, knowledge graph, and CLI platform."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Yuxi repo skill

Load this repo skill when the task is about Yuxi / 语析: deploying the stack, debugging agent runtime behavior, working with knowledge bases or OCR, using or extending `yuxi-cli`, or choosing repository development checks.

Yuxi combines a FastAPI backend package, LangGraph agent runtime, Vue/Vite frontend, Docker Compose services, RAG/knowledge-graph/OCR workflows, and a Typer-based CLI. Treat Docker Compose as the canonical live runtime, but use CPU-safe package/CLI/static checks before escalating to service-required or external-credential tests.

## First safety gates

1. **Do not expose secrets.** `.env`, `.env.prod`, provider keys, admin credentials, Langfuse keys, API keys, MinIO data, and local database contents are sensitive.
2. **Classify the backend requirement.** Core package/CLI guidance is CPU/any. Compose integration/e2e checks require live services. Model providers, Langfuse, cloud OCR, and external API calls require explicit credentials/network approval.
3. **Prefer bundled references and scripts.** Generated files are self-contained. If a source repo helper is mutating or credentialed, use the bundled policy reference instead of auto-running it.
4. **Keep import disabled for this production run.** This skill was generated with final managed import intentionally disabled; do not import it into the live repo-skills library unless a later user explicitly asks.

## Route tasks to sub-skills

| Task signal | Use sub-skill | Why |
| --- | --- | --- |
| Start/diagnose the Docker stack, Compose profiles, `.env`, images, ports, logs, production deployment, sandbox-provisioner, OCR services, model-provider config | `sub-skills/deployment-and-configuration/` | Owns service topology, configuration, health probes, and deployment troubleshooting. |
| Agent configs, run submission, request queue, steer, streaming, middleware, attachments, built-in tools, Skills, MCP, subagents, sandbox file semantics, API-key/SSE agent calls, Langfuse runtime hooks | `sub-skills/agent-runtime/` | Owns Yuxi's LangGraph/FastAPI agent execution path and tool surfaces. |
| Knowledge bases, document upload/parse/chunk/index/retrieve, Milvus/vector config, graph/mindmap, evaluation, OCR engines, `read_file` image/OCR fallback | `sub-skills/knowledge-and-ocr/` | Owns RAG, KB, document processing, OCR, and knowledge evaluation behavior. |
| `yuxi` CLI, remote discovery/login/status/logout, temporary browser chat, `agent eval`, `kb upload/list/files/query/open/find`, API-key external calls, SSE client behavior | `sub-skills/cli-and-external-integration/` | Owns CLI and external integration commands, including safe offline smoke checks. |
| Code edits, monorepo boundaries, Docker hot reload, backend/frontend/CLI tests, lint/format, changelog/docs navigation, versioning/release policy | `sub-skills/repo-development/` | Owns maintainer workflow and bounded check selection. |

## Quick operating sequence

1. Read `references/repo-provenance.md` before relying on this skill for a new checkout; compare the checkout branch/commit and package versions to the recorded evidence.
2. Pick the sub-skill from the routing table. If the task spans areas, start with deployment/config for live stack prerequisites, then load the runtime/knowledge/CLI/development sub-skill that owns the behavior.
3. Use the sub-skill's `references/troubleshooting.md` before changing code or configuration.
4. For validation, use the owner sub-skill's native candidate notes and any bundled script. Treat service-required and external-credential candidates as blocked until prerequisites are visibly available.

## Minimal local verification

Use the owning sub-skill before running broad checks, but these smoke paths are safe starting points in a Yuxi checkout:

- Backend package import: `cd backend && uv run --group test pytest test/unit/test_package_import.py`
- CLI help/config: `sub-skills/cli-and-external-integration/scripts/check-cli.sh`
- Running stack health: `sub-skills/deployment-and-configuration/scripts/check-runtime-health.sh --project-dir . --dev`
- Check selection for code changes: `sub-skills/repo-development/scripts/run-selected-checks.sh all-safe`

Do not treat service-required or external-credential workflows as verified unless their prerequisites are visible and the user approved the run.

## Bundled references

- `references/repo-provenance.md` — commit, versions, dirty-state note, and evidence paths used to build the skill.
- `references/repo-routing-metadata.json` — structured router metadata for repo-skills import tooling.
- `references/capability-map.md` — public capability ownership and native verification candidate summary.
- `references/source-script-policy.md` — why repo-owned helpers were copied, adapted, wrapped, or left reference-only.
- `references/troubleshooting.md` — cross-cutting failure-mode index.

## Bundled scripts

Root does not own mutable scripts. Use scripts from the owning sub-skill:

- `sub-skills/deployment-and-configuration/scripts/check-runtime-health.sh` — read-only health/log probe for an already running stack.
- `sub-skills/cli-and-external-integration/scripts/check-cli.sh` — offline CLI help/config smoke check with explicit opt-in remote ping.
- `sub-skills/repo-development/scripts/run-selected-checks.sh` — opt-in command printer/runner for bounded maintainer checks.

## Verification status

This generated skill is an operating-knowledge candidate for Yuxi at the provenance recorded in `references/repo-provenance.md`. A private CPU/any Python inspection environment successfully imported the backend package, CLI package, selected agent/knowledge modules, and `yuxi_cli --help`. Final `verify-repo-skill` usability/native verification and managed import have not been performed by this creation phase.
