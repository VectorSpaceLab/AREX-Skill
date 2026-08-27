---
name: nodes-catalog
description: "Explains RocketRide node catalog service definitions,
  documentation rules, optional dependencies, and node contract
  troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# RocketRide Nodes Catalog

Use this sub-skill when the task is about RocketRide node providers, `service*.json` definitions, node categories, generated node documentation, per-node requirements, or node contract failures.

## Route first

- Read [service-definition-guide.md](references/service-definition-guide.md) to understand `service*.json` fields such as `title`, `protocol`, `classType`, `capabilities`, `register`, `node`, `path`, `prefix`, `lanes`, `preconfig`, and parameter/shape definitions.
- Read [node-workflows.md](references/node-workflows.md) when adding or revising a node, updating co-located node docs, regenerating the generated parameters block, choosing node tests, or handling per-node dependencies.
- Read [troubleshooting.md](references/troubleshooting.md) when a service JSON does not parse, a node cannot be wired, generated docs drift, optional dependencies are missing, or node contract tests fail.

## Scope boundaries

This sub-skill owns the node catalog and node-maintainer rules. It does not own full `.pipe` composition recipes, SDK usage, runtime deployment, or generic builder-task documentation. For those, route to the root skill's pipeline, SDK, runtime, or development/build/docs guidance.

## Validation helper

Use the shared static probe `../../scripts/rocketride_static_probe.py` with
`--service-json` to parse a concrete service definition with comments before
trying broader docs generation or native node tests.

## Operating principles

- Treat `service*.json` as JSON-with-comments, not strict JSON. Use a parser that strips `//` comments and trailing commas before validation.
- Keep `SKILL.md` routing concise. The field catalog, maintenance recipes, and failure modes live in the bundled references.
- Do not claim that all optional node dependencies, provider credentials, GPU packages, databases, or external services are installed. The node catalog can document them; verification should use static parsing or explicitly selected safe tests unless the user authorizes broader runtime work.
- When a public node input, output, config schema, or generated docs block changes, update the co-located prose in the same change and regenerate the generated parameter block instead of editing generated rows manually.
