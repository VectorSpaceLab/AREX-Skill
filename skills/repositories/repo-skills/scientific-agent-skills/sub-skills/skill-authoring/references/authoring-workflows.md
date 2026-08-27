# Authoring Workflows

## Add a new skill

1. Confirm the workflow is narrow, useful, and not already covered by an existing skill.
2. Create `skills/<name>/` with a `SKILL.md` whose frontmatter `name` equals `<name>`.
3. Start `metadata.version` at quoted `"1.0"`.
4. Write a third-person description containing capability and trigger terms.
5. Document prerequisites, packages, credentials, network access, system dependencies, data assumptions, concrete commands, validation checks, and scientific caveats.
6. Add `references/`, `scripts/`, or `assets/` only when they improve reuse. Keep tests and fixtures under `tests/<name>/`.
7. If scripts exist, add their package requirements to `tests/skill-requirements.toml`; use `packages = []` for standard-library-only helpers.
8. Update `docs/skills.md` and any repository-level counts or examples affected by the new entry.
9. Run the lightweight audit, canonical validator, focused tests, repo-wide guard, and security scan plan.

## Update an existing skill

1. Read the current skill and linked files first.
2. Check upstream documentation and the installed package version used by the skill.
3. Make the smallest change that addresses the request.
4. Bump `metadata.version` (`1.2` to `1.3` for normal improvements; a major bump only for a breaking redesign).
5. Re-run changed commands, examples, and scripts.
6. Run `pytest tests/<name> -q` when a suite exists, then choose broader checks through `validation-testing`.
7. Record behavior changes and known limitations for the PR.

## Content placement

- `SKILL.md`: purpose, triggers, short workflow, routing, safety boundaries.
- `references/`: long API details, CLI catalogs, data schemas, extended examples, troubleshooting tables, and provenance.
- `scripts/`: safe repetitive validation, conversion, inspection, or smoke-test logic.
- `assets/`: templates/static files future agents actually need.
- `tests/<name>/`: test code and fixtures only; never ship these under `skills/<name>/`.

## Source and evidence discipline

Use docs and examples for intent, source and installed-package inspection for exact API facts, and tests for edge behavior. Mark untested claims as illustrative. Never copy secrets, private URLs, local paths, credentials, or unpublished data into a skill.
