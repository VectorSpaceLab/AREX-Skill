---
name: repository-maintenance
description: "Maintain the ARIS repository, skill corpus, helper scripts,
  installers, MCP servers, mirrors, provenance rules, and focused native tests
  safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Repository Maintenance

Use this sub-skill when changing the ARIS checkout itself: `skills/`, shared references, installer scripts, `tools/`, MCP servers, templates, tests, Codex mirrors, reviewer overlays, or repository documentation.

## Route Here

- Add, update, remove, or reorganize an ARIS skill.
- Fix installer selection/reconcile/symlink behavior.
- Maintain `tools/skill-groups.tsv`, helper-resolution contracts, Codex mirrors, and reviewer overlays.
- Change Python helpers or MCP servers and choose focused tests.
- Preserve provenance, cross-model review, safety, and corpus-write guardrails.

## Reroute

- User project installation and manifest operations: `../install-and-distribution/SKILL.md`.
- Choosing or invoking ARIS workflows: `../workflow-routing-and-skill-catalog/SKILL.md`.
- Provider configuration as a user task: `../review-and-provider-backends/SKILL.md`.
- Project state or watchdog operation: `../state-recovery-and-experiment-ops/SKILL.md`.

## Maintenance Pattern

1. Read `CONTRIBUTING.md`, `AGENT_GUIDE.md`, and the owning `SKILL.md`/shared references.
2. Identify the narrowest source surface and its native test candidates.
3. Preserve helper resolution; do not add hardcoded `python3 tools/...` calls to skills.
4. Update the catalog/mirrors/overlays when the change affects them.
5. Run focused tests first, then broader inventory/static checks.
6. Keep credentials, private paths, generated outputs, and external API calls out of tests.

## Reference Map

- `references/maintenance-checks.md` covers corpus, catalog, mirror, helper, and provenance checks.
- `references/native-tests.md` maps common source changes to safe focused test commands.
- `references/troubleshooting.md` covers test collection, optional dependency, mirror drift, and installer failures.
- Root `../../references/repo-provenance.md` explains the source snapshot used by this generated skill.

## Avoid

- Do not run the privileged meta-apply path automatically.
- Do not rewrite the whole skill corpus for a local feature.
- Do not treat a passing syntax/import check as proof of a live provider, GPU, or remote workflow.
- Do not import this generated skill into a managed router as part of repository maintenance; import is a separate authorized step.
