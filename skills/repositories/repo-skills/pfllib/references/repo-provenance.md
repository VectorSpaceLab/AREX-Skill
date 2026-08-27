# Repository Provenance

## Purpose

Read this before deciding whether this skill matches a PFLlib checkout. If the
commit, dirty state, package surface, or key evidence paths differ materially
from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T11:52:04Z",
  "repository": {
    "name": "PFLlib",
    "remote_url": "https://github.com/TsingZ0/PFLlib.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "0169ba7e412c9856a08bb3faefab1e35f538a3c1",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "source-only",
      "version": null,
      "import_names": ["flcore", "dataset", "system"]
    }
  ],
  "evidence": {
    "source_roots": ["system/", "dataset/"],
    "docs": ["README.md", "docs/"],
    "examples": ["dataset/generate_*.py", "system/main.py"],
    "tests": [],
    "configs": ["env_cuda_latest.yaml", "prepare.sh"]
  }
}
```

## Refresh Check

- If the current `git rev-parse HEAD` differs from the recorded commit, refresh
  the skill.
- If the dirty path set changes in a way that indicates different repository
  content, refresh the skill.
- If public CLI names, dataset generator names, or supported model/algorithm
  registries change, refresh the skill.
- If the repository later gains an installable distribution, refresh the skill
  to record the package name and version.
