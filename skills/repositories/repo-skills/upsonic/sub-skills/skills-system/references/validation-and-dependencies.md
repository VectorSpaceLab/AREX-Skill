# Validation and Dependencies

## Verified validation rules

- The `SKILL.md` frontmatter must start with YAML and expose a mapping.
- Required keys: `name` and `description`.
- The skill name must be lowercase, hyphenated, and no longer than 64 characters.
- The skill directory name must match the skill name.
- The description must be plain text and no longer than 1024 characters.
- `compatibility`, `license`, `allowed-tools`, `metadata`, and `dependencies` have their own shape checks.
- DisCo repo skills add `disable-model-invocation` and `metadata.disco-role`; use the bundled validator's `--allow-disco-fields` flag when checking this generated repo-skill tree.

## Dependency behavior

- Missing dependencies produce warnings unless `strict_deps=True`, in which case validation fails.
- Dependency cycles are detected and can be escalated to a hard failure in strict mode.
- `cache_ttl` enables a skill cache for repeated lookups.
- `on_script_execute` and `on_reference_access` are hooks future agents can use for tracing skill usage.

## Good debugging sequence

1. Run the bundled directory validator.
2. Fix frontmatter and naming first.
3. Resolve missing dependencies and cycles.
4. Only then debug script or reference content.
