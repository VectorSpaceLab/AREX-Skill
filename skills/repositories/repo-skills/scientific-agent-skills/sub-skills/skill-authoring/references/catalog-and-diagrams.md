# Catalog and Diagrams

## Catalog updates

Update repository-level catalog material when a new skill, renamed skill, removed skill, or materially changed public description affects discovery. The primary catalog evidence in this snapshot is `docs/skills.md`; the README also carries public counts, categories, and examples.

When updating catalog prose:

- Keep descriptions concise but specific.
- Include the package/service/workflow name and natural trigger terms.
- Preserve safety boundaries and credential/network requirements.
- Avoid duplicating a full skill body in the catalog.
- Check links point to the skill directory and match the canonical name.

## Diagram policy

Repository policy says every canonical skill has a generated workflow image at `docs/images/<skill-name>.png`, and the image should be regenerated when the skill's workflow changes.

In this checkout snapshot, the documented generator script was not present. Therefore:

1. Do not invent or hand-draw a placeholder image.
2. Check whether `scripts/generate_skill_image.py` exists in the target checkout before promising regeneration.
3. If it exists, run the documented dry-run/prompt-only path first when appropriate, then generate after the skill text and references are final.
4. If it is absent, record the missing generator as a blocker in the PR or maintenance notes and still complete text/test/security validation.

A typo fix, link repair, or version bump alone does not require a new image.

## Release and public count notes

`pyproject.toml` version changes can trigger the release workflow on `main`. Do not bump the project version, create tags, or create releases unless the user explicitly asks for release preparation. Skill-level `metadata.version` bumps are separate from the repository package version.
