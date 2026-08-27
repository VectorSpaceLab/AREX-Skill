---
name: index-and-vespa
description: "Marqo index settings, index model validation,
  structured/semi-structured/legacy-unstructured Vespa schema/query generation,
  index management, and local Vespa app/custom searcher guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
  repo: marqo
  sub-skill-id: index-and-vespa
license: Apache 2.0
---

# index-and-vespa

Use this sub-skill when the task is about Marqo index settings, core index/schema models, field type or feature validation, structured versus semi-structured versus legacy-unstructured internals, Vespa schema/query conversion, index-management deployments, local Vespa application-package assumptions, or the Vespa custom Java searcher.

## Route elsewhere

- Public HTTP route mechanics, document add/update/get/delete examples, and request/response mapping → `../documents-and-api/`.
- Search payload composition, ranking knobs, hybrid/facet/collapse request examples, filters, and recommend payloads → `../search-and-ranking/`.
- Model registry contents, vectorisation backends, inference services, Triton/model-management behavior, model downloads, and CUDA diagnostics → `../inference-and-models/`.
- Choosing test commands, starting/stopping services, Docker compose orchestration, and general contributor workflow → `../local-development/`.

## Open first

1. [Index models](references/index-models.md) for index settings, request/model classes, field names, field types, features, collapse fields, and structured/semi-structured distinctions.
2. [Vespa schema and local app](references/vespa-schema-and-local-app.md) for schema generation, query conversion, index-management deployment flow, Vespa client URLs, local Vespa package expectations, and custom searcher build/deploy guidance.
3. [Troubleshooting](references/troubleshooting.md) for invalid field/index settings, unsupported schema features, Vespa URL/config failures, Java/Maven/custom-searcher issues, Zookeeper lock/convergence problems, and schema update/rollback cautions.
4. `scripts/inspect_vespa_local.py` for a read-only prerequisite inspection of the expected local Vespa helper, schema templates, custom searcher files, and host tools. The script never starts Docker/Vespa and never runs Maven.

## Operating rules

- Treat semi-structured indexes as the future-facing implementation path. Even when a class currently inherits or duplicates behavior from structured internals, direct new index/schema/query changes to the semi-structured code path unless the task is explicitly about a legacy structured behavior.
- Treat public `unstructured` index settings as a compatibility/API label. For current Marqo versions, those settings generate an internal semi-structured Vespa schema; the old unstructured Vespa schema is only for legacy indexes created before the semi-structured cutover.
- Validate index names and field names before diagnosing downstream Vespa errors. Many apparent Vespa failures are actually rejected Marqo names, field features, tensor fields, collapse fields, or model properties.
- For schema-changing work, reason through both Marqo's stored index setting and the generated Vespa schema. Dynamic semi-structured fields can trigger an index schema update during document ingestion.
- For local Vespa or custom-searcher validation, plan in two phases: inspect prerequisites with the bundled script first, then use `local-development` for the actual service/test command selection and explicit service-mutating approval.
- If `HybridSearcher.java` or custom-searcher Java logic changed, building the jar is not enough: the Vespa application package must be redeployed before any query behavior can be trusted.

## Quick safe helper

From this sub-skill directory, inspect only:

```bash
python scripts/inspect_vespa_local.py --repo-root <marqo-repository-root>
python scripts/inspect_vespa_local.py --repo-root <marqo-repository-root> --json
```

The helper reads filesystem metadata and host-tool availability only. It does not run Docker, Maven, Java, Vespa, curl, tests, or repository scripts.
