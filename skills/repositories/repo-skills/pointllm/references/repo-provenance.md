# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a PointLLM checkout.
If the current commit, dirty state, package version, or public evidence paths
differ from this snapshot, run a refresh workflow rather than assuming the
operating guidance is current.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T20:38:29Z",
  "repository": {
    "name": "PointLLM",
    "remote_url": "https://github.com/InternRobotics/PointLLM.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "cb72f4e6ab625ddab92f84931127e12bc326b4be",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "pointllm",
      "version": "0.1.2",
      "import_names": ["pointllm"]
    }
  ],
  "evidence": {
    "source_roots": ["pointllm/"],
    "docs": ["README.md"],
    "examples": ["pointllm/eval/", "scripts/"],
    "tests": [],
    "configs": [
      "pyproject.toml",
      "pointllm/data/modelnet_config/",
      "pointllm/model/pointbert/*.yaml"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as
  potentially stale and refresh it.
- If the working tree's dirty state differs, or its relevant dirty paths change,
  refresh it. This snapshot was already dirty under `skills/`; the commit alone
  is not the entire baseline.
- If package metadata, dependency pins, public launchers, data contracts,
  checkpoints, or model-registration behavior changes, refresh even if the
  commit happens to be the same.
- Evidence paths are source provenance only. The operating routes and bundled
  helpers in this skill are self-contained and must not require the checkout to
  remain available after installation.
