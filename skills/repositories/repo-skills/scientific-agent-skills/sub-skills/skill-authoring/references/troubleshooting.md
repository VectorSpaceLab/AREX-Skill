# Skill Authoring Troubleshooting

## Frontmatter parse failures

**Symptoms:** `skills-ref` says `name` or `description` is missing even though it appears in the file; CI reports a flow-style metadata block.

**Likely causes:** JSON-style YAML flow mapping, an unclosed frontmatter delimiter, unsupported top-level keys, or YAML scalar coercion.

**Recovery:** Convert to block YAML, keep only the six top-level fields, quote `metadata.version`, and run `scripts/audit_skill_frontmatter.py` followed by `skills-ref validate`.

## Existing skill update rejected because version was not bumped

**Symptoms:** Review or CI notes changed files under `skills/<name>/` with unchanged `metadata.version`.

**Recovery:** Increment the quoted skill metadata version in the same change. Tests do not need to know the exact value; they only require a quoted version to exist.

## Tests accidentally placed in the skill package

**Symptoms:** `tests/_meta` or the frontmatter audit reports `tests/` or `test_*.py` under `skills/<name>/`.

**Recovery:** Move test code to `tests/<name>/`. The runtime skill directory should contain only files future agents load.

## Useful script described only in prose

**Symptoms:** A workflow depends on repetitive validation/conversion logic but the skill only says what to do manually.

**Recovery:** Add a safe bundled script if the logic can run locally with bounded inputs. Add tests and a `skill-requirements.toml` entry. If the original script is too large, credential-bound, destructive, or environment-specific, document a concrete reference-only/exclude reason.

## Diagram generation blocked

**Symptoms:** Repository policy expects `docs/images/<name>.png`, but the generator command cannot be found.

**Recovery:** Do not fabricate output. Record the missing generator script, finish text/test/security checks, and ask a maintainer whether the diagram tooling should be restored or the policy updated.
