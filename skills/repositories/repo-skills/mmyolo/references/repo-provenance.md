# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of MMYOLO. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T19:10:04Z",
  "repository": {
    "name": "mmyolo",
    "remote_url": "https://github.com/open-mmlab/mmyolo.git",
    "vcs": "git",
    "branch": "main",
    "tag": "v0.6.0",
    "commit": "8c4d9dc503dc8e327bec8147e8dc97124052f693",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "mmyolo",
      "version": "0.6.0",
      "import_names": ["mmyolo"]
    }
  ],
  "evidence": {
    "source_roots": ["mmyolo"],
    "configs": ["configs", "model-index.yml"],
    "docs": ["README.md", "docs/en"],
    "examples": ["demo", "projects"],
    "tools": ["tools"],
    "tests": ["tests"],
    "package_metadata": ["setup.py", "setup.cfg", "requirements", "requirements.txt", "MANIFEST.in"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source/config/docs changes outside generated skill artifacts, run `refresh-repo-skill`.
- If package metadata, OpenMMLab version constraints, MIM command resources, or public model/config families changed, run `refresh-repo-skill`.
- If MMYOLO changes deployment APIs or optional backend support, refresh before relying on `deployment-conversion` guidance.
