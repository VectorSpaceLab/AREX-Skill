# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, public
entry points, or major evidence paths differ from this snapshot, run
`refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T17:32:20Z",
  "repository": {
    "name": "stylegan2-pytorch",
    "remote_url": "https://github.com/lucidrains/stylegan2-pytorch.git",
    "vcs": "git",
    "branch": "master",
    "tag": "1.9.0",
    "commit": "ce7f830bc10d037cddc75d6166904baf07945cf6",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "stylegan2_pytorch",
      "version": "1.9.0",
      "import_names": ["stylegan2_pytorch"],
      "console_scripts": ["stylegan2_pytorch"]
    }
  ],
  "evidence": {
    "source_roots": ["stylegan2_pytorch"],
    "docs": ["README.md"],
    "examples": ["samples"],
    "tests": [],
    "configs": ["setup.py", "setup.cfg"],
    "ci": [".github/workflows/python-publish.yml"],
    "existing_skill_artifacts": ["skills/stylegan2-pytorch.log"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the
  snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If package metadata, dependencies, public exports, CLI parameters, checkpoint
  format, or output directory behavior changed even on the same commit, run
  `refresh-repo-skill`.
- The package asserts CUDA availability at import time in this snapshot. If a
  future version removes or changes that requirement, refresh the skill before
  reusing backend guidance.
