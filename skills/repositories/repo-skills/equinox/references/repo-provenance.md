# Repository Provenance

## Purpose

This file records the generation snapshot; reading it does not verify that a
current checkout is fresh. Check the current checkout against the explicit
conditions below before relying on version-sensitive guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-19T00:00:00Z",
  "repository": {
    "name": "equinox",
    "remote_url": "https://github.com/patrick-kidger/equinox",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "f87fc08c17ba990817150f58086c2e22076e2948",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "equinox",
      "version": "0.13.8",
      "import_names": ["equinox", "equinox.nn", "equinox.debug", "equinox.internal"]
    }
  ],
  "evidence": {
    "source_roots": ["equinox", "equinox/nn", "equinox/debug", "equinox/internal"],
    "docs": ["README.md", "docs", "mkdocs.yml"],
    "examples": ["docs/examples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "mkdocs.yml"]
  }
}
```

## Freshness Check Conditions

Treat the skill as potentially stale and refresh it if any of these conditions
is observed:

- `git rev-parse HEAD` differs from `repository.commit`.
- The current working-tree clean/dirty state differs from `repository.working_tree`,
  or the current dirty paths differ from `repository.dirty_paths`.
- Package metadata or public entry points changed, even on the same commit.
- Any recorded source, documentation, example, test, or configuration evidence
  path is missing or materially changed.
- `equinox.internal` guidance is needed after a JAX or Equinox upgrade; in that
  case, re-run its smoke and native tests before relying on that guidance.
