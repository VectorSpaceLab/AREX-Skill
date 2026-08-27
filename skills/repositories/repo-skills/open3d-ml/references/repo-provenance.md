# Repository Provenance

## Purpose

Read this before deciding whether this skill matches a checkout of Open3D-ML.
If the current commit or package baseline differs materially from this snapshot,
refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T11:23:49Z",
  "repository": {
    "name": "Open3D-ML",
    "remote_url": "https://github.com/isl-org/Open3D-ML.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "5e81f52340c2ef40da9bb05065b5549c7d8ca49f",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "ml3d",
      "version": "0.0.0",
      "import_names": ["ml3d"]
    },
    {
      "name": "open3d",
      "version": "0.19.0",
      "import_names": ["open3d", "open3d.ml"]
    },
    {
      "name": "torch",
      "version": "2.2.2+cpu",
      "import_names": ["torch"]
    }
  ],
  "evidence": {
    "source_roots": ["ml3d"],
    "docs": ["README.md", "docs"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["ml3d/configs", "requirements.txt", "requirements-torch.txt", "requirements-torch-cuda.txt", "requirements-tensorflow.txt", "requirements-openvino.txt"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` changes, refresh this skill.
- If the working tree dirty paths differ materially, refresh this skill.
- If package metadata or public entry points change, refresh this skill.
