# Validation and Testing Troubleshooting

## Missing suite for a script-bearing skill

**Symptom:** `tests/_meta` says a skill ships `scripts/` but has no `tests/<name>/` suite.

**Fix:** Add `tests/<name>/test_scripts.py` or another `test_*.py` file. Use `SKILL_ROOT = Path(__file__).resolve().parents[2] / "skills" / "<name>"` as the anchor.

## Missing `skill-requirements.toml` entry

**Symptom:** `tests/_meta` asks for a `[skills.<name>]` block.

**Fix:** Add one. If the skill scripts are standard-library only, use `packages = []`; otherwise list only the packages that the skill documents or the tests require.

## Wrong interpreter or dependency conflict

**Symptom:** A scientific package cannot install in the project environment, or another skill's dependency version breaks it.

**Fix:** Do not install all scientific packages together. Use `python tests/run_all.py --isolated <name>` and set a per-skill `python` override in the manifest when needed.

## Broken local link

**Symptom:** `tests/_meta` reports `references/...` or `scripts/...` does not exist.

**Fix:** Create the target file, repair the relative path, or remove the link. Runtime links should point to files shipped inside that skill. Cross-skill links are accepted only when the owning skill is named on the line and the path exists there.

## Multiple suites collected together

**Symptom:** Pytest usage error says it cannot collect multiple skills in one process.

**Fix:** Run one suite at a time or use `python tests/run_all.py`.

## `skills-ref` passes but CI still fails

**Likely cause:** Repository-specific checks or `tests/_meta` caught rules outside the reference validator, such as missing `metadata.version`, unquoted metadata scalars, missing test suite, hardcoded local path, or invalid script. Run `tests/_meta` and inspect the failing rule name.
