---
name: repo-skills-router
description: "Routes substantive ML, AI, data, scientific-computing, and software-engineering requests to the smallest useful set of managed repository skills. Invoke proactively when a request names or implies a package, framework, model family, dataset, modality, workflow, backend, deployment target, evaluation method, or implementation approach that may benefit from repository guidance, even if no repository is named. Narrow progressively from area to family to repository root: inspect only the one or two most likely area pages; compare candidates by capability, task surface, model/data format, training versus inference versus evaluation intent, runtime constraints, and root-skill description; then open only the selected root and relevant sub-skills, references, or scripts. Select multiple repositories only when each adds a distinct capability. Do not load the whole collection, treat dependencies or incidental integrations as capabilities, choose by name alone, or force a match when no exact taxonomy family applies."
metadata:
  disco-role: operating
---

# Repo Skills Router

This bundled skill is the empty router template used by DisCo's repository
skill importer. A generated live router contains the current area/family
membership tables under `references/areas/`, `references/families/`, and
`references/index/`. The bundled template contains the canonical taxonomy but
no repository assignments.

Use progressive disclosure: let DisCo Researcher narrow the request from an
area to a family and then to the smallest useful repository-skill set. The
managed collection is already available to DisCo Researcher at runtime, so
cross-agent export is not required for DisCo.

## Routing procedure

1. Identify the user's dominant capability, workflow, data/model format, and
   runtime intent.
2. Read only the one or two most likely area pages.
3. Compare the relevant family pages, especially when training, inference,
   evaluation, deployment, or similarly named repositories overlap.
4. Open the selected repository root at
   `../repo-skills/<skill-id>/SKILL.md`, then read only its relevant sub-skills,
   references, and scripts.
5. If no exact family fits, do not force a repository match; continue with
   general task context or report that the managed collection has no exact
   route.

A repository may appear in several families. Choose the smallest set of roots
that directly covers the request, and do not load every candidate listed on a
family page.

## Empty template state

The taxonomy is the only populated routing input in this bundled template.
`references/index/repositories.jsonl` and
`references/index/assignments.jsonl` are populated only by a collection build
or import transaction. The live router is model-visible by default; the CLI
may add `disable-model-invocation: true` only when the user explicitly
disables automatic router selection.

## Maintenance

The machine-readable files under `references/index/` are the generated routing
source of truth. Do not hand-edit area or family pages. For creation,
verification, refresh, extension, import, or taxonomy changes, read
[references/maintenance.md](references/maintenance.md) and use the verified
importer/updater transaction.
