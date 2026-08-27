---
name: local-development
description: "Local Marqo repository development, service operation, testing,
  Docker/Vespa/Triton prerequisites, Maven custom searcher build guidance, and
  contributor constraints."
disable-model-invocation: true
metadata:
  disco-role: operating
  repo: marqo
  sub-skill-id: local-development
license: Apache 2.0
---

# local-development

Use this sub-skill when the task is about preparing a Marqo development environment, choosing local tests, planning service startup, diagnosing local Docker/Vespa/Triton/Redis/Zookeeper problems, building the Vespa custom searcher, or applying repository contribution rules.

Do **not** use this sub-skill for API payload semantics, index/search/model internals, or user-facing request examples beyond service/test setup:

- Public route behavior, document/index/typeahead payloads → `documents-and-api`.
- Index schemas, Vespa query generation, field-type semantics → `index-and-vespa`.
- Search/ranking/filter/score semantics → `search-and-ranking`.
- Inference schemas, model registry, model-management payloads → `inference-and-models`.

## Required operating pattern

1. Start from the relevant bundled reference:
   - [Local services](references/local-services.md) for service topology, environment variables, compose profiles, Vespa/API/Triton/MMC/MIOC plans, ports, and Java/Maven custom searcher build steps.
   - [Testing](references/testing.md) for safe unit/integration/API-test command selection, working directories, `PYTHONPATH`, and service prerequisites.
   - [Contributor guidance](references/contributor-guidance.md) for maintainer rules, imports, exceptions, semi-structured changes, and test style.
   - [Troubleshooting](references/troubleshooting.md) for failure-mode triage.
2. Prefer safe planning before mutation. The bundled scripts print plans by default:
   - `scripts/print_service_commands.py` prints service/build/test command plans without running them.
   - `scripts/select_tests.py` maps changed files to a minimal test plan without running tests unless `--run` is explicitly passed.
3. Before running any repository command, activate the intended Python environment and load the repository `.env` variables when present. Use Python 3.11 for Marqo services.
4. For Marqo unit and integration tests, run from the Marqo component root with `PYTHONPATH=./src`. For API tests, run a Marqo API process first and terminate it after the test session.
5. If `HybridSearcher.java` or Vespa custom searcher code changes, build the custom searcher with Maven and redeploy the Vespa application package before validating behavior against Vespa.
6. Treat Docker/Vespa/API tests as service-mutating: they can create/delete indexes, start/stop containers, download images/models, and change local ports. Ask for explicit approval when the task has not already authorized service changes.

## Quick safe helpers

From this sub-skill directory, print commands only:

```bash
python scripts/print_service_commands.py --plan all
python scripts/print_service_commands.py --plan local-api
python scripts/select_tests.py components/marqo/src/marqo/core/semi_structured_vespa_index/semi_structured_vespa_index.py
```

Only run selected safe unit tests when explicitly requested:

```bash
python scripts/select_tests.py --run components/marqo/src/marqo/core/semi_structured_vespa_index/semi_structured_vespa_index.py
```

The scripts never start or stop containers and never run service-backed tests.
