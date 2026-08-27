---
name: skill-authoring
description: "Creates and updates canonical Agent Skills in the Scientific Agent
  Skills repository while preserving scope, frontmatter, progressive disclosure,
  versioning, tests, catalog entries, and diagram policy. Use for new skills,
  skill revisions, metadata fixes, references/scripts/assets placement, or
  contribution checklists."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Skill Authoring

Use this route when the task changes a canonical skill under `skills/<name>/`.

## Before editing

1. Read the existing `SKILL.md` and every linked local reference/script that the change may affect.
2. Read `AGENTS.md` and the relevant `CONTRIBUTING.md` section.
3. Decide whether the request is a new skill, an update, or a scope correction. Do not create a broad orchestrator skill merely because several neighboring skills exist.
4. Use current upstream package/platform documentation for API claims; keep untested behavior explicitly illustrative.

Read `references/authoring-workflows.md` for the new/update checklists and `references/frontmatter-and-layout.md` for the exact structural contract. Use `scripts/audit_skill_frontmatter.py` for a fast local preflight before the repository validator.

## New skill route

- Create `skills/<name>/` with a matching lowercase-hyphen `SKILL.md`.
- Put only runtime content in the skill directory: `SKILL.md`, `references/`, `scripts/`, and useful `assets/`.
- If the skill ships scripts, create tests under `tests/<name>/` and add a matching entry to `tests/skill-requirements.toml`.
- Keep the root document router-like; move long API tables, examples, data schemas, and troubleshooting matrices into references.
- Update the public catalog and any required generated diagram only after the content is final. Read `references/catalog-and-diagrams.md` because this checkout may not contain the diagram generator named by repository policy.

## Existing skill update route

- Make the smallest useful change and preserve unrelated behavior.
- Bump the quoted `metadata.version` in the same change.
- Re-run touched examples/scripts and the skill's own test suite.
- Re-check local links, line count, optional dependency claims, credentials, and safety boundaries.
- If the workflow or references changed materially, regenerate the diagram when the required tool is available; a typo/link/version-only change does not require an image refresh.

## Exit handoff

Before handing off, report the skill directory, files changed, evidence consulted, intentional omissions, version bump, test/validation commands to run, catalog/diagram status, and any upstream or environment uncertainty. Route execution to `validation-testing`, then route scanner review to `security-scanning`.
