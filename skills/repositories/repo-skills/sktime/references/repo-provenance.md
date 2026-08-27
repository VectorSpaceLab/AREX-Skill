# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
`sktime`. If the current repo commit, dirty state, package version, or major
evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T16:20:00Z",
  "repository": {
    "name": "sktime",
    "remote_url": "https://github.com/sktime/sktime.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "4c0d3c4dde685642ac57d1ed67f2043a650849c9",
    "working_tree": "clean at initial source snapshot; generated skill files were added under skills/ afterward",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "sktime",
      "version": "1.1.0",
      "import_names": ["sktime"]
    }
  ],
  "evidence": {
    "source_roots": ["sktime"],
    "docs": ["README.md", "docs/source/installation.rst", "docs/source/examples.rst", "docs/source/api_reference", "docs/source/developer_guide"],
    "examples": ["examples", "extension_templates"],
    "tests": ["sktime/tests", "sktime/*/tests"],
    "configs": ["pyproject.toml", "setup.cfg"],
    "scripts": ["build_tools", ".github/scripts"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If package metadata, optional dependency groups, public module names, estimator
  tags, or extension template contracts changed, refresh even on the same commit.
- If a task depends on an optional deep-learning, foundation-model, dataset
  download, or accelerator workflow not covered by this skill's base CPU checks,
  verify that workflow separately or extend the skill.
