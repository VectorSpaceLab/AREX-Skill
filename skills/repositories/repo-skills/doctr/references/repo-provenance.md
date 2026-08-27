# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of docTR. If the current repo commit, package metadata, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T05:55:27Z",
  "repository": {
    "name": "doctr",
    "remote_url": "https://github.com/mindee/doctr.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "533257459802a6759c0263c3a96c61d4f588173c",
    "working_tree": "clean at source snapshot before generated skill/artifact files were written",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "python-doctr",
      "version": "1.0.2a0",
      "import_names": ["doctr"]
    }
  ],
  "entry_points": [
    {
      "name": "doctr-cli",
      "target": "doctr.cli.main:main"
    }
  ],
  "evidence": {
    "metadata": ["pyproject.toml", "setup.py", "README.md"],
    "source_roots": ["doctr"],
    "docs": ["docs/source", "README.md"],
    "source_scripts": ["scripts", "references"],
    "tests": ["tests/common", "tests/pytorch", "tests/conftest.py"],
    "optional_deployment": ["api", "demo", "Dockerfile"]
  },
  "construction_notes": {
    "generated_skill_id": "doctr",
    "runtime_scope": "self-contained generated repo skill",
    "required_backend_scope": "cpu",
    "optional_backend_notes": ["cuda and mps are documented acceleration paths, not required for this skill's verification scope"],
    "import_policy": "not imported per user request"
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, console entry points, public model factories, dataset schemas, or export APIs changed even on the same commit, run `refresh-repo-skill`.
- If using this skill for a checkout with a materially dirty source tree, compare the changed files to the evidence paths above; refresh when public behavior or docs may differ.
- The generated skill and review artifacts themselves are not source evidence for staleness.
