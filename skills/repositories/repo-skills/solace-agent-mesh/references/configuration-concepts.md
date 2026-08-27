# Configuration concepts

## When to read

Read this when a task spans multiple sub-skills and you need the shared SAM configuration vocabulary: project layout, YAML app files, `.env` values, model providers, brokers, services, artifacts, sessions, and namespace behavior.

## Project layout

A typical generated SAM project contains:

```text
requirements.txt
.env
configs/
  shared_config.yaml
  logging_config.yaml
  agents/
  gateways/
  services/
  plugins/
src/
data/
```

`sam init` creates the baseline layout. `sam add` and `sam plugin add` add component configs and optional source packages.

## Environment variables

SAM project configs commonly resolve values from `.env` or process environment variables. Treat secret-bearing values as environment data, not skill content.

Common groups:

- Namespace and broker: `NAMESPACE`, `SOLACE_BROKER_URL`, `SOLACE_BROKER_VPN`, `SOLACE_BROKER_USERNAME`, `SOLACE_BROKER_PASSWORD`.
- LLM providers: endpoint, model, model ID, API key, provider-specific credentials.
- Web UI/platform: host, ports, secret key, auth, database URLs.
- Storage: filesystem base path, S3/GCS bucket, endpoint, region, credentials.
- Evaluation remote mode: `EVAL_REMOTE_URL`, `EVAL_NAMESPACE`, optional `EVAL_AUTH_TOKEN`.

When planning a command, explicitly separate placeholders that can remain unresolved during dry validation from values needed for live runtime.

## Shared config anchors

`configs/shared_config.yaml` centralizes cross-app anchors and default services. Generated app configs can reference these anchors instead of repeating model, broker, artifact, or data-tool settings.

Important concepts:

- **Model anchors**: planning/general model blocks selected during init. If no provider is selected, init strips the model anchor references from generated configs.
- **Artifact service**: memory, filesystem, GCS, or S3. Filesystem defaults to a local base path; cloud backends require bucket/endpoint/region/credentials.
- **Session service**: in-memory or SQL-backed persistence depending on generated component. Web UI gateway and orchestrator can use SQLite defaults or provided database URLs.
- **Data tools config**: default settings for built-in data/artifact tools used by agents.
- **Logging config**: packaged logging configuration generated as `configs/logging_config.yaml`.

## App config families

| Family | Typical location | Notes |
| --- | --- | --- |
| Agent configs | `configs/agents/*.yaml` | Own instructions, model selection, tools, card metadata, artifact/session settings, inter-agent communication. |
| Gateway configs | `configs/gateways/*.yaml` | Expose external entry points such as Web UI/REST/custom gateways and often include host/port/auth/database settings. |
| Service configs | `configs/services/*.yaml` | Platform/model-config services and supporting API services. |
| Workflow configs | `configs/agents/*.yaml` or dedicated workflow app YAML | Use `app_module: solace_agent_mesh.workflow.app` and `app_config.workflow`. |
| Plugin-created configs | `configs/agents`, `configs/gateways`, `configs/workflows`, or `configs/plugins` | Written from installed plugin `config.yaml` templates after placeholder substitution. |

## Naming and generated files

The CLI normalizes user-facing component names into variants such as kebab-case paths, snake-case Python modules, and Pascal/Camel display names. When manually editing generated files, keep these aligned:

- Agent names should use letters, numbers, and underscores for agent identity fields.
- Directory/file names usually use kebab or snake forms from the same source name.
- Plugin/component placeholders like `__COMPONENT_KEBAB_CASE_NAME__` are replaced by `sam plugin add`.

## Live service boundary

Dry validation can parse YAML, inspect expected files, and check package imports. Live runtime requires the selected external services:

- Broker connectivity for task exchange.
- LLM provider credentials for model calls.
- Gateway server availability for `sam task` or REST client calls.
- Database/object storage credentials when configured.
- Browser/ports for GUI config portal, plugin catalog, docs, and Web UI.

Use sub-skill validators before live commands, and report explicitly which values remain placeholders.
