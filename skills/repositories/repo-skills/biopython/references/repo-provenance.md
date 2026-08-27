# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T17:02:03Z",
  "repository": {
    "name": "biopython",
    "remote_url": "https://github.com/biopython/biopython.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "c9489604d1d9607602ca9199a3852c1219ed330f",
    "working_tree": "dirty-generated-artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "biopython",
      "version": "1.89.dev0",
      "import_names": ["Bio", "BioSQL"]
    }
  ],
  "evidence": {
    "package_metadata": ["pyproject.toml", "setup.py", "MANIFEST.in"],
    "source_roots": ["Bio/", "BioSQL/"],
    "docs": ["README.rst", "DEPRECATED.rst", "Doc/Tutorial/"],
    "examples": ["Doc/examples/"],
    "tests": ["Tests/"],
    "scripts": ["Scripts/"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source, metadata, docs, examples, tests, or scripts changes beyond generated skill artifacts, refresh before relying on package-specific guidance.
- If `Bio.__version__`, package metadata, supported Python versions, public format maps, or major optional dependency behavior changed, refresh even when the commit is otherwise familiar.
- If a task depends on a module not covered by this skill's current sub-skill routes, prefer `extend-repo-skill` rather than editing generated runtime files ad hoc.
