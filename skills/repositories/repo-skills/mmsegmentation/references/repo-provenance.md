# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of MMSegmentation. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-23T00:00:00Z",
  "repository": {
    "name": "mmsegmentation",
    "remote_url": "https://github.com/open-mmlab/mmsegmentation",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "b040e147adfa027bbc071b624bedf0ae84dfc922",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "mmsegmentation",
      "version": "1.2.2",
      "import_names": ["mmseg"]
    }
  ],
  "evidence": {
    "source_roots": ["mmseg"],
    "configs": ["configs", "mmseg/configs"],
    "docs": ["README.md", "docs/en"],
    "examples": ["demo"],
    "scripts": ["tools"],
    "tests": ["tests"],
    "projects": ["projects/README.md", "projects/example_project", "selected projects/*/README.md"],
    "metadata": ["setup.py", "setup.cfg", "requirements", "model-index.yml", "dataset-index.yml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If public APIs, config conventions, dataset classes, tool flags, dependencies, or model/project coverage changed, run `refresh-repo-skill` even on the same commit.
- If package metadata reports a different `mmsegmentation` version, re-check install compatibility and generated API references.
- Ignore dirty paths that are only generated skill or verification artifacts when comparing the source repository itself.
