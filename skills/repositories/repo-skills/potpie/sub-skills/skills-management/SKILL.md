---
name: skills-management
description: "Install, update, inspect, and repair Potpie's bundled agent skills."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Potpie skills management

Use this sub-skill when the task is about Potpie-managed agent skill bundles, install targets, drift, nudge prompts, or skill status.

## Read this when

- The user asks about `potpie skills list`, `potpie skills install`, `potpie skills update`, `potpie skills remove`, `potpie skills status`, or `potpie skills add`.
- A setup run reports missing, outdated, or stale Potpie agent skills.
- You need to inspect the bundled Potpie skill catalog without a running daemon.

## Do not use this for

- The DisCo repo skill you are currently reading; this sub-skill is about Potpie's own agent-bundle installer.
- Runtime daemon startup: read `../runtime/SKILL.md`.
- Graph memory read/write commands: read `../graph-read/SKILL.md` or `../graph-write/SKILL.md`.
- Pot/source or provider auth setup: read `../workspace-boundaries/SKILL.md` or `../auth-integrations/SKILL.md`.

## Operating procedure

1. Use `potpie skills list` to inspect the daemon-backed catalog and `scripts/list_bundle_skills.py` for an offline installed-package catalog.
2. Use `potpie skills install --agent <claude|codex|cursor|...>` to write bundled skill files to an agent harness; choose `--scope global` or `--scope project --path <dir>` deliberately.
3. Use `potpie skills status` before `update` or `remove` so drift and target paths are visible.
4. Treat skills commands as daemon-dependent unless you are using the offline helper script.
5. Do not hand-edit unrelated agent files to bypass Potpie's installer; let the skill manager handle templates, manifest state, and update/remove semantics.

## References

- `references/workflow.md` — bundled skill IDs, target harnesses, install scopes, and drift workflow.
- `references/troubleshooting.md` — daemon unavailable, invalid target path, stale manifest, project/global scope, and outdated bundle nudges.
- `scripts/list_bundle_skills.py` — offline catalog helper for the installed package.

## Verification notes

- Safe native candidates include skills CLI, setup agent-skill/defer-skill flows, skill-manager global target tests, bundle catalog tests, repo-baseline skill tests, and agent-template v1.5 tests.
- No accelerator backend is required for skill-management behavior.
