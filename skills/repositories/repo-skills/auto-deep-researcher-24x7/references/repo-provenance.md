# Repository Provenance

## Purpose

Read this before using the operating graph against a checkout of the
repository. If the commit, dirty source-skill state, public entry points, or
major evidence paths differ, treat this graph as potentially stale and run
`refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-25T21:38:11Z",
  "repository": {
    "name": "auto-deep-researcher-24x7",
    "remote_url": "https://github.com/Xiangyue-Zhang/auto-deep-researcher-24x7.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "dbf3df816c60a17a159b96c6f31191cd14bac5c3",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/auto-experiment/SKILL.md",
      "skills/auto-experiment/references/",
      "skills/conf-search/SKILL.md",
      "skills/daily-papers/SKILL.md",
      "skills/experiment-status/SKILL.md",
      "skills/gpu-monitor/SKILL.md",
      "skills/obsidian-sync/SKILL.md",
      "skills/paper-analyze/SKILL.md",
      "skills/progress-report/SKILL.md"
    ]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["core", "gpu"]
    }
  ],
  "evidence": {
    "source_roots": ["core", "gpu", "agents"],
    "docs": ["README.md", "docs/architecture.md"],
    "examples": ["examples/single_gpu", "examples/toy_experiment"],
    "tests": ["tests"],
    "configs": ["config.yaml", "requirements.txt"],
    "integrations": ["install.py", "skills/*/SKILL.md"]
  }
}
```

The checkout has no `pyproject.toml`, `setup.py`, or `setup.cfg`; this is an
application repository whose `core` and `gpu` modules are imported from the
application environment rather than a published distribution name. The
repository's documented runtime dependencies are in `requirements.txt`.

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, refresh before
  making API or configuration claims.
- If the current source-skill dirty paths differ materially from the snapshot,
  refresh; generated `skills/disco/` and `skills/tests/` output is not evidence
  for the source baseline.
- Refresh when `core/`, `gpu/`, `agents/`, `config.yaml`, `install.py`, the
  source `skills/*/SKILL.md` files, or the public tests change.
- A source-skill edit may affect route wording without changing the core loop;
  compare the changed source file to the corresponding integration reference.
