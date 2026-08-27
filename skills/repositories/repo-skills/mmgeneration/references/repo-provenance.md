# Repository Provenance

## Purpose

Read this before deciding whether the generated skill still matches a checkout of MMGeneration. If the commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T16:32:13Z",
  "repository": {
    "name": "mmgeneration",
    "remote_url": "https://github.com/open-mmlab/mmgeneration.git",
    "vcs": "git",
    "branch": "master",
    "tag": "v0.7.3",
    "commit": "ccd1f56c107886bb411e0fdf3a92aa6f1cf7024e",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "mmgen",
      "version": "0.7.3",
      "import_names": ["mmgen"]
    },
    {
      "name": "mmcv-full",
      "version": "1.7.2",
      "import_names": ["mmcv"]
    },
    {
      "name": "mmcls",
      "version": "0.25.0",
      "import_names": ["mmcls"]
    },
    {
      "name": "torch",
      "version": "2.0.1",
      "import_names": ["torch"]
    },
    {
      "name": "torchvision",
      "version": "0.15.2",
      "import_names": ["torchvision"]
    }
  ],
  "evidence": {
    "source_roots": ["mmgen"],
    "docs": ["README.md", "docs/en"],
    "examples": ["demo", "apps", "tools"],
    "tests": ["tests"],
    "configs": ["configs"],
    "metadata": ["setup.py", "setup.cfg", "requirements", "model-index.yml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the working tree becomes dirty or the dirty paths change, refresh the skill.
- If package metadata or public entry points change on the same commit, refresh the skill.
