---
name: developer-extension
description: "Guides contributors modifying or extending Viseron components,
  domains, reload behavior, entities, docs, tests, and source-root imports."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Developer Extension

Use this sub-skill when the task is to modify or extend Viseron backend code rather than only configure an existing camera, detector, recorder, or integration.

## Route here for

- Adding or changing a component package, domain implementation, domain dependency, entity, event/data-stream publisher or subscriber, config schema, or unload hook.
- Diagnosing component/domain lifecycle states, `DomainNotReady` retries, hot reload behavior, or stale entities/listeners after reload.
- Updating schema-backed component documentation or choosing focused backend tests for a component/domain/reload change.
- Investigating source-root/import failures around subprocess workers and top-level `manager.py`.

## Do not use for

- User-level Viseron configuration recipes, camera stream tuning, detector labels/zones, notification delivery, or deployment operations; route those to the corresponding sibling workflow sub-skill.
- Full release engineering, CI image maintenance, or container builds except as reference-only context.

## Operating references

Read only the references needed for the current change:

1. [Component and domain API](references/component-domain-api.md) for component shape, `CONFIG_SCHEMA`, `setup()`/`setup_domains()`, domain registration, `RequireDomain`/`OptionalDomain`, entities, events, and `Viseron` core APIs.
2. [Reload and lifecycle](references/reload-and-lifecycle.md) for component/domain state transitions, unload order, hot reload rules, identifier-level changes, and retry behavior.
3. [Docs, tests, and packaging](references/docs-tests-and-packaging.md) for schema-derived docs, focused tests, safe schema inspection, and the source-root `manager.py` import caveat.
4. [Troubleshooting](references/troubleshooting.md) for owned failure modes before proposing code changes.

## Bundled helper

Use [`scripts/inspect_component_schema.py`](scripts/inspect_component_schema.py) as a read-only helper to summarize one component's `CONFIG_SCHEMA` and, when requested, supported domain schemas. It prints to stdout and never writes Docusaurus files.
