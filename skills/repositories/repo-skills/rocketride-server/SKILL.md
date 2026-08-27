---
name: rocketride-server
description: "Operate RocketRide Server workflows across pipeline authoring, SDK
  clients, node catalog, runtime deployment, IDE apps, MCP/n8n integrations, and
  contributor docs/build tasks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# RocketRide Server

Use this repo skill when a task involves RocketRide Server, RocketRide `.pipe`
files, RocketRide SDKs/CLI, pipeline nodes, the native engine/runtime, the VS
Code extension, MCP, n8n, or repository contributor workflows.

RocketRide is an AI pipeline platform: users author portable JSON pipelines,
run them on a local/self-hosted/Cloud engine, and integrate them through Python,
TypeScript, MCP, IDE, or n8n surfaces.

## Start here

1. Identify the requested surface: pipeline JSON, SDK/CLI, node catalog,
   runtime/deployment, IDE/app, MCP/n8n, or contributor build/docs.
2. Read [repo overview](references/repo-overview.md) if you need the monorepo
   map, package/version baseline, or common route combinations.
3. Read [cross-cutting troubleshooting](references/troubleshooting.md) if the
   symptom spans endpoint/auth/token/runtime/dependency boundaries.
4. Use the focused sub-skill below. Keep task-specific details in the nearest
   sub-skill reference instead of expanding the root router.
5. Before executing anything side-effecting, distinguish safe static/import
   checks from engine starts, provider calls, Docker/Helm, VS Code launches,
   n8n workflows, model downloads, or billed external services.

## Route map

| Task intent | Read |
|---|---|
| Create, validate, repair, or adapt a `.pipe` workflow; reason about components, providers, lane wiring, `input`, `control`, RAG/document/agent recipes, or env placeholders. | [Pipeline authoring](sub-skills/pipeline-authoring/SKILL.md) |
| Use Python/TypeScript SDKs or the `rocketride` CLI; connect, authenticate, start a pipeline, send/upload/stream data, monitor events, use file store/log/deploy/database APIs, or troubleshoot tokens. | [SDK clients](sub-skills/sdk-clients/SKILL.md) |
| Understand or modify node provider definitions, `service*.json`, class types, lanes, generated node docs, per-node requirements, or node contract tests. | [Nodes catalog](sub-skills/nodes-catalog/SKILL.md) |
| Start or deploy the native engine; debug `/ping`, WebSocket `/task/service`, port `5565`, Docker Compose, Helm, source builds, observability, or runtime credentials. | [Runtime deployment](sub-skills/runtime-deployment/SKILL.md) |
| Work on the VS Code extension, visual `.pipe`/`.rrapp` editors, connection settings, App Builder, Module Federation shell, or UI app descriptors. | [IDE and apps](sub-skills/ide-and-apps/SKILL.md) |
| Expose pipelines to assistants through MCP, configure `rocketride-mcp`, use MCP resources/tools, integrate with n8n action/trigger nodes, or debug webhook round trips. | [MCP and integrations](sub-skills/mcp-and-integrations/SKILL.md) |
| Choose repo builder tasks, update co-located docs after public-contract changes, regenerate generated references, run focused tests/lint, or diagnose CI/build setup. | [Development, build, and docs](sub-skills/development-build-docs/SKILL.md) |

## Public installs

Use the package that matches the task surface:

```bash
pip install rocketride
pip install rocketride-mcp
npm install rocketride
```

For a repo checkout development task, use that checkout's documented pnpm and
`./builder` workflow instead of installing every optional node dependency.

## Quick facts

- Pipeline components have `id`, `provider`, `config`, optional `input` data-lane
  edges, and optional `control` invoke edges.
- SDK/CLI data operations target a running pipeline task token returned by
  `use()` or `rocketride start`.
- Local engines normally listen on port `5565`; SDKs speak a WebSocket/DAP-style
  protocol at `/task/service`.
- Cloud endpoints must use secure `https://` or `wss://` schemes.
- `ROCKETRIDE_APIKEY` is the main SDK/CLI auth variable; MCP can also use
  `ROCKETRIDE_AUTH`.
- Node docs are co-located with node source, but generated parameter blocks come
  from `services*.json` and should not be hand-edited.
- Many provider nodes and integrations require optional packages, credentials,
  external services, databases, or model runtimes; do not claim they are
  available from a base import check.

## Safe checks

Use bundled checks before runtime execution:

```bash
python scripts/rocketride_static_probe.py --skill-root .
python scripts/rocketride_static_probe.py --pipe ./candidate.pipe
python scripts/rocketride_static_probe.py --service-json ./candidate-service.json
```

For Python SDK import/API smoke, use the SDK sub-skill helper from its own
folder:

```bash
python sub-skills/sdk-clients/scripts/sdk_import_smoke.py --json
```

For MCP config-only checks, use the integration sub-skill helper:

```bash
python sub-skills/mcp-and-integrations/scripts/mcp_config_smoke.py --help
```

These checks do not start an engine, connect to Cloud, call providers, launch
VS Code, start Docker/Helm/n8n, or download models.

## References

- [Repo overview](references/repo-overview.md)
- [Cross-cutting troubleshooting](references/troubleshooting.md)
- [Repo provenance](references/repo-provenance.md)
- [Router metadata](references/repo-routing-metadata.json)

## Boundaries

This skill is operational guidance, not a live engine. If a task needs real
pipeline execution, verify endpoint, credentials, services, data, and side-effect
approval first. If a task only asks for generic LLM, vector database, MCP, n8n,
VS Code, Docker, or Kubernetes help with no RocketRide-specific signal, use a
more specific skill instead of this repo skill.
