---
name: instrumentations
description: "Router for OpenLLMetry instrumentation packages, SDK instrument
  selection, and wrapper troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Instrumentations

Use this sub-skill for direct use and troubleshooting of OpenLLMetry instrumentation packages and SDK instrument selection across providers, vector DBs, frameworks, local services, and protocol wrappers.

## Route away from this sub-skill

- SDK initialization, exporters/processors, decorators, manual spans, and tracing setup -> [sdk-and-tracing](../sdk-and-tracing/SKILL.md)
- Exact semantic-convention constants, aliases, and migration tables -> [semantic-conventions](../semantic-conventions/SKILL.md)
- Nx, uv, package maintenance, release, and VCR replay workflow -> [repo-development](../repo-development/SKILL.md)

## This sub-skill owns

- instrumentor package discovery and install mapping
- direct `Instrumentor().instrument()` usage for provider, vector DB, framework, local service, and protocol clients
- SDK `Instruments` / `block_instruments` selection for those same surfaces
- content capture mode vs event mode, suppression of nested language-model instrumentation, and metrics/logs behavior
- package-specific import/runtime troubleshooting, including optional target clients and live-service implications

## Start here

- [Instrumentation catalog](references/instrumentation-catalog.md)
- [Workflow recipes](references/workflow-recipes.md)
- [Troubleshooting](references/troubleshooting.md)
- [Instrumentor inspector](scripts/inspect_instrumentors.py)

## Router notes

- Prefer direct instrumentors when the app already owns its tracer, meter, or logger providers.
- Prefer SDK selection when the app wants OpenLLMetry to choose multiple instrumentations from the installed package set.
- Use the catalog to map a distribution to its entry point and target dependency before guessing imports.
- Use the troubleshooting reference before assuming a bug in the wrapper.
- For exact GenAI attribute names, event shapes, and migration details, follow the semantic-conventions sub-skill.
