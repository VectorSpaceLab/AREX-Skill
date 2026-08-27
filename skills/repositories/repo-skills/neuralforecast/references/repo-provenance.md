# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
NeuralForecast. If the current commit, dirty state, package version, or major
evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T12:22:55Z",
  "repository": {
    "name": "neuralforecast",
    "remote_url": "https://github.com/Nixtla/neuralforecast.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "ad099fce08e1f4e36cdbf89301f69bd3b820fd41",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/disco/neuralforecast/",
      "skills/tests/neuralforecast/"
    ]
  },
  "packages": [
    {
      "name": "neuralforecast",
      "version": "3.2.1",
      "import_names": ["neuralforecast"]
    }
  ],
  "evidence": {
    "source_roots": ["neuralforecast"],
    "docs": ["README.md", "docs", "nbs/docs"],
    "examples": ["scripts", "nbs/docs/tutorials", "nbs/docs/capabilities"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "uv.lock", "Makefile", "CONTRIBUTING.md"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ in a meaningful way from this
  snapshot, run `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit,
  run `refresh-repo-skill`.
