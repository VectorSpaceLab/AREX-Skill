---
name: marqo
description: "Marqo AI-native search service workflows for HTTP APIs, indexes,
  Vespa schemas, search/ranking, inference/model services, and local repository
  development."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Marqo

Use this repo skill when a task involves Marqo: AI-native search APIs, index/document/search workflows, Vespa-backed schema/query behavior, inference/model-management services, or Marqo repository development and testing.

Marqo is a multi-component Python/FastAPI service repository. Its main public surface is the Marqo API service, with supporting common model registry, inference orchestrator, model-management service, Vespa application package, and Docker/compose runtime.

## First checks

- Read [references/repo-provenance.md](references/repo-provenance.md) before relying on this skill for a checkout whose commit or package metadata may differ.
- Read [references/package-map.md](references/package-map.md) for component/package/import names, important routes, and environment variables.
- Use [scripts/check_marqo_environment.py](scripts/check_marqo_environment.py) for a safe import/version/route/backend probe. It does not start services or download models.
- Use [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import/service/backend failures before opening a narrower sub-skill.

## Route by task

| User task | Open |
| --- | --- |
| Health/index/document/embed/recommend/typeahead HTTP requests, request/response/error mapping, dry-run HTTP smoke plans | [sub-skills/documents-and-api/](sub-skills/documents-and-api/SKILL.md) |
| Index settings, structured vs semi-structured vs legacy unstructured models, field validation, Vespa schema/query generation, local Vespa app/custom searcher guidance | [sub-skills/index-and-vespa/](sub-skills/index-and-vespa/SKILL.md) |
| Tensor/lexical/hybrid search payloads, filters, searchable attributes, score modifiers, facets, collapse, recency, sort, relevance cutoff, recommend ranking choices | [sub-skills/search-and-ranking/](sub-skills/search-and-ranking/SKILL.md) |
| Model registry, `/vectorise`, preprocessing schemas, random/HF/OpenCLIP pipelines, inference cache, Triton/model-management load/unload, CUDA/backend checks | [sub-skills/inference-and-models/](sub-skills/inference-and-models/SKILL.md) |
| Local development, Docker/Vespa/Triton/Redis/Zookeeper services, Maven custom searcher build, test selection, contributor rules | [sub-skills/local-development/](sub-skills/local-development/SKILL.md) |

## Operating rules

1. Prefer the narrowest sub-skill. Marqo search requests often span API, index schema, search ranking, and model inference; route each decision to its owning sub-skill instead of guessing.
2. Treat service-mutating actions as explicit decisions. Bundled scripts default to printing or checking only; starting/stopping containers, deleting indexes, deploying Vespa apps, loading models, and sending writes to Marqo require user approval or an explicit live-service request.
3. For no-download or no-service checks, prefer `random/*` model properties, safe import probes, and payload builders before using OpenCLIP/HF model downloads or Triton.
4. When editing source, follow the repository rule to make changes directly in `semi_structured_vespa_index` even if code inherits from `structured_vespa_index`.
5. Core code should raise `marqo.core.exceptions` or `marqo.exceptions`, not API-layer exceptions; API mapping belongs in the API layer.
6. Use Python 3.11 for package/runtime checks. Unit and integration tests generally require component-root working directories and `PYTHONPATH=./src`.

## Minimal public install/import check

For a development checkout, install only the component(s) needed for the task rather than every dev/perf requirement group. For package-use checks, the important import names are:

```python
import marqo
import marqo_common
import inference_orchestrator
import model_management
```

For an offline safety probe from a prepared environment:

```bash
python scripts/check_marqo_environment.py --json
```

If imports fail, open [references/troubleshooting.md](references/troubleshooting.md) and then route to [sub-skills/local-development/](sub-skills/local-development/SKILL.md) for install/test setup or [sub-skills/inference-and-models/](sub-skills/inference-and-models/SKILL.md) for optional model/backend dependencies.

## Verification scope

This skill includes safe script checks and static/offline workflows. Service-backed API, Vespa, Triton, and model-download checks are intentionally optional and must be selected explicitly because they can start containers, mutate indexes, deploy application packages, or contact external model/object stores.
