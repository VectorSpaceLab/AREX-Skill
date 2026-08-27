# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, public
entry points, or major evidence paths differ from this snapshot, run a refresh
workflow before relying on the skill for precise API guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T16:28:48Z",
  "repository": {
    "name": "fg-data-profiling",
    "remote_url": "https://github.com/Data-Centric-AI-Community/fg-data-profiling.git",
    "vcs": "git",
    "branch": "develop",
    "tags_at_head": ["4.19.1", "v4.18.1.pre4", "v4.19.0.rc1"],
    "tag": "v4.19.0.rc1",
    "commit": "628d40088663790f54fa3d01733e2ecca1bf9338",
    "working_tree": "dirty-untracked-generated-skill-output",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "fg-data-profiling",
      "version": "0.0.dev0",
      "version_note": "Editable inspection fallback because VERSION was absent in the checkout; use commit/tags for refresh decisions.",
      "import_names": ["data_profiling", "ydata_profiling"]
    }
  ],
  "evidence": {
    "source_roots": ["src/data_profiling", "src/ydata_profiling"],
    "package_metadata": ["pyproject.toml", "setup.py", "MANIFEST.in", "Makefile", ".github/workflows/tests.yml"],
    "docs": ["README.md", "docs/getting-started", "docs/features", "docs/advanced_settings", "docs/integrations", "docs/support-contribution"],
    "examples": ["examples"],
    "tests": ["tests/unit", "tests/issues", "tests/backends/spark_backend", "tests/notebooks"],
    "configs": ["src/data_profiling/config_default.yaml", "src/data_profiling/config_minimal.yaml"],
    "generated_skill_artifacts": ["skills/tests/fg-data-profiling/reports/integration"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the `repository.commit` above, treat the
  skill as potentially stale.
- If package metadata changes the distribution name, import names, console
  entry points, optional extras, or Python version range, refresh the root skill
  and the relevant sub-skills.
- If `ProfileReport`, `compare`, `Settings`, config YAML fields, CLI flags, or
  Spark backend behavior changes, refresh the owning sub-skill before using old
  instructions for a user task.
- If a checkout is dirty for source, docs, tests, examples, configs, or package
  metadata, do not assume the commit alone represents the current behavior.

## Evidence categories consulted

This skill distilled source code, package metadata, public docs, examples,
unit tests, Spark backend tests, CI workflows, and installed-package inspection.
The generated skill intentionally copies/adapts operational guidance into its
own `references/` and `scripts/` instead of requiring original repository docs,
examples, or tests at runtime.
