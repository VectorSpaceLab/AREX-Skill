# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of LTX-2. If the source commit, package metadata, or evidence paths differ materially, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T17:16:03Z",
  "repository": {
    "name": "LTX-2",
    "remote_url": "https://github.com/Lightricks/LTX-2.git",
    "vcs": "git",
    "branch": "main",
    "tag": "readme-demo-window",
    "commit": "fd4ded7f2d88d3da713abcdd4ad41ecc4a9314ca",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "ltx-core",
      "version": "1.2.0",
      "import_names": ["ltx_core"]
    },
    {
      "name": "ltx-pipelines",
      "version": "1.2.0",
      "import_names": ["ltx_pipelines"]
    },
    {
      "name": "ltx-trainer",
      "version": "1.2.0",
      "import_names": ["ltx_trainer"]
    },
    {
      "name": "ltx-kernels",
      "version": "1.2.0",
      "import_names": ["ltx_kernels"]
    }
  ],
  "evidence": {
    "source_roots": [
      "packages/ltx-core/src/ltx_core",
      "packages/ltx-pipelines/src/ltx_pipelines",
      "packages/ltx-trainer/src/ltx_trainer",
      "packages/ltx-kernels/src/ltx_kernels"
    ],
    "docs": [
      "README.md",
      "MODELS-LTX-2.3.md",
      "packages/ltx-core/README.md",
      "packages/ltx-pipelines/README.md",
      "packages/ltx-pipelines/docs",
      "packages/ltx-trainer/README.md",
      "packages/ltx-trainer/docs",
      "packages/ltx-kernels/README.md",
      "packages/ltx-kernels/docs"
    ],
    "examples": [],
    "tests": [],
    "configs": [
      "packages/ltx-trainer/configs"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, the skill may be stale.
- If the working tree dirty paths differ materially from this snapshot, refresh the skill.
- If package versions or public entry points changed, refresh the skill even on the same commit.
