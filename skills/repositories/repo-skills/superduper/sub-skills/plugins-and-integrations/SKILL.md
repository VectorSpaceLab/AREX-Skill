---
name: plugins-and-integrations
description: "Choose, install, import, and troubleshoot first-party Superduper
  plugins and custom plugin packages."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Plugins and Integrations

Use this sub-skill when a task needs to choose, install, import, or troubleshoot a Superduper plugin before using a data backend, vector search engine, API/LLM provider, ML framework, encoder, or custom package.

This sub-skill is an installation and routing layer. After the right plugin imports successfully, route deeper table/query/model/vector-index/RAG/application work back to the appropriate sibling Superduper skills.

## Evidence and verification status

- The prepared runtime verified the base Superduper package plus `superduper_mongodb` with a local `mongomock://` Datalayer smoke.
- Other first-party plugin entries are distilled from plugin package metadata, exported `__init__.py` APIs, source behavior, READMEs, plugin tests, and plugin CI structure. Treat them as install/import guidance until they are installed and checked in the target environment.
- Do not treat a successful import check as proof that credentials, external services, GPU kernels, model weights, or live API calls are available.

## Read order

1. Read [references/plugin-catalog.md](references/plugin-catalog.md) for plugin package names, import modules, exported names, dependencies, URI routing, and backend boundaries.
2. Read [references/plugin-installation.md](references/plugin-installation.md) to choose the minimum plugin, install it, import it, and use the bundled checker.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for missing modules, package/import spelling mismatches, API keys, service failures, GPU/model-download limits, version skew, and custom `Plugin` component issues.
4. Use [scripts/check_superduper_plugins.py](scripts/check_superduper_plugins.py) for deterministic local import checks. It does not install packages, open network connections, read credentials, or call provider APIs.

## Routing boundaries

Use this sub-skill for:

- Selecting between first-party plugins such as `superduper_mongodb`, `superduper_sql`, `superduper_snowflake`, `superduper_openai`, `superduper_torch`, and vector-search plugins.
- Explaining how Superduper maps data-backend URI schemes to plugin modules.
- Diagnosing `ModuleNotFoundError` and optional dependency failures without installing every plugin.
- Understanding custom `superduper.components.plugin.Plugin` behavior for local `.py` files, package directories, and requirements files.

Do not use this sub-skill to:

- Provision real cloud credentials, Snowflake sessions, Atlas databases, Redis/Qdrant/Chroma services, or live provider API calls.
- Run training, download large model weights, or validate GPU runtime behavior.
- Replace workflow-specific guidance after a plugin is installed. Route those tasks to sibling data, model, vector, listener, or application skills.
