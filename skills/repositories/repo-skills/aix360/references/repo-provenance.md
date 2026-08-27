# Repository Provenance

Read this before deciding whether this skill is current for another AIX360
checkout. If the source commit, package version, public entry points, or major
evidence paths differ, run `refresh-repo-skill` rather than assuming the graph
still matches.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T09:55:00Z",
  "repository": {
    "name": "AIX360",
    "remote_url": "https://github.com/Trusted-AI/AIX360",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "783f8365d4f63bf8be8b53befacdab9fbbbb7335",
    "working_tree": "dirty-after-generation; source baseline was clean",
    "dirty_paths": ["skills/disco/ (generated runtime output)"]
  },
  "packages": [
    {
      "name": "aix360",
      "version": "0.3.0",
      "import_names": ["aix360"]
    }
  ],
  "evidence": {
    "source_roots": ["aix360/algorithms", "aix360/datasets", "aix360/metrics", "aix360/data"],
    "docs": ["README.md", "docs"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["setup.py", ".github/workflows/Build.yml", "Dockerfile"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `783f8365d4f63bf8be8b53befacdab9fbbbb7335`,
  treat the skill as potentially stale.
- If the source working tree is dirty in paths other than the generated
  `skills/disco/` output, inspect those changes before relying on this
  baseline.
- If `setup.py`, public algorithm modules, dataset/metric modules, or the
  documented optional extras changed, run `refresh-repo-skill`.
- If a future checkout uses different dependency pins or exports a newly added
  algorithm family, update the affected sub-skill and rerun verification.
