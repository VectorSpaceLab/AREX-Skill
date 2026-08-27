---
name: integrations-and-extensibility
description: "Use when selecting or configuring Feast optional stores,
  providers, compute engines, dbt, MLflow, OpenLineage, data quality monitoring,
  or custom provider/store/engine extensions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Feast Integrations and Extensibility

Use this sub-skill for requests like:

- "Which Feast extra do I need for Snowflake and Redis?"
- "Configure Ray/Spark/Snowflake/Flink as a compute engine."
- "Import feature views from dbt."
- "Enable MLflow, OpenLineage, or Great Expectations validation."
- "Design a custom online/offline store, provider, or compute engine."

## Route First

- Feature repository lifecycle, `feast init`, `feature_store.yaml` basics, `feast apply`, and `feast plan`: use `../feature-repos-and-cli/SKILL.md`.
- Concrete historical retrieval, online retrieval, `materialize`, `materialize-incremental`, `push`, or local E2E examples: use `../retrieval-and-materialization/SKILL.md`.
- Feature server, offline server, registry server, remote store clients, TLS/auth/RBAC serving: use `../servers-and-remote/SKILL.md`.
- Vector DB/RAG store selection: use `../rag-and-vector-search/SKILL.md`, then return here for backend extras.
- Contributing a store/engine/provider to Feast itself, tests, lint, docs, or PR mechanics: use `../repo-development/SKILL.md`.

## Core References

- Store, provider, compute engine, and optional extra selection: `references/store-and-provider-matrix.md`.
- Custom extension interfaces and implementation checklists: `references/extensibility.md`.
- dbt, MLflow, OpenLineage, and DQM workflows: `references/integrations.md`.
- Install, import, config, credential, and workflow failure diagnosis: `references/troubleshooting.md`.

## Safe Helper

Run `python scripts/check_optional_extra.py --help` from this sub-skill directory to inspect required imports for selected extras/backends. The script does not install packages or connect to services.
