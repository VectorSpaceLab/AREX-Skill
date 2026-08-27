---
name: potpie
description: "Operate Potpie's CLI, daemon, context graph, source bindings, auth
  integrations, and bundled agent skills."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Potpie

Use this repo skill when a task names Potpie or asks how to operate its CLI, daemon runtime, Context Graph memory, pot/source workspace boundaries, provider integrations, graph read/write surface, or bundled agent-skill installer.

## Quick start

```bash
uv tool install potpie          # or: python -m pip install potpie
potpie --version
potpie --help
potpie daemon status
```

If you are working inside a live Potpie source checkout, the repo also provides `make cli-install` and `make cli-status`; those are convenience paths, not requirements for using this generated skill.

## Route by task

| Task surface | Read |
| --- | --- |
| Install, setup, status, doctor, daemon, backend, UI, telemetry | [`runtime`](sub-skills/runtime/SKILL.md) |
| Pots, active workspace, repo defaults, registered sources | [`workspace-boundaries`](sub-skills/workspace-boundaries/SKILL.md) |
| Potpie login/logout, provider credentials, GitHub/GitLab/Linear/Jira/Confluence/GitBucket, ledger | [`auth-integrations`](sub-skills/auth-integrations/SKILL.md) |
| Resolve/search/read graph context, entity keys, neighborhoods, timeline, graph status, inspect/export | [`graph-read`](sub-skills/graph-read/SKILL.md) |
| Record/propose/commit/mutate graph state, import/repair, inbox, quality, bulk, nudge | [`graph-write`](sub-skills/graph-write/SKILL.md) |
| Install/update/status/remove Potpie's bundled agent skills | [`skills-management`](sub-skills/skills-management/SKILL.md) |

## Operating rules

- Diagnose runtime availability before retrying graph or skills commands. `potpie daemon status` is the safe first probe; many higher-level commands are daemon-dependent.
- Keep workspace identity explicit. Pot/source registration chooses the workspace boundary; it does not by itself scan or ingest data.
- Keep provider credentials separate from source bindings. A provider token does not automatically link a repo to a pot or populate the graph.
- Prefer read-before-write for graph tasks: resolve entity keys and scope, then use `graph propose` followed by `graph commit` for durable changes.
- Treat Event Ledger and managed/cloud command surfaces as limited unless the current runtime proves support.
- Do not use Potpie's own `potpie skills install` command to import this generated DisCo repo skill; that command manages Potpie's packaged agent bundle.

## Bundled helpers

- [`scripts/potpie_smoke.sh`](scripts/potpie_smoke.sh) — safe CLI help/version/daemon-status smoke check.
- [`scripts/typecheck_public_context_api.py`](scripts/typecheck_public_context_api.py) — public API import smoke for context-core/context-engine.
- [`scripts/generate_agent_contract.py`](scripts/generate_agent_contract.py) — installed-package graph/agent contract reference generator.
- [`sub-skills/skills-management/scripts/list_bundle_skills.py`](sub-skills/skills-management/scripts/list_bundle_skills.py) — offline bundled-agent-skill catalog listing.

## Root references

- [`references/troubleshooting.md`](references/troubleshooting.md) — cross-cutting install, daemon, source, auth, graph, and skills triage.
- [`references/repo-provenance.md`](references/repo-provenance.md) — source commit, versions, evidence paths, and staleness triggers.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) — structured placement for `repo-skills-router` import.
