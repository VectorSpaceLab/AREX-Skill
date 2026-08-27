---
name: development-maintenance
description: "Make safe Nilearn checkout code, test, documentation, changelog,
  and maintenance changes without violating repository architecture or
  conventions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Nilearn Development Maintenance Skill

Use this sub-skill when working inside the Nilearn source checkout on code,
tests, documentation, changelog entries, maintenance scripts, or repository
configuration. It is for coding-agent maintenance tasks, not user-facing
neuroimaging analysis workflows.

## Route Tasks

- **Code changes:** Follow style, public API, backcompat, deprecation, and
  estimator conventions in [development guide](references/development-guide.md).
- **Import architecture:** Check the import-linter layer rules before adding
  cross-package imports. See [development guide](references/development-guide.md)
  and [troubleshooting](references/troubleshooting.md).
- **Tests and docs:** Pick narrow no-network tests first, mark generated or
  modified tests with `@pytest.mark.ai_generated`, and use doc/gallery guidance
  in [testing and docs](references/testing-and-docs.md).
- **Validation planning:** Use the bundled helper to suggest targeted commands
  without running them:
  `python scripts/select_safe_tests.py <changed-paths>` from this sub-skill directory.
- **Failures:** Diagnose import-linter, optional plotting, baseline image,
  network/data skip, estimator-check, and pre-commit failures with
  [troubleshooting](references/troubleshooting.md).

## Quick Checklist

1. Keep changes focused; do not add dependencies or unrelated refactors.
2. Respect `pyproject.toml` ruff settings: double quotes, 4-space indents, and
   79-character Python lines.
3. Use absolute internal imports and obey Nilearn's layered import contracts.
4. Preserve scikit-learn-style estimator APIs: `fit` returns `self`, learned
   attributes end with `_`, and `fit` overwrites fitted state.
5. Add or update small synthetic tests near the changed module and mark any
   generated or modified tests with `@pytest.mark.ai_generated`.
6. Add an entry to `doc/changes/latest.rst` for PR-worthy user, API, code,
   test, doc, plotting, maintenance, or deprecation changes.

## Boundaries

- Route analysis usage, Niimg operations, GLM, maskers, decoding,
  connectivity, plotting, or surface workflows to their domain sub-skills unless
  the task is specifically about changing Nilearn source/tests/docs.
- Do not run broad test suites, slow examples, visual baseline generation,
  network dataset downloads, or native data fetchers unless the user explicitly
  asks and the environment is appropriate.
- Do not create Codex-, Claude-, or export-specific files from this sub-skill.

## References

- [Development guide](references/development-guide.md)
- [Testing and docs](references/testing-and-docs.md)
- [Troubleshooting](references/troubleshooting.md)
- [Safe test selector](scripts/select_safe_tests.py)
