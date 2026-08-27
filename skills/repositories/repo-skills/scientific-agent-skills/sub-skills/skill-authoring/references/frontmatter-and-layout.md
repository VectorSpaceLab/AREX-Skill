# Frontmatter and Layout

## Canonical frontmatter fields

Canonical repository skills use the closed Agent Skills top-level field set:

- `name` (required): lowercase letters, digits, hyphens; must equal directory basename.
- `description` (required): third-person, useful trigger terms, max 1024 characters.
- `license` (optional).
- `compatibility` (optional): environment requirements only.
- `allowed-tools` (optional): a space-separated string such as `Read Write Edit Bash`; not a list and not comma-separated.
- `metadata` (required by this repository): a mapping containing quoted `version`.

Put authorship, review dates, host manifests, and other custom data under `metadata`, not at top level.

## YAML rules that prevent CI failures

- Use block-style YAML. Do not write JSON flow mappings such as `metadata: {"version": "1.0"}`.
- Quote scalar metadata values that YAML could coerce: `version: "1.0"`, dates, booleans, and numeric-looking values.
- Keep `metadata.openclaw` and `metadata.hermes` as nested mappings when used; do not stringify them as JSON.
- Mention credentials in `compatibility` and host manifest metadata, not in a non-spec top-level key.

## Body and file layout

- Keep `SKILL.md` below 500 lines.
- Move long details to linked references.
- Keep local links relative to the skill root and verify they resolve.
- Do not include `tests/`, `test_*.py`, bytecode, caches, downloaded artifacts, or scratch outputs under `skills/<name>/`.
- If a script is useful and safe, bundle it under the skill; if it is unsafe, credential-bound, too large, or maintainer-only, explain that in a reference or PR note rather than telling agents to run it blindly.

## Fast preflight

Run the bundled lightweight audit before heavier validators:

```bash
python sub-skills/skill-authoring/scripts/audit_skill_frontmatter.py --skill-dir skills/<name>
```

This helper is not a replacement for `skills-ref validate` or `tests/_meta`; it catches common local mistakes quickly and without importing repository test helpers.
