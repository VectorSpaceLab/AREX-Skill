---
name: feast
description: "Use for Feast feature store tasks: feature repositories,
  definitions, CLI, retrieval, materialization, serving, RAG/vector search,
  integrations, and Feast contributor workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Feast

Use this skill when the user asks to work with Feast as a feature store or to contribute to the Feast codebase. Feast manages feature definitions, registry state, offline training retrieval, online serving, materialization, feature servers, vector/RAG retrieval, and optional data infrastructure integrations.

## Start Here

1. If the user is operating a Feast project, identify the feature repository root and `feature_store.yaml` first.
2. If the user is defining objects, inspect or create Python definitions before running `feast apply`.
3. If the user is retrieving features, confirm the definitions were applied and the online store was materialized or pushed.
4. If the user is using remote services, auth, cloud stores, vector DBs, or clusters, confirm the required Feast extra, service, credentials, and safe validation path before running commands.
5. If the user is changing Feast source code, use targeted tests and lint/type checks before broad suites.

## Install And Smoke Check

Public install patterns:

```bash
pip install feast
pip install "feast[redis]"        # example optional backend extra
pip install "feast[snowflake]"    # example offline store extra
```

Minimal import and CLI checks:

```bash
python - <<'PY'
import feast
from feast import FeatureStore, Entity, FeatureView, Field
print("Feast import OK", getattr(feast, "__version__", "unknown"))
PY
feast --help
feast version
```

Run `scripts/check_feast_environment.py --help` when you need a bundled diagnostic for installed Feast, CLI availability, and optional extras.

## Route By Task

| User request | Use this sub-skill |
| --- | --- |
| Create a feature repo, inspect `feature_store.yaml`, choose CLI commands, run `init`, `apply`, `plan`, list objects, or handle registry paths | `sub-skills/feature-repos-and-cli/SKILL.md` |
| Define `Entity`, `Field`, data sources, `FeatureView`, `OnDemandFeatureView`, stream/batch feature views, feature services, labels, or permission metadata | `sub-skills/feature-definitions/SKILL.md` |
| Retrieve historical or online features, materialize, push rows, build training datasets, diagnose null/stale online values, or handle saved datasets | `sub-skills/retrieval-and-materialization/SKILL.md` |
| Run or debug feature server, offline server, registry server, transformation server, MCP, TLS, auth/RBAC, remote stores, or production serving topology | `sub-skills/servers-and-remote/SKILL.md` |
| Build RAG or vector-search workflows with vector fields, vector online stores, document embeddings, chunking, or `retrieve_online_documents` | `sub-skills/rag-and-vector-search/SKILL.md` |
| Select optional extras, configure stores/providers/compute engines, use dbt/MLflow/OpenLineage/DQM, or design custom store/provider extensions | `sub-skills/integrations-and-extensibility/SKILL.md` |
| Modify Feast source, choose focused tests, run Ruff/MyPy/Pytest, update docs/protos, work on Go/Java/operator code, or prepare a PR | `sub-skills/repo-development/SKILL.md` |

## Common Decision Points

- **Local quickstart:** prefer local provider, file offline store, SQLite online store, and the `feature-repos-and-cli` plus `retrieval-and-materialization` routes.
- **Definition errors:** stay in `feature-definitions` until constructors, schemas, sources, and feature services are valid; then route to `feature-repos-and-cli` for `apply`.
- **Online nulls:** check materialization/push windows, entity join keys, feature refs, and registry state in `retrieval-and-materialization` before blaming serving.
- **Remote/service errors:** use `servers-and-remote` for endpoint/auth/TLS behavior and `integrations-and-extensibility` for missing extras or backend selectors.
- **Vector/RAG:** define vector `Field` metadata in `feature-definitions`, then use `rag-and-vector-search` for vector store config and document retrieval.
- **Contributing:** use `repo-development`; do not run broad integration suites or service-backed examples unless prerequisites and safety are clear.

## Bundled References And Scripts

- Read `references/repo-provenance.md` before deciding whether this skill matches a current Feast checkout or should be refreshed.
- Read `references/troubleshooting.md` for cross-cutting install/import, CLI discovery, optional dependency, and routing failures.
- Run `scripts/check_feast_environment.py` for a safe import/CLI/extra diagnostic that does not contact external services.

## Safety Rules

- Do not run `feast teardown`, cloud-backed materialization, Kubernetes/operator examples, release scripts, or service-backed integration tests without explicit confirmation and prerequisites.
- Do not assume optional extras are installed. Check imports and route backend selection to `integrations-and-extensibility`.
- Keep generated project examples local and tiny unless the user explicitly asks for production/cloud/service deployment.
- For source changes, start with the smallest relevant lint/type/test commands, then broaden only if needed.
