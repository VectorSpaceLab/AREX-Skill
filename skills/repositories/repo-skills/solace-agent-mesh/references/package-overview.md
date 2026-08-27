# Package overview

## When to read

Read this for a quick map of Solace Agent Mesh (SAM) concepts before choosing a sub-skill. SAM is an event-driven, multi-agent framework with a CLI-centric project workflow, YAML app configs, gateway components, plugin packages, workflow DAGs, runtime task submission, and evaluation tooling.

## Main operating surfaces

| Surface | What it owns | Route |
| --- | --- | --- |
| `sam init` / project files | New project directories, `.env`, `configs/shared_config.yaml`, orchestrator/web UI/platform service configs, data/logging layout | `sub-skills/project-bootstrap/` |
| `sam add` | Agent, gateway, and proxy config/source scaffolds inside an existing project | `sub-skills/project-bootstrap/` |
| `sam plugin` | Plugin package creation, metadata, component templates, installation, catalog UI, and build artifacts | `sub-skills/plugin-lifecycle/` |
| `sam run` | Starting configured SAM app YAML files and loading project environment | `sub-skills/runtime-operations/` |
| `sam task` | Sending or one-shot-running tasks through a running Web UI gateway | `sub-skills/runtime-operations/` |
| `sam docs` / `sam tools` | Local docs server and built-in tool discovery | `sub-skills/runtime-operations/` |
| `sam-rest-client` | Programmatic REST gateway invocation and `sam-rest-cli` | `sub-skills/runtime-operations/` |
| Workflow app configs | `app_module: solace_agent_mesh.workflow.app`, workflow DAG nodes, map/switch/loop/agent/workflow nodes, template resolution | `sub-skills/workflow-authoring/` |
| `sam eval` | Local/remote evaluation suites, test cases, scoring, results | `sub-skills/evaluation/` |

## Component model

- **Projects** are directory layouts with `requirements.txt`, `.env`, `configs/`, `src/`, and optional data/logging directories.
- **Apps/configs** are YAML files loaded by `sam run`. A project may contain agents, gateways, services, workflows, and shared anchors.
- **Agents** process tasks, own tools, publish agent cards, and may communicate with peers through A2A semantics.
- **Gateways** expose external interfaces such as Web UI, REST/API, or custom event surfaces and translate incoming requests into SAM tasks.
- **Proxies** bridge or expose existing A2A-compatible agents.
- **Workflows** are agent-like apps that orchestrate a DAG of agent/workflow/map/switch/loop nodes.
- **Plugins** package reusable agent/gateway/tool/workflow/custom components that can be installed and added to projects.
- **Evaluation suites** run one or more test cases against local or remote SAM runtimes and score results.

## Runtime prerequisites

Dry validation can often use only Python and the installed package. Live execution may require:

- A Solace broker or broker-compatible configuration.
- LLM provider endpoint/API key/model environment variables.
- A running Web UI or REST gateway for task submission.
- Local databases, object storage, or cloud credentials when configured.
- Browser/port availability for docs, config portal, plugin catalog, or Web UI flows.
- Optional separate environment for `sam-rest-client` when its dependency pins conflict with the main SAM package.

## Safe operating strategy

1. Route to the smallest sub-skill that owns the workflow.
2. Run safe bundled validators before live commands when available.
3. Separate dry file/schema checks from live broker/LLM/gateway execution.
4. Keep install/package issues in the root troubleshooting reference and workflow-specific failures in the nearest sub-skill troubleshooting reference.
5. Refresh this skill if command help, public config fields, or package versions differ from the provenance snapshot.
