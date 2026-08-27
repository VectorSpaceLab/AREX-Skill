# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Chartify. If the current repo commit, dirty state, package version, public API signatures, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on edge-case guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T18:02:38Z",
  "repository": {
    "name": "chartify",
    "remote_url": "https://github.com/spotify/chartify.git",
    "vcs": "git",
    "branch": "master",
    "tag": "5.0.1",
    "commit": "cb401e019fb7625a0f301e572db385c13bf61c0f",
    "working_tree": "dirty-after-generated-skill-artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "chartify",
      "version": "5.0.1",
      "import_names": ["chartify"]
    }
  ],
  "evidence": {
    "source_roots": ["chartify/", "chartify/_core/"],
    "docs": ["README.md", "docs/installation.rst", "docs/usage.rst", "docs/index.rst"],
    "examples": ["chartify/examples.py", "examples/Examples.ipynb", "examples/Chartify Tutorial.ipynb"],
    "tests": [
      "tests/test_axes.py",
      "tests/test_callout.py",
      "tests/test_chart.py",
      "tests/test_color_palettes_config.py",
      "tests/test_colors.py",
      "tests/test_colors_config.py",
      "tests/test_examples.py",
      "tests/test_options_config.py",
      "tests/test_plots.py",
      "tests/test_style_settings_config.py"
    ],
    "package_metadata": ["setup.py", "setup.cfg", "requirements.txt", "requirements_dev.txt", "tox.ini", ".github/workflows/tox.yml"],
    "excluded": [".git/", "docs/_static/", "tests/outputs/", "maintainer release/docs build artifacts"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If public constructor or plot-method signatures differ from those documented in this skill, refresh before answering API-detail questions.
- If the installed package version is not `5.0.1`, use this skill as a starting point only and verify current behavior with the bundled smoke scripts.
- If local changes modify `chartify/`, `docs/`, `examples/`, `tests/`, or package metadata, refresh the skill. Dirty `skills/` output from generation alone does not imply Chartify source behavior changed.
