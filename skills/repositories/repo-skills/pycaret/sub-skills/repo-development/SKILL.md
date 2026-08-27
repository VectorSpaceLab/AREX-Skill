---
name: repo-development
description: "Contributor and maintainer workflows for the PyCaret monorepo:
  layout, coding conventions, testing, releases, decisions, docs, issue triage,
  and kill-list guardrails."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Repo Development

Use this sub-skill when a task asks you to modify or review the PyCaret source tree, contributor workflow, CI, release notes, developer docs, issue triage, dependency policy, or maintainer automation.

Do **not** use this sub-skill for user-facing PyCaret engine recipes, Control Plane API operation, self-hosting runbooks, or web UI usage. Route those to the sibling sub-skills that own those surfaces.

## Quick routing

- Engine notebook/script usage, task classes, typed results, model workflows → `engine-workflows`.
- FastAPI routes, server CLI, workspaces/runs/data sources/deployments/LLM API → `control-plane-api`.
- React source, route/component conventions, API client, Vitest → `web-ui`.
- Docker, config, secrets, backup/restore, worker/GPU operations → `platform-operations`.
- Repository editing policy, tests, releases, docs, issue triage, kill-list checks → stay here.

## Read these first

1. [references/contributor-guidance.md](references/contributor-guidance.md) for monorepo map, non-negotiables, coding style, and change-record rules.
2. [references/testing-matrix.md](references/testing-matrix.md) to choose the smallest adequate local and CI-equivalent checks.
3. [references/kill-list-and-decisions.md](references/kill-list-and-decisions.md) before restoring any 3.x behavior, dependency, public API, or architectural pattern.
4. [references/release-and-docs.md](references/release-and-docs.md) for release prep, notebook generation, site docs, and changelog handling.
5. [references/troubleshooting.md](references/troubleshooting.md) when installs, tests, migrations, optional extras, stale docs, or secret scanning fail.

## Conservative maintainer workflow

1. Identify the touched area: `packages/engine`, `services/api`, `apps/web`, `apps/site`, `infra`, or docs/config.
2. Check whether the request conflicts with the kill list or an ADR. If it does, stop and report the conflict unless the maintainer explicitly changes scope.
3. Plan a small, cohesive diff. For bugs, reproduce first and add/adjust a behavior-level test before changing implementation.
4. Implement with the conventions in the references. Do not invent a second shape for `RunConfig`, model metadata, UI schema, or release notes.
5. Run the relevant validation subset from [references/testing-matrix.md](references/testing-matrix.md), then broaden only when the touched surface requires it.
6. Record the change: release-notes entry for non-trivial changes; status/roadmap/ADR updates only when the change actually finishes scope, changes scope, or makes a non-obvious decision. Respect any active agent policy that requires explicit approval before editing archival `docs/revamp` files.
7. Before handoff, run the safe helpers when applicable:
   - [scripts/check_secrets.sh](scripts/check_secrets.sh) to scan for accidental credentials.
   - [scripts/classify_issue_text.py](scripts/classify_issue_text.py) to triage pasted issue text against kill-list and stale/fixed hints.
   - [scripts/verify_skill_tree.py](scripts/verify_skill_tree.py) when editing this generated skill tree.

## Hard stops

- Do not reintroduce killed engine APIs or dependencies as compatibility shims.
- Do not restore the 3.x module-level functional API. Current PyCaret 4 is OOP-only.
- Do not add a runtime dependency without deciding core vs optional extra, adding a release-note entry, and adding or updating an ADR when the dependency is new top-level scope.
- Do not publish packages, push to `main`, force-push, bypass hooks, alter legal files, or bump versions unless the maintainer explicitly asks for a release task.
- Do not let LLM/advisory code trigger destructive actions directly; the user approves and the deterministic engine/server executes.
