# Repository Provenance

## Purpose

Read this before deciding whether this skill still matches a checkout of
`ultralyticsPro`. If the commit, dirty state, or evidence paths differ from this
snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T06:03:00Z",
  "repository": {
    "name": "ultralyticsPro",
    "remote_url": "https://github.com/iscyy/ultralyticsPro.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "9097311d908fdb5326bb27cde489091942d6c018",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "ultralytics",
      "version": "8.4.118",
      "import_names": ["ultralytics"]
    }
  ],
  "evidence": {
    "source_roots": ["."],
    "docs": ["README.md", "说明.md", "YOLO11", "YOLOv8", "YOLOv12", "YOLOv13", "YOLO改进系列"],
    "examples": [],
    "tests": [],
    "configs": []
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, refresh this skill.
- If the dirty paths change materially, refresh this skill.
- If the installed `ultralytics` package version changes, refresh this skill.
- If the repository gains package metadata, source code, or new workflows that
  materially change the wrapper presets, refresh this skill.
