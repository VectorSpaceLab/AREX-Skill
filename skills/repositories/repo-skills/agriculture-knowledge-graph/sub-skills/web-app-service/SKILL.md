---
name: web-app-service
description: "Operate the Django 1.11 demo application, its routes, forms, and
  service preflight checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# web-app-service

Use this sub-skill when you need to inspect, run, or modify the Django demo under `demo/`.

## Start here
- [Routes and views](references/django-routes-and-views.md)
- [QA and tagging flows](references/question-answering-and-tagging.md)
- [Configuration and prerequisites](references/configuration.md)
- [Troubleshooting](references/troubleshooting.md)
- [Preflight script](scripts/run_django_demo_check.sh)

## Owns
- Django URL routing, request field names, and page-to-view mapping.
- Service startup checks for Neo4j, MongoDB, and bundled data assets.
- Eager preload side effects from the demo's shared model modules.
- QA, tagging, and image-match request flow behavior.

## Route elsewhere
- Graph import/schema, Cypher, or data loading -> graph-query-and-data-management
- NER and label classification -> entity-labeling-and-ner
- Relation dataset construction or PCNN training -> relation-extraction-pipeline

## Safe usage
Run `scripts/run_django_demo_check.sh --repo-root <repo-root>` before starting the app. Add `--start` only when you explicitly want the server command executed after the checks pass.

The shared preload module initializes THULAC, Neo4j, MongoDB, the word-vector model, and the taxonomy tree as soon as the view modules import it. If those resources are missing, the app can fail during startup rather than on the first request.
