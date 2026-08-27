# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of MMDetection3D. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T06:14:00Z",
  "repository": {
    "name": "mmdetection3d",
    "remote_url": "https://github.com/open-mmlab/mmdetection3d.git",
    "vcs": "git",
    "branch": "main",
    "tag": "v1.4.0",
    "commit": "fe25f7a51d36e3702f961e198894580d83c4387b",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "mmdet3d",
      "version": "1.4.0",
      "import_names": ["mmdet3d"]
    }
  ],
  "evidence": {
    "source_roots": ["mmdet3d"],
    "docs": ["README.md", "docs/en"],
    "examples": ["demo"],
    "tests": ["tests"],
    "configs": ["configs", "mmdet3d/configs", "model-index.yml", "dataset-index.yml"],
    "tools": ["tools"],
    "projects": ["projects"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and refresh it.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, refresh it.
- If MMDetection3D package metadata, public APIs, config layout, tool arguments, or OpenMMLab dependency ranges changed, refresh it.
- If a task relies on optional project extensions or sparse backends not covered here, verify the specific project/backend before use.
