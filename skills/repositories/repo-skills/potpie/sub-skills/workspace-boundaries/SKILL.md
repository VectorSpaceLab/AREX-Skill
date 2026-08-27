---
name: workspace-boundaries
description: "Manage Potpie pots, repo defaults, and source registration boundaries."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Potpie workspace boundaries

Use this sub-skill when the task is about which Potpie workspace (`pot`) owns a repository, which source is registered, or why a command cannot find the expected repo default.

## Read this when

- The user asks about `potpie pot ...`, `potpie source ...`, default pot bindings, or source status.
- A workflow needs to bind a local repo, remote repo identity, or provider source before graph operations.
- A failure says there is no active pot, no linked repo, an unknown source, or ambiguous repository identity.

## Do not use this for

- Runtime/daemon setup: read `../runtime/SKILL.md`.
- Provider login, tokens, OAuth, or ledger binding: read `../auth-integrations/SKILL.md`.
- Graph read/write semantics: read `../graph-read/SKILL.md` or `../graph-write/SKILL.md`.
- Bundled agent-skill installation: read `../skills-management/SKILL.md`.

## Operating procedure

1. Inspect the active workspace with `potpie pot list`, `potpie pot info`, and `potpie pot linked` before creating a new pot.
2. Register a repository source with `potpie source add repo ...` or `potpie pot create ... --repo ...` when the user wants Potpie to know about a codebase.
3. Remember that source registration is not ingestion. It records source metadata so later graph, ledger, and nudge paths can reason about it.
4. Use `potpie pot default show|set|clear` to manage the repo default instead of relying on the current shell directory.
5. Avoid destructive commands such as `potpie pot reset` unless the user explicitly wants to clear data for that pot.

## References

- `references/workflow.md` — pot/source command matrix, repo-default resolution, and safe examples.
- `references/troubleshooting.md` — repo identity, source normalization, no-scan behavior, and reset cautions.

## Verification notes

- Safe native candidates include pot creation, source CLI contract, repo-location, first-pot setup, empty-pot guidance, and source-resolution tests.
- No accelerator backend is required for workspace boundary behavior.
