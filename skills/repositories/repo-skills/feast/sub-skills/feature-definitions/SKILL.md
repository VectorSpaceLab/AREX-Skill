---
name: feature-definitions
description: "Model Feast entities, fields, data sources, feature views,
  on-demand/batch/stream transforms, feature services, labels, permissions
  basics, validation, and versioning without applying a repo."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Feature Definitions

Use this sub-skill when the user asks how to define, migrate, validate, or troubleshoot Feast Python definition objects: `Entity`, `Field`, `FileSource`/request/push sources, `FeatureView`, `OnDemandFeatureView`, `BatchFeatureView`, `StreamFeatureView`, `FeatureService`, label-oriented definitions, and permission metadata basics.

## Route First

- Definition modeling, constructors, schema/types, `ttl`, `online`/`offline`, vector metadata, source wiring, ODFV decorators, feature services, and validation errors: stay here.
- Feature repo layout, `feast apply`, `feast plan`, registry commands, and CLI lifecycle: use `../feature-repos-and-cli/SKILL.md`.
- Historical/online retrieval, materialization, `push`, saved datasets, and point-in-time joins: use `../retrieval-and-materialization/SKILL.md`.
- Vector document retrieval or RAG workflow beyond defining vector `Field`s: use `../rag-and-vector-search/SKILL.md`.
- Feature server, remote registry/store, auth enforcement, TLS, and RBAC runtime behavior: use `../servers-and-remote/SKILL.md`.

## Core References

- API signatures and safe snippets: `references/api-reference.md`.
- Data-modeling patterns for entities, fields, sources, feature views, services, labels, and permission metadata: `references/data-modeling.md`.
- Transformations, ODFVs, batch/stream feature views, validation, and versioning: `references/transformations.md`.
- Diagnostics for imports, schema/type/vector mistakes, source wiring, TTL, and service precompute issues: `references/troubleshooting.md`.

## Safe Definition Validation

Run the bundled validator against a Python definitions file before apply/materialization work:

```bash
python skills/disco/feast/sub-skills/feature-definitions/scripts/validate_feature_definitions.py path/to/features.py
```

Expected output lists discovered Feast object types/names and reports local validation warnings/errors. The script imports the installed `feast` package if available, never calls `FeatureStore.apply`, `plan`, `materialize`, `push`, retrieval APIs, or any server command, and does not require a Feast source checkout.
